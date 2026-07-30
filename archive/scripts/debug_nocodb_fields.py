"""NocoDB 테이블의 실제 필드명과 SKU 값 형태를 확인하기 위한 디버그 스크립트."""
import config
from nocodb_client import NocoDBTable


def main():
    table = NocoDBTable(config.NOCODB_URL, config.NOCODB_API_TOKEN, config.NOCODB_TABLE_ID)
    records = table.all()
    print(f"총 {len(records)}개 레코드")
    if not records:
        return

    print("\n첫 레코드의 필드 키 목록:")
    print(list(records[0]["fields"].keys()))

    print("\nSKU 값 샘플 (앞 30개):")
    for r in records[:30]:
        f = r["fields"]
        print(f"  SKU={f.get('SKU')!r}  Name={f.get('Name') or f.get('name')!r}  판매금액={f.get('판매금액')!r}")


if __name__ == "__main__":
    main()
