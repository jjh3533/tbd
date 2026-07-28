"""이미 네이버에 등록된 상품들의 배송/원산지 설정을 일괄 수정한다.

수정 항목:
    1) 택배사: ACE Express ("ACE")
    2) 직접수령: 불가능 (visitAddressId -> 0)
    3) 반품배송비: 40,000원 / 교환배송비: 80,000원
    4) 원산지: 중국 -> 미국

동작 방식은 update_price_stock.py와 동일하게 GET 전체 조회 -> 필요한 필드만
교체 -> 그 객체 그대로 PUT (커머스API가 요청 본문에 없는 필드는 지워버리므로).

사용법:
    python3 fix_delivery_settings.py --dry-run          # 무엇이 바뀔지만 출력 (API 호출 없음)
    python3 fix_delivery_settings.py --limit 1           # 실제로 1개만 수정 (먼저 이걸로 검증 권장)
    python3 fix_delivery_settings.py                     # registered_log.json의 전체 상품 반영
"""
import argparse
import json
from pathlib import Path

import requests

import naver_config as config
from auth import get_bearer_token

API_BASE = "https://api.commerce.naver.com/external/v2/products/channel-products"
LOG_PATH = Path(__file__).parent / "registered_log.json"

NEW_DELIVERY_COMPANY = "ACE"
NEW_RETURN_FEE = 40000
NEW_EXCHANGE_FEE = 80000
NEW_ORIGIN_AREA_CODE = "0204000"  # 수입산 > 북아메리카(북미) > 미국


def get_channel_product(token: str, channel_no: int) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/{channel_no}", headers=headers, timeout=30)
    if resp.status_code >= 300:
        raise RuntimeError(f"조회 실패 {resp.status_code}: {resp.text}")
    return resp.json()


def put_channel_product(token: str, channel_no: int, body: dict):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.put(f"{API_BASE}/{channel_no}", headers=headers, json=body, timeout=30)
    if resp.status_code >= 300:
        raise RuntimeError(f"수정 실패 {resp.status_code}: {resp.text}")
    return resp.json() if resp.text else {}


def apply_fixes(body: dict) -> tuple[dict, list[str]]:
    """GET으로 받아온 전체 body에서 배송/원산지 관련 필드만 교체.
    (before, after) 요약 문자열 리스트를 함께 돌려줘서 dry-run에서 보여준다."""
    origin = body.get("originProduct")
    if origin is None:
        raise RuntimeError(f"originProduct 키를 찾을 수 없음: {list(body.keys())}")

    changes = []

    # statusType은 GET 응답에선 재고에 따라 네이버가 계산해서 내려주는 표시값인데
    # ("OUTOFSTOCK" 등), 그대로 PUT에 되돌리면 "허용되지 않은 Enum 값"으로 거부된다.
    # SALE로 되돌려도 stockQuantity가 0이면 품절로 다시 표시되므로 동작은 동일함.
    if origin.get("statusType") == "OUTOFSTOCK":
        origin["statusType"] = "SALE"
        changes.append("statusType: 'OUTOFSTOCK' -> 'SALE' (품절 표시는 재고 0으로 그대로 유지됨)")

    di = origin.setdefault("deliveryInfo", {})

    old = di.get("deliveryCompany")
    if old != NEW_DELIVERY_COMPANY:
        changes.append(f"deliveryCompany: {old!r} -> {NEW_DELIVERY_COMPANY!r}")
    di["deliveryCompany"] = NEW_DELIVERY_COMPANY

    old = di.pop("visitAddressId", None)
    if old:
        changes.append(f"visitAddressId(직접수령): {old!r} -> (필드 제거, 방문수령 불가)")

    cdi = di.setdefault("claimDeliveryInfo", {})
    old = cdi.get("returnDeliveryFee")
    if old != NEW_RETURN_FEE:
        changes.append(f"returnDeliveryFee: {old!r} -> {NEW_RETURN_FEE!r}")
    cdi["returnDeliveryFee"] = NEW_RETURN_FEE

    old = cdi.get("exchangeDeliveryFee")
    if old != NEW_EXCHANGE_FEE:
        changes.append(f"exchangeDeliveryFee: {old!r} -> {NEW_EXCHANGE_FEE!r}")
    cdi["exchangeDeliveryFee"] = NEW_EXCHANGE_FEE

    oa = origin.setdefault("detailAttribute", {}).setdefault("originAreaInfo", {})
    old_code = oa.get("originAreaCode")
    if old_code != NEW_ORIGIN_AREA_CODE:
        changes.append(f"originAreaCode: {old_code!r} -> {NEW_ORIGIN_AREA_CODE!r}")
    oa["originAreaCode"] = NEW_ORIGIN_AREA_CODE

    old_content = oa.get("content") or ""
    if "중국" in old_content:
        new_content = old_content.replace("중국", "미국")
    elif old_content in ("", None):
        new_content = "미국"
    else:
        new_content = old_content  # 이미 다른 나라로 표기된 경우 등 - 손대지 않고 그대로 둠
    if new_content != old_content:
        changes.append(f"origin content: {old_content!r} -> {new_content!r}")
    oa["content"] = new_content

    return body, changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    with open(LOG_PATH) as f:
        log = json.load(f)

    token = None
    if not args.dry_run:
        token = get_bearer_token(config.CLIENT_ID, config.CLIENT_SECRET)

    processed = 0
    for product_name, entry in log.items():
        if args.limit is not None and processed >= args.limit:
            break

        channel_no = entry.get("smartstoreChannelProductNo")
        if not channel_no:
            print(f"[건너뜀] '{product_name}' - smartstoreChannelProductNo 없음")
            continue

        print(f"\n=== {product_name} (channelProductNo={channel_no}) ===")

        try:
            if args.dry_run:
                current = entry  # registered_log.json에 저장된 마지막 상태로 미리보기
            else:
                current = get_channel_product(token, int(channel_no))

            updated_body, changes = apply_fixes(current)
            if not changes:
                print("  변경 없음 (이미 최신 설정)")
            else:
                for c in changes:
                    print(f"  {c}")

            if not args.dry_run:
                put_channel_product(token, int(channel_no), updated_body)
                print("  [완료]")
        except Exception as e:  # noqa: BLE001
            print(f"  [오류] {e}")

        processed += 1

    print(f"\n총 {processed}개 처리")


if __name__ == "__main__":
    main()
