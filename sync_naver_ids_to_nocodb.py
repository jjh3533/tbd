"""
registered_log.json(네이버 상품등록 스크립트가 남긴 등록 결과)을 읽어서,
각 상품의 smartstoreChannelProductNo를 NocoDB의 Naver_Product_No 필드에 채워넣는다.

왜 smartstoreChannelProductNo인가:
    app.py의 _naver_url()이 만드는 스토어 링크
    (https://smartstore.naver.com/tbdseoul/products/{id}) 는
    "채널상품번호"를 쓴다. originProductNo는 원상품번호로, 스토어 URL에는 안 맞는다.

사용법:
    python sync_naver_ids_to_nocodb.py             # registered_log.json 전체 반영
    python sync_naver_ids_to_nocodb.py --dry-run    # 실제로 NocoDB에 쓰지 않고 무엇을 쓸지만 출력
"""
import argparse
import json
from pathlib import Path

import config
from nocodb_client import NocoDBTable

LOG_PATH = Path(__file__).parent / "registered_log.json"

# naver_상품등록_템플릿.xlsx의 영문상품명 -> NocoDB "SKU"(실제로는 상품명) 필드에서 찾을 검색어
# export_prices_for_naver.py와 동일한 매핑을 사용한다.
TARGET_PRODUCTS = {
    "UniFi Cloud Gateway Ultra UCG-Ultra": "Cloud Gateway Ultra",
    "UniFi U7 Pro XG": "U7 Pro XG",
    "UniFi Dream Router 7": "Dream Router 7",
    "UniFi Dream Router 5G Max": "Dream Router 5G Max",
    "UniFi U7 Lite": "U7 Lite",
    "UniFi U7 Long Range": "U7 Long-Range",
    "UniFi U7 Pro": "U7 Pro",
    "UniFi U7 Pro Max": "U7 Pro Max",
    "UniFi UCG Fiber": "Cloud Gateway Fiber",
    "UniFi UCG Max": "Cloud Gateway Max",
    "UniFi UX7": "Express 7",
    "UniFi Switch Flex 2.5G": "Flex 2.5G",
    "UniFi Switch Flex 2.5G PoE": "Flex 2.5G PoE",
    "UniFi Switch Flex mini": "Flex Mini",
    "UniFi Switch Flex mini 2.5G": "Flex Mini 2.5G",
    "UniFi Switch Lite 16 PoE": "Lite 16 PoE",
    "UniFi Switch Lite 8 PoE": "Lite 8 PoE",
    "UniFi Switch Ultra 210W": "Ultra 210W",
    "UniFi Switch Ultra 60W": "Ultra 60W",
}


def normalize(s: str) -> str:
    return (s or "").lower().replace("-", " ").replace("_", " ").strip()


def build_finder(records):
    norm_index = {}
    for r in records:
        name = r["fields"].get("SKU") or ""
        norm_index[normalize(name)] = r  # 레코드 전체(= id 포함) 보관

    def find(search_key: str):
        nk = normalize(search_key)
        for full_norm, rec in norm_index.items():
            if full_norm == nk or full_norm.endswith(" " + nk) or full_norm == "unifi " + nk:
                return rec
        candidates = [rec for full_norm, rec in norm_index.items() if nk in full_norm]
        if len(candidates) == 1:
            return candidates[0]
        return None

    return find


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not LOG_PATH.exists():
        print(f"{LOG_PATH} 가 없습니다. main.py로 먼저 상품을 등록하세요.")
        return

    with open(LOG_PATH, encoding="utf-8") as f:
        log = json.load(f)

    if not log:
        print("registered_log.json 이 비어있습니다. 등록된 상품이 없습니다.")
        return

    table = NocoDBTable(config.NOCODB_URL, config.NOCODB_API_TOKEN, config.NOCODB_TABLE_ID)
    records = table.all()
    find = build_finder(records)

    updated, skipped = 0, 0
    for product_name, result in log.items():
        channel_no = result.get("smartstoreChannelProductNo")
        if not channel_no:
            print(f"[건너뜀] '{product_name}' - smartstoreChannelProductNo 없음")
            skipped += 1
            continue

        search_key = TARGET_PRODUCTS.get(product_name)
        if not search_key:
            print(f"[건너뜀] '{product_name}' - TARGET_PRODUCTS에 매핑이 없음 (스크립트에 추가 필요)")
            skipped += 1
            continue

        rec = find(search_key)
        if not rec:
            print(f"[건너뜀] '{product_name}' - NocoDB에서 '{search_key}' 매칭 실패")
            skipped += 1
            continue

        nocodb_name = rec["fields"].get("SKU")
        if args.dry_run:
            print(f"[dry-run] '{nocodb_name}' (id={rec['id']})  Naver_Product_No <- {channel_no}")
        else:
            table.update(rec["id"], {"Naver_Product_No": str(channel_no)})
            print(f"[완료] '{nocodb_name}' (id={rec['id']})  Naver_Product_No = {channel_no}")
        updated += 1

    print(f"\n총 {updated}개 반영, {skipped}개 건너뜀")


if __name__ == "__main__":
    main()
