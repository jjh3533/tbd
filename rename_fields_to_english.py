#!/usr/bin/env python3
"""NocoDB 필드명을 한글에서 영문으로 변경합니다.

변경 대상:
  - 판매금액 → sale_price
  - 구매원가 → purchase_cost
  - 수익 → profit

사용법:
    python3 rename_fields_to_english.py
"""
import json
import sys
import urllib.request
import urllib.error

import config

NOCODB_URL = config.NOCODB_URL.rstrip("/")
NOCODB_TOKEN = config.NOCODB_API_TOKEN
TABLE_ID = config.NOCODB_TABLE_ID

HEADERS = {"xc-token": NOCODB_TOKEN, "Content-Type": "application/json"}


def request(method, path, body=None):
    url = f"{NOCODB_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} 에러 ({method} {path}):")
        print(e.read().decode("utf-8"))
        sys.exit(1)


def get_columns():
    detail = request("GET", f"/api/v2/meta/tables/{TABLE_ID}")
    return detail["columns"]


def find_column(columns, title):
    return next((c for c in columns if c["title"] == title), None)


def rename_column(col_id, new_title):
    request("PATCH", f"/api/v2/meta/columns/{col_id}", {"title": new_title})
    print(f"  ✓ '{new_title}' 로 변경 완료")


def main():
    columns = get_columns()

    # 변경할 필드명 매핑
    rename_map = {
        "판매금액": "sale_price",
        "구매원가": "purchase_cost",
        "수익": "profit",
    }

    print("NocoDB 필드명을 영문으로 변경합니다.\n")

    for old_name, new_name in rename_map.items():
        print(f"'{old_name}' → '{new_name}'")

        # 이미 영문 필드가 있는지 확인
        existing = find_column(columns, new_name)
        if existing:
            print(f"  ⚠️  '{new_name}' 이미 존재함, 건너뜀")
            continue

        # 한글 필드 찾기
        old_col = find_column(columns, old_name)
        if not old_col:
            print(f"  ⚠️  '{old_name}' 필드를 찾을 수 없음, 건너뜀")
            continue

        # 이름 변경
        rename_column(old_col["id"], new_name)

    print("\n완료! 변경된 필드명:")
    columns = get_columns()
    for new_name in rename_map.values():
        col = find_column(columns, new_name)
        if col:
            print(f"  ✓ {new_name}")
        else:
            print(f"  ✗ {new_name} (변경 실패)")


if __name__ == "__main__":
    main()
