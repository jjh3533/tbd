"""NocoDB의 '최종가격' 필드명을 '구매원가'로 변경합니다."""
import requests
import sys
sys.path.insert(0, '.')
from config import NOCODB_URL, NOCODB_TABLE_ID, NOCODB_API_TOKEN

def get_columns():
    """테이블의 모든 컬럼 정보를 가져옵니다."""
    url = f"{NOCODB_URL}/api/v2/meta/tables/{NOCODB_TABLE_ID}/columns"
    headers = {"xc-token": NOCODB_API_TOKEN}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["list"]


def rename_column(column_id, new_title):
    """컬럼명을 변경합니다."""
    url = f"{NOCODB_URL}/api/v2/meta/columns/{column_id}"
    headers = {
        "xc-token": NOCODB_API_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "title": new_title,
        "column_name": new_title
    }
    resp = requests.patch(url, headers=headers, json=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    print("NocoDB '최종가격' → '구매원가' 필드명 변경\n")

    # 1. 최종가격 컬럼 찾기
    columns = get_columns()
    target_col = None

    for col in columns:
        if col.get("title") == "최종가격":
            target_col = col
            break

    if not target_col:
        print("⚠️  '최종가격' 필드를 찾을 수 없습니다.")
        print("이미 '구매원가'로 변경되었거나 필드가 존재하지 않습니다.")
        return

    print(f"✓ '최종가격' 필드 발견 (ID: {target_col['id']})")
    print(f"  현재 이름: {target_col['title']}")
    print(f"  타입: {target_col['uidt']}")
    print()

    # 2. 필드명 변경
    print("필드명 변경 중...")
    try:
        result = rename_column(target_col['id'], "구매원가")
        print("✓ 필드명이 '구매원가'로 변경되었습니다.")
        print()
        print("변경 사항:")
        print(f"  이전: {target_col['title']}")
        print(f"  이후: 구매원가")
        print()
        print("NocoDB에서 새로고침하여 확인하세요.")
    except Exception as e:
        print(f"⚠️  변경 실패: {e}")
        print()
        print("수동 변경 방법:")
        print("1. NocoDB 웹 UI에서 테이블 열기")
        print("2. '최종가격' 컬럼 헤더 클릭 → Edit")
        print("3. Column Name을 '구매원가'로 변경")


if __name__ == "__main__":
    main()
