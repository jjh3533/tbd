#!/usr/bin/env python3
"""Physical Security 카테고리 제품 확인"""

from config import NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID
from nocodb_client import NocoDBTable

def main():
    table = NocoDBTable(NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID)
    records = table.all()

    # Physical Security 카테고리 필터링
    ps_products = [r for r in records if r["fields"].get("Category") == "Physical Security"]

    print(f"Physical Security 제품 총 {len(ps_products)}개:\n")

    if ps_products:
        # 첫 번째 레코드의 모든 필드 출력 (필드명 확인용)
        print("=== 첫 번째 레코드의 모든 필드 ===")
        first = ps_products[0]
        for key, value in first["fields"].items():
            print(f"{key}: {value}")
        print("\n" + "="*50 + "\n")

    for r in ps_products:
        fields = r["fields"]
        name = fields.get("SKU") or "이름없음"
        model = fields.get("Model Number") or ""
        naver_no = fields.get("Naver_Product_No") or ""
        page = fields.get("Product_Page") or ""
        stock = fields.get("In_Stock") or 0

        print(f"- {name}")
        print(f"  Model: {model}")
        print(f"  네이버 상품번호: {naver_no if naver_no else '미등록'}")
        print(f"  상세페이지: {page if page else '없음'}")
        print(f"  재고: {stock}")
        print()

if __name__ == "__main__":
    main()
