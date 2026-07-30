"""Door Access 제품의 NocoDB Product_Page 필드 업데이트

31개 Door Access 제품의 Product_Page 필드를:
- Batch 1, 2 (10개): "Detail"
- Batch 3 Simple (21개): "Simple"
"""
from nocodb_client import NocoDBTable
from config import NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID

table = NocoDBTable(NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID)

# Door Access 제품 매핑
DOOR_ACCESS_PRODUCTS = {
    # Batch 1: 핵심 제품 (Detail)
    "UniFi Reader Pro": "Detail",
    "UniFi Reader Flex": "Detail",
    "UniFi Access Ultra": "Detail",
    "UniFi Door Hub": "Detail",
    "UniFi Door Hub Mini": "Detail",

    # Batch 2: 엔터프라이즈/인터콤 (Detail)
    "UniFi Enterprise Access Hub": "Detail",
    "UniFi Intercom Viewer": "Detail",
    "UniFi G6 Entry": "Detail",
    "UniFi Magnetic Lock": "Detail",
    "UniFi Access Button": "Detail",

    # Batch 3: Simple 액세서리
    "UniFi Reader Junction Box": "Simple",
    "UniFi Reader Pro Junction Box": "Simple",
    "UniFi Reader Pro Angle Mount": "Simple",
    "UniFi Intercom Viewer Table Stand": "Simple",
    "UniFi Intercom Flush Mount": "Simple",
    "UniFi Intercom Surface Angle Mount": "Simple",
    "UniFi Intercom Wedge Mount": "Simple",
    "UniFi Intercom Sunshield": "Simple",
    "UniFi Gate Hub": "Simple",
    "UniFi Junction Utility": "Simple",
    "UniFi Door Lock Relay Cable": "Simple",
    "UniFi Door Closer": "Simple",
    "UniFi PoE Over 2-Wire Retrofit Extender": "Simple",
    "UniFi Retrofit Hub": "Simple",
    "UniFi Retrofit PSU 12V": "Simple",
    "UniFi Panic Bar": "Simple",
    "UniFi Access Rescue KeySwitch": "Simple",
    "UniFi Access Card (10-Pack)": "Simple",
    "UniFi Pocket Keyfob, 10-Pack": "Simple",
    "UniFi Gate Starter Kit": "Simple",
    "UniFi G3 Elevator Starter Kit": "Simple",
}


def update_product_pages():
    """NocoDB에서 Door Access 제품을 찾아 Product_Page 필드를 업데이트합니다."""
    records = table.all()

    updated = 0
    not_found = 0

    print("Door Access 제품 Product_Page 필드 업데이트 시작...\n")

    for product_name, page_type in DOOR_ACCESS_PRODUCTS.items():
        # SKU 필드로 제품 찾기
        matching_records = [r for r in records if r["fields"].get("SKU") == product_name]

        if not matching_records:
            print(f"⚠️  제품 없음: {product_name}")
            not_found += 1
            continue

        record = matching_records[0]
        record_id = record["id"]
        current_value = record["fields"].get("Product_Page")

        if current_value == page_type:
            print(f"✓ 이미 설정됨: {product_name} → {page_type}")
        else:
            table.update(record_id, {"Product_Page": page_type})
            print(f"✓ 업데이트: {product_name} → {page_type} (이전: {current_value})")
            updated += 1

    print(f"\n{'='*60}")
    print(f"✅ 업데이트 완료: {updated}개 제품")
    print(f"⚠️  제품 없음: {not_found}개")
    print(f"{'='*60}")


if __name__ == "__main__":
    update_product_pages()
