"""
이미 네이버에 등록된 상품의 '판매가'와 '재고'만 NocoDB 값 기준으로 갱신한다.
이미지/상세페이지/카테고리 등 나머지 정보는 건드리지 않는다.

동작 방식 (네이버 공식 가이드 기준):
    커머스API는 '상품 수정' 시 요청 본문에 포함하지 않은 필드를 제거해버리므로,
    무작정 새 payload를 만들어 PUT하면 기존 정보가 날아갈 수 있다.
    그래서 이 스크립트는 항상
        1) GET으로 해당 상품의 현재 전체 정보를 조회
        2) 그 안의 salePrice / stockQuantity(옵션 있으면 옵션별 stockQuantity)만 교체
        3) 그 전체 객체를 그대로 PUT으로 되돌려보냄
    순서로 동작한다.

사용법:
    python3 update_price_stock.py --dry-run          # 무엇이 바뀔지만 출력 (API 호출 없음)
    python3 update_price_stock.py --limit 1           # 실제로 1개만 수정 (먼저 이걸로 검증 권장)
    python3 update_price_stock.py                     # 전체 반영

주의:
    GET/PUT 엔드포인트(/external/v2/products/channel-products/{channelProductNo})는
    커머스API 공식 GitHub 기술지원 저장소의 문의글을 근거로 추정한 경로다.
    실제 호출 시 404/405가 뜨면 에러 메시지를 공유해달라 - 경로를 바로 수정하겠다.

NocoDB 필드:
    - sale_price: 네이버 판매가
    - In_Stock: 재고 여부 (True/False)
"""
import argparse
import json

import requests

import config  # tbd 기존 config.py (NOCODB_URL / NOCODB_API_TOKEN / NOCODB_TABLE_ID)
import naver_config  # 네이버 커머스API 인증 정보 (CLIENT_ID / CLIENT_SECRET)
from auth import get_bearer_token
from sync_naver_ids_to_nocodb import TARGET_PRODUCTS, build_finder
from nocodb_client import NocoDBTable

API_BASE = "https://api.commerce.naver.com/external/v2/products/channel-products"

DEFAULT_STOCK_IN = 5
DEFAULT_STOCK_OUT = 0


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


def apply_price_stock(body: dict, new_price: int, new_stock: int) -> dict:
    """GET으로 받아온 전체 body에서 salePrice/stockQuantity만 바꿔치기."""
    origin = body.get("originProduct")
    if origin is None:
        raise RuntimeError(f"originProduct 키를 찾을 수 없음. 응답 구조 확인 필요: {list(body.keys())}")

    # statusType은 GET 응답에서 재고에 따라 네이버가 계산해서 내려주는 표시값이라
    # ("OUTOFSTOCK" 등) 그대로 PUT에 되돌리면 "허용되지 않은 Enum 값"으로 거부된다.
    # SALE로 되돌려도 stockQuantity가 0이면 품절로 다시 표시되므로 동작은 동일함.
    if origin.get("statusType") == "OUTOFSTOCK":
        origin["statusType"] = "SALE"

    origin["salePrice"] = new_price

    option_info = (origin.get("detailAttribute") or {}).get("optionInfo")
    combinations = (option_info or {}).get("optionCombinations")
    if combinations:
        # 옵션형 상품(U7 Pro XG 등)은 상위 stockQuantity가 아니라 옵션별 재고 합산으로 관리됨.
        for combo in combinations:
            combo["stockQuantity"] = new_stock
    else:
        origin["stockQuantity"] = new_stock

    return body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    table = NocoDBTable(config.NOCODB_URL, config.NOCODB_API_TOKEN, config.NOCODB_TABLE_ID)
    records = table.all()
    find = build_finder(records)

    token = None
    if not args.dry_run:
        token = get_bearer_token(naver_config.CLIENT_ID, naver_config.CLIENT_SECRET)

    processed = 0
    for product_name, search_key in TARGET_PRODUCTS.items():
        if args.limit is not None and processed >= args.limit:
            break

        rec = find(search_key)
        if not rec:
            print(f"[건너뜀] '{product_name}' - NocoDB에서 '{search_key}' 매칭 실패")
            continue

        fields = rec["fields"]
        channel_no = fields.get("Naver_Product_No")
        if not channel_no:
            print(f"[건너뜀] '{product_name}' - Naver_Product_No 없음 (아직 미등록)")
            continue

        new_price = fields.get("sale_price")
        if not new_price:
            print(f"[건너뜀] '{product_name}' - NocoDB 'sale_price' 값 없음")
            continue
        new_price = int(new_price)

        in_stock = fields.get("In_Stock")
        new_stock = DEFAULT_STOCK_IN if in_stock else DEFAULT_STOCK_OUT

        print(f"\n=== {product_name} (channelProductNo={channel_no}) ===")
        print(f"  판매가 -> {new_price:,}원 / 재고 -> {new_stock}")

        if args.dry_run:
            processed += 1
            continue

        try:
            current = get_channel_product(token, int(channel_no))
            updated_body = apply_price_stock(current, new_price, new_stock)
            put_channel_product(token, int(channel_no), updated_body)
            print("  [완료]")
        except Exception as e:  # noqa: BLE001
            print(f"  [오류] {e}")

        processed += 1

    print(f"\n총 {processed}개 처리")


if __name__ == "__main__":
    main()
