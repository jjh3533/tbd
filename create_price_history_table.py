#!/usr/bin/env python3
"""NocoDB Base(pqlruah70l8clo1)에 Price_History 테이블을 생성합니다 (1회성 스크립트).

가격/재고 변동 이력을 EAV 스타일(한 행 = 한 번의 실제 변화)로 저장하기 위한
테이블. 재실행해도 안전합니다 (이미 존재하면 건너뜁니다).

사용법:
    python3 create_price_history_table.py
"""
import sys

import requests

import config

NOCODB_URL = config.NOCODB_URL.rstrip("/")
NOCODB_TOKEN = config.NOCODB_API_TOKEN
BASE_ID = "pqlruah70l8clo1"

HEADERS = {"xc-token": NOCODB_TOKEN, "Content-Type": "application/json"}


def request(method, path, body=None):
    url = f"{NOCODB_URL}{path}"
    resp = requests.request(method, url, json=body, headers=HEADERS, timeout=20)
    if not resp.ok:
        print(f"HTTP {resp.status_code} 에러 ({method} {path}):")
        print(resp.text)
        sys.exit(1)
    return resp.json() if resp.text else {}


def find_existing_table():
    tables = request("GET", f"/api/v2/meta/bases/{BASE_ID}/tables")["list"]
    return next((t for t in tables if t["title"] == "Price_History"), None)


def main():
    existing = find_existing_table()
    if existing:
        print(f"이미 존재함: Price_History (table_id: {existing['id']})")
        print("\n.env / .env.example에 다음을 추가하세요:")
        print(f"NOCODB_HISTORY_TABLE_ID={existing['id']}")
        return

    body = {
        "table_name": "Price_History",
        "title": "Price_History",
        "columns": [
            {"title": "SKU", "uidt": "SingleLineText"},
            {"title": "Naver_Product_No", "uidt": "SingleLineText"},
            {"title": "Field_Name", "uidt": "SingleLineText"},
            {"title": "Old_Value", "uidt": "SingleLineText"},
            {"title": "New_Value", "uidt": "SingleLineText"},
            {"title": "Changed_At", "uidt": "DateTime"},
        ],
    }
    result = request("POST", f"/api/v2/meta/bases/{BASE_ID}/tables", body)
    table_id = result["id"]
    print(f"생성 완료: Price_History (table_id: {table_id})")
    print("\n.env / .env.example에 다음을 추가하세요:")
    print(f"NOCODB_HISTORY_TABLE_ID={table_id}")


if __name__ == "__main__":
    main()
