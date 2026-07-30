"""Expense 테이블 확인"""
import requests
from config import NOCODB_URL, NOCODB_API_TOKEN

EXPENSE_TABLE_ID = "mu382v0vk7rkih9"

def check_expense_table():
    print("=== Expense 테이블 메타데이터 ===")
    url = f"{NOCODB_URL}/api/v2/meta/tables/{EXPENSE_TABLE_ID}"
    headers = {"xc-token": NOCODB_API_TOKEN}

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        print(f"테이블명: {data.get('title')}")
        print(f"\n컬럼 목록:")
        for col in data.get('columns', []):
            print(f"  - {col.get('title')} ({col.get('uidt')})")

    print("\n=== Expense 테이블 레코드 (최대 10개) ===")
    records_url = f"{NOCODB_URL}/api/v2/tables/{EXPENSE_TABLE_ID}/records"
    resp = requests.get(records_url, headers=headers, params={"limit": 10}, timeout=30)

    if resp.status_code == 200:
        data = resp.json()
        records = data.get('list', [])
        print(f"총 레코드 수: {len(records)}")
        for i, record in enumerate(records, 1):
            print(f"\n레코드 {i}:")
            for key, value in record.items():
                if not key.startswith('nc_') and key not in ['CreatedAt', 'UpdatedAt']:
                    print(f"  {key}: {value}")

if __name__ == "__main__":
    check_expense_table()
