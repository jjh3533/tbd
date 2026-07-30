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

색상(화이트/블랙) 옵션 상품:
    create_color_variant_rows.py로 만든 "{화이트 SKU} Black" 로우가 있고 거기에
    sale_price가 채워져 있으면(구매처 ID 입력 후 스크래핑 완료), 네이버의 "화이트"/
    "블랙" 옵션 조합에 각각 다른 price(추가금액)/stockQuantity를 반영한다. Black
    로우에 아직 sale_price가 없으면(구매처 ID 미입력) 기존처럼 모든 옵션에
    균일하게 적용하고 콘솔에 안내만 출력한다.
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


# 옵션 조합의 optionName1에 실제로 쓰이는 색상 라벨 (product_builder.py의
# 옵션값(콤마구분) 컬럼 관례와 동일하게 한글 라벨을 그대로 키로 사용).
WHITE_LABEL = "화이트"
BLACK_LABEL = "블랙"


def build_new_color_option_info(white_addon: int, white_stock: int, black_addon: int, black_stock: int) -> dict:
    """옵션 구조가 아예 없는 단일가 상품에 화이트/블랙 색상 옵션을 처음 추가할
    때 쓰는 전체 optionInfo 블록. 이미 수동으로 옵션이 설정돼 있던 U7 Pro XG의
    라이브 구조를 그대로 참고해 필드를 구성했다(누락되면 네이버가 거부하는
    필드가 있을 수 있어, 실제로 동작이 확인된 형태를 그대로 씀)."""
    return {
        "simpleOptionSortType": "CREATE",
        "optionSimple": [],
        "optionCustom": [],
        "optionCombinationSortType": "CREATE",
        "optionCombinationGroupNames": {"optionGroupName1": "색상"},
        "optionCombinations": [
            {"optionName1": WHITE_LABEL, "stockQuantity": white_stock, "price": white_addon, "usable": True},
            {"optionName1": BLACK_LABEL, "stockQuantity": black_stock, "price": black_addon, "usable": True},
        ],
        "standardOptionGroups": [],
        "optionStandards": [],
        "useStockManagement": True,
        "optionDeliveryAttributes": [],
    }


