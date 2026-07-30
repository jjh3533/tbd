"""ProjectExpenses 테이블 찾기 스크립트"""
import requests
from config import NOCODB_URL, NOCODB_API_TOKEN

# LibreChat에서 생성했다는 테이블 ID
TABLE_ID = "m72i8atzqylc6yw"

def check_table_metadata():
    """테이블 메타데이터 조회"""
    print(f"=== 테이블 메타데이터 조회 (ID: {TABLE_ID}) ===")
    url = f"{NOCODB_URL}/api/v2/meta/tables/{TABLE_ID}"
    headers = {"xc-token": NOCODB_API_TOKEN}

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"테이블명: {data.get('title')}")
            print(f"테이블 타입: {data.get('type')}")
            print(f"Base ID: {data.get('base_id')}")
            print(f"컬럼 수: {len(data.get('columns', []))}")
            print("\n컬럼 목록:")
            for col in data.get('columns', []):
                print(f"  - {col.get('title')} ({col.get('uidt')})")
            return data
        else:
            print(f"오류: {resp.text}")
            return None
    except Exception as e:
        print(f"예외 발생: {e}")
        return None

def check_table_records():
    """테이블 레코드 조회"""
    print(f"\n=== 테이블 레코드 조회 (ID: {TABLE_ID}) ===")
    url = f"{NOCODB_URL}/api/v2/tables/{TABLE_ID}/records"
    headers = {"xc-token": NOCODB_API_TOKEN}

    try:
        resp = requests.get(url, headers=headers, params={"limit": 5}, timeout=30)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            records = data.get('list', [])
            print(f"레코드 수: {len(records)}")
            if records:
                print("\n첫 번째 레코드:")
                print(records[0])
            return data
        else:
            print(f"오류: {resp.text}")
            return None
    except Exception as e:
        print(f"예외 발생: {e}")
        return None

def list_all_tables():
    """모든 테이블 목록 조회 (base_id가 필요)"""
    print(f"\n=== 사용 가능한 모든 테이블 조회 시도 ===")
    # NocoDB에서 base 목록을 먼저 조회해야 함
    url = f"{NOCODB_URL}/api/v2/meta/bases"
    headers = {"xc-token": NOCODB_API_TOKEN}

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        print(f"Base 목록 Status: {resp.status_code}")
        if resp.status_code == 200:
            bases = resp.json()
            if isinstance(bases, dict):
                bases = bases.get('list', [])

            print(f"발견된 Base 수: {len(bases)}")

            for base in bases:
                base_id = base.get('id')
                base_title = base.get('title', base.get('alias', 'Untitled'))
                print(f"\n--- Base: {base_title} (ID: {base_id}) ---")

                # 각 base의 테이블 목록 조회
                tables_url = f"{NOCODB_URL}/api/v2/meta/bases/{base_id}/tables"
                tables_resp = requests.get(tables_url, headers=headers, timeout=30)

                if tables_resp.status_code == 200:
                    tables = tables_resp.json()
                    if isinstance(tables, dict):
                        tables = tables.get('list', [])

                    print(f"테이블 수: {len(tables)}")
                    for table in tables:
                        table_id = table.get('id')
                        table_title = table.get('title')
                        print(f"  - {table_title} (ID: {table_id})")

                        # ProjectExpenses 테이블 찾기
                        if 'ProjectExpenses' in table_title or table_id == TABLE_ID:
                            print(f"    ^^^ 찾았습니다! ^^^")
        else:
            print(f"오류: {resp.text}")
    except Exception as e:
        print(f"예외 발생: {e}")

if __name__ == "__main__":
    # 1. 테이블 메타데이터 직접 조회
    metadata = check_table_metadata()

    # 2. 테이블 레코드 조회
    records = check_table_records()

    # 3. 모든 테이블 목록에서 찾기
    list_all_tables()
