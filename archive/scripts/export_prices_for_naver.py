"""
NocoDB의 "sale_price"(및 재고 상태)을 조회해서, 스마트스토어 상품등록 자동화 스크립트가
쓸 수 있는 CSV로 저장합니다.

주의: 이 테이블의 "SKU" 필드에는 실제로는 짧은 코드가 아니라 상품명 전체
(예: "UniFi U7 Pro Max")가 들어있습니다. 그래서 상품명 문자열로 매칭합니다.

실행 위치: /Users/cheil/tbd (이 폴더의 .env, nocodb_client.py, config.py 를 그대로 사용)

사용법:
    python export_prices_for_naver.py

결과: /Users/cheil/naver/nocodb_prices.csv 에 상품명, sale_price, purchase_cost, profit, In_Stock 저장
"""
import csv
from pathlib import Path

import config
from nocodb_client import NocoDBTable

# (naver 템플릿에서 쓸 키, NocoDB "SKU"(=상품명) 필드에서 찾을 이름)
TARGET_PRODUCTS = [
    ("UniFi Cloud Gateway Ultra UCG-Ultra", "Cloud Gateway Ultra"),
    ("UniFi U7 Pro XG", "U7 Pro XG"),
    ("UniFi Dream Router 7", "Dream Router 7"),
    ("UniFi Dream Router 5G Max", "Dream Router 5G Max"),
    ("UniFi U7 Lite", "U7 Lite"),
    ("UniFi U7 Long Range", "U7 Long-Range"),
    ("UniFi U7 Pro", "U7 Pro"),
    ("UniFi U7 Pro Max", "U7 Pro Max"),
    ("UniFi UCG Fiber", "Cloud Gateway Fiber"),
    ("UniFi UCG Max", "Cloud Gateway Max"),
    ("UniFi UX7", "Express 7"),
    ("UniFi Switch Flex 2.5G", "Flex 2.5G"),
    ("UniFi Switch Flex 2.5G PoE", "Flex 2.5G PoE"),
    ("UniFi Switch Flex mini", "Flex Mini"),
    ("UniFi Switch Flex mini 2.5G", "Flex Mini 2.5G"),
    ("UniFi Switch Lite 16 PoE", "Lite 16 PoE"),
    ("UniFi Switch Lite 8 PoE", "Lite 8 PoE"),
    ("UniFi Switch Ultra 210W", "Ultra 210W"),
    ("UniFi Switch Ultra 60W", "Ultra 60W"),
]

OUTPUT_PATH = Path("/Users/cheil/naver/nocodb_prices.csv")


def normalize(s: str) -> str:
    return (s or "").lower().replace("-", " ").replace("_", " ").strip()


def main():
    table = NocoDBTable(config.NOCODB_URL, config.NOCODB_API_TOKEN, config.NOCODB_TABLE_ID)
    records = table.all()
    print(f"NocoDB에서 총 {len(records)}개 레코드 조회됨")

    # 정규화된 이름 -> fields
    norm_index = {}
    for r in records:
        f = r["fields"]
        name = f.get("SKU") or ""
        norm_index[normalize(name)] = f

    def find(search_key: str):
        nk = normalize(search_key)
        # 1) 정확히 끝나는 형태로 포함 (예: "U7 Pro" 검색 시 "U7 Pro Max"에 오매칭 안 되도록 exact 우선)
        for full_norm, f in norm_index.items():
            if full_norm == nk or full_norm.endswith(" " + nk) or full_norm == "unifi " + nk:
                return f
        # 2) 부분 포함 매칭 (fallback)
        candidates = [f for full_norm, f in norm_index.items() if nk in full_norm]
        if len(candidates) == 1:
            return candidates[0]
        return None

    rows = []
    missing = []
    for excel_name, search_key in TARGET_PRODUCTS:
        fields = find(search_key)
        if not fields:
            missing.append((excel_name, search_key))
            continue
        rows.append({
            "영문상품명": excel_name,
            "NocoDB_SKU명": fields.get("SKU"),
            "sale_price": fields.get("sale_price", 0),
            "purchase_cost": fields.get("purchase_cost", 0),
            "profit": fields.get("profit", 0),
            "In_Stock": fields.get("In_Stock", False),
            "Naver_Product_No": fields.get("Naver_Product_No", ""),
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "영문상품명", "NocoDB_SKU명", "sale_price", "purchase_cost", "profit", "In_Stock", "Naver_Product_No",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)}개 저장 완료 -> {OUTPUT_PATH}")
    if missing:
        print(f"매칭 실패 ({len(missing)}개):")
        for excel_name, search_key in missing:
            print(f"  - {excel_name}  (검색어: '{search_key}')")


if __name__ == "__main__":
    main()