def apply_price_stock(body: dict, new_price: int, new_stock: int, option_overrides: dict | None = None) -> dict:
    """GET으로 받아온 전체 body에서 salePrice/stockQuantity만 바꿔치기.

    option_overrides: {"화이트": (price_addon, stock), "블랙": (price_addon, stock)}
    형태로 넘기면:
    - 이미 옵션 조합(화이트/블랙)이 있는 상품은 그 옵션들의 price(추가금액)/
      stockQuantity를 각각 다르게 갱신한다.
    - 옵션 자체가 아직 없는 단일가 상품이면, build_new_color_option_info()로
      화이트/블랙 옵션 구조를 새로 추가한다(고객 페이지에 "색상" 선택지가
      새로 생김).
    option_overrides를 넘기지 않으면 기존처럼 모든 옵션(또는 단일 상품)에
    new_price/new_stock을 균일하게 적용한다."""
    origin = body.get("originProduct")
    if origin is None:
        raise RuntimeError(f"originProduct 키를 찾을 수 없음. 응답 구조 확인 필요: {list(body.keys())}")

    # statusType은 GET 응답에서 재고에 따라 네이버가 계산해서 내려주는 표시값이라
    # ("OUTOFSTOCK" 등) 그대로 PUT에 되돌리면 "허용되지 않은 Enum 값"으로 거부된다.
    # SALE로 되돌려도 stockQuantity가 0이면 품절로 다시 표시되므로 동작은 동일함.
    if origin.get("statusType") == "OUTOFSTOCK":
        origin["statusType"] = "SALE"

    origin["salePrice"] = new_price

    detail_attr = origin.setdefault("detailAttribute", {})
    option_info = detail_attr.get("optionInfo")
    combinations = (option_info or {}).get("optionCombinations")

    if combinations:
        # 옵션형 상품(U7 Pro XG 등)은 상위 stockQuantity가 아니라 옵션별 재고 합산으로 관리됨.
        for combo in combinations:
            label = combo.get("optionName1")
            if option_overrides and label in option_overrides:
                price_addon, stock = option_overrides[label]
                combo["price"] = price_addon
                combo["stockQuantity"] = stock
            else:
                combo["stockQuantity"] = new_stock
    elif option_overrides:
        white_addon, white_stock = option_overrides.get(WHITE_LABEL, (0, new_stock))
        black_addon, black_stock = option_overrides.get(BLACK_LABEL, (0, new_stock))

        # 네이버는 옵션을 신규 생성할 때 "옵션가 0원 + 재고 1개 이상 + 사용함"인
        # 옵션이 최소 1개 있어야 한다(NoZeroStock 검증). 화이트를 0원 기준으로
        # 두는 게 원칙이지만, 화이트 재고가 0이면 그 조건을 못 만족하므로
        # 재고가 있는 색상을 0원 기준으로 삼고 나머지 색상의 추가금액을 그
        # 기준 대비로 재계산한다(최종 판매가=salePrice+추가금액은 어느 쪽을
        # 기준 삼든 동일하게 나옴).
        if white_stock <= 0 and black_stock > 0:
            new_price = new_price + black_addon
            white_addon, black_addon = white_addon - black_addon, 0

        if white_stock <= 0 and black_stock <= 0:
            # 화이트/블랙 둘 다 품절이면 옵션 신규 생성 자체가 거부되므로,
            # 재고가 생길 때까지는 기존처럼 단일가/단일재고로 반영하고
            # 다음 Sync 이후 재시도한다(자동으로 다시 시도됨, 별도 조치 불필요).
            origin["stockQuantity"] = new_stock
        else:
            origin["salePrice"] = new_price
            detail_attr["optionInfo"] = build_new_color_option_info(white_addon, white_stock, black_addon, black_stock)
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
    records_by_sku = {r["fields"].get("SKU", "").strip(): r for r in records}

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
        white_sku = fields.get("SKU", "").strip()
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

        # 화이트/블랙 색상 옵션 짝: create_color_variant_rows.py가 만든
        # "{화이트 SKU} Black" 로우가 있고 거기에 sale_price가 채워져 있으면
        # (=구매처 ID가 입력되어 스크래핑된 상태), 옵션별로 다른 가격/재고를 반영한다.
        option_overrides = None
        black_rec = records_by_sku.get(f"{white_sku} Black")
        if black_rec:
            black_fields = black_rec["fields"]
            black_price = black_fields.get("sale_price")
            if black_price:
                black_stock = DEFAULT_STOCK_IN if black_fields.get("In_Stock") else DEFAULT_STOCK_OUT
                option_overrides = {
                    WHITE_LABEL: (0, new_stock),
                    BLACK_LABEL: (int(black_price) - new_price, black_stock),
                }
            else:
                print(f"  [참고] '{white_sku} Black' 로우는 있지만 sale_price가 없음"
                      " (구매처 ID 미입력) - 옵션 균일 적용으로 진행")

        print(f"\n=== {product_name} (channelProductNo={channel_no}) ===")
        if option_overrides:
            print(f"  화이트 판매가 -> {new_price:,}원 / 재고 -> {new_stock}")
            black_addon, black_stock = option_overrides[BLACK_LABEL]
            print(f"  블랙 추가금액 -> {black_addon:+,}원 / 재고 -> {black_stock}")
        else:
            print(f"  판매가 -> {new_price:,}원 / 재고 -> {new_stock}")

        if args.dry_run:
            processed += 1
            continue

        try:
            current = get_channel_product(token, int(channel_no))
            updated_body = apply_price_stock(current, new_price, new_stock, option_overrides)
            put_channel_product(token, int(channel_no), updated_body)
            print("  [완료]")
        except Exception as e:  # noqa: BLE001
            print(f"  [오류] {e}")

        processed += 1

    print(f"\n총 {processed}개 처리")


if __name__ == "__main__":
    main()
