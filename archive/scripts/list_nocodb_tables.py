#!/usr/bin/env python3
"""NocoDB Base의 테이블 목록을 조회합니다."""

import requests
import json
from config import NOCODB_URL, NOCODB_API_TOKEN

def get_bases():
    """모든 Base 조회"""
    headers = {"xc-token": NOCODB_API_TOKEN}
    url = f"{NOCODB_URL.rstrip('/')}/api/v2/meta/bases"

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()

def get_tables(base_id):
    """특정 Base의 테이블 목록 조회"""
    headers = {"xc-token": NOCODB_API_TOKEN}
    url = f"{NOCODB_URL.rstrip('/')}/api/v1/db/meta/projects/{base_id}/tables"

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()

def main():
    print("=" * 60)
    print("NocoDB Base 및 테이블 목록")
    print("=" * 60)

    # 1. Base 목록
    bases_data = get_bases()
    bases = bases_data.get('list', [])

    print(f"\n총 {len(bases)}개의 Base 발견\n")

    for base in bases:
        base_id = base.get('id')
        base_title = base.get('title')
        print(f"Base: {base_title} (ID: {base_id})")

        # 2. 각 Base의 테이블 목록
        try:
            tables_data = get_tables(base_id)
            tables = tables_data.get('list', [])

            print(f"  총 {len(tables)}개의 테이블:")

            for table in tables:
                table_id = table.get('id')
                table_title = table.get('title')
                table_name = table.get('table_name')
                enabled = table.get('enabled', True)
                deleted = table.get('deleted', False)

                status = []
                if not enabled:
                    status.append("비활성")
                if deleted:
                    status.append("삭제됨")

                status_str = f" [{', '.join(status)}]" if status else ""

                print(f"    • {table_title} (테이블명: {table_name})")
                print(f"      ID: {table_id}{status_str}")

        except Exception as e:
            print(f"  ⚠️  테이블 조회 실패: {e}")

        print()

if __name__ == "__main__":
    main()
