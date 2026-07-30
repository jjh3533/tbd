#!/usr/bin/env python3
"""NocoDB 레코드의 실제 구조를 확인합니다."""

import requests
import json
from config import NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID

def list_records(table_id, limit=3):
    """테이블의 레코드 조회"""
    url = f"{NOCODB_URL.rstrip('/')}/api/v2/tables/{table_id}/records"
    headers = {"xc-token": NOCODB_API_TOKEN}

    resp = requests.get(url, headers=headers, params={"limit": limit}, timeout=30)
    resp.raise_for_status()
    return resp.json()

def main():
    print("=" * 60)
    print("NocoDB 레코드 상세 구조 확인")
    print("=" * 60)

    try:
        records_data = list_records(NOCODB_TABLE_ID, limit=3)

        print(f"\n전체 응답 키: {list(records_data.keys())}")
        print(f"총 레코드 수: {records_data.get('pageInfo', {}).get('totalRows', '(알 수 없음)')}")

        records = records_data.get('list', [])

        print(f"\n첫 번째 레코드의 모든 필드:")
        if records:
            first_record = records[0]
            print(json.dumps(first_record, indent=2, ensure_ascii=False))

            print(f"\n\n필드명 목록 ({len(first_record)}개):")
            for key in sorted(first_record.keys()):
                value = first_record[key]
                if value is None or value == "":
                    continue
                # 값이 긴 경우 앞부분만 표시
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:50] + "..."
                print(f"  • {key}: {value_str}")

    except Exception as e:
        print(f"  ⚠️  조회 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
