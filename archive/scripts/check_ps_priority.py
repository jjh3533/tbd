#!/usr/bin/env python3
"""Physical Security 우선순위 제품 확인"""

from config import NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID
from nocodb_client import NocoDBTable

def main():
    table = NocoDBTable(NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID)
    records = table.all()

    # Physical Security 카테고리 필터링
    ps_products = [r for r in records if r["fields"].get("Category") == "Physical Security"]

    # 재고 있는 제품
    in_stock = [r for r in ps_products if r["fields"].get("In_Stock", 0) > 0]

    print(f"=== 재고 있는 제품 ({len(in_stock)}개) ===\n")
    for r in sorted(in_stock, key=lambda x: x["fields"].get("In_Stock", 0), reverse=True):
        fields = r["fields"]
        name = fields.get("SKU", "이름없음")
        model = fields.get("Model Number", "")
        stock = fields.get("In_Stock", 0)
        msrp = fields.get("MSRP_USD", 0)
        best = fields.get("Best_USD", 0)

        print(f"- {name} ({model})")
        print(f"  재고: {stock}개 | MSRP: ${msrp} | 최저가: ${best}")
        print()

    # 재고 없지만 가격 정보 있는 제품 (인기 제품 추정)
    no_stock = [r for r in ps_products
                if r["fields"].get("In_Stock", 0) == 0
                and r["fields"].get("Best_USD", 0) > 0]

    print(f"\n=== 재고 없지만 가격 추적 중인 제품 ({len(no_stock)}개) ===")
    print("(가격대별 정렬)\n")

    for r in sorted(no_stock, key=lambda x: x["fields"].get("MSRP_USD", 0), reverse=True)[:20]:
        fields = r["fields"]
        name = fields.get("SKU", "이름없음")
        model = fields.get("Model Number", "")
        msrp = fields.get("MSRP_USD", 0)
        best = fields.get("Best_USD", 0)

        print(f"- {name} ({model})")
        print(f"  MSRP: ${msrp} | 최저가: ${best}")

if __name__ == "__main__":
    main()
