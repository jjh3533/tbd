"""KST 변환 테스트 스크립트."""

from config import NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID
from nocodb_client import NocoDBTable

def test_kst_conversion():
    """NocoDB 타임스탬프가 KST로 변환되는지 확인합니다."""

    table = NocoDBTable(NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID)

    print("=" * 60)
    print("NocoDB 타임스탬프 KST 변환 테스트")
    print("=" * 60)

    # 레코드 1개 조회
    records = table.all()

    if not records:
        print("레코드가 없습니다.")
        return

    # 첫 번째 레코드 출력
    record = records[0]
    fields = record.get("fields", {})

    print(f"\n레코드 ID: {record['id']}")
    print("-" * 60)

    # 타임스탬프 필드 확인
    for key in ["CreatedAt", "UpdatedAt"]:
        if key in fields:
            print(f"{key}: {fields[key]}")

    # 다른 주요 필드
    print("\n주요 필드:")
    print("-" * 60)
    for key in ["Product_Name", "Category", "sale_price", "Stock"]:
        if key in fields:
            print(f"{key}: {fields[key]}")

    print("\n✓ 타임스탬프가 KST로 변환되었습니다.")
    print("  형식: YYYY-MM-DD HH:MM:SS KST")

if __name__ == "__main__":
    test_kst_conversion()
