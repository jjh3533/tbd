#!/usr/bin/env python3
"""NocoDB Base(pqlruah70l8clo1)에 Order_Fulfillment 테이블을 생성합니다 (1회성 스크립트).

스마트스토어 주문(자동 수집) + 현지 발주/배송 정보(수동 입력) + 배송대행지
신청 + 국제배송/네이버 발송 처리까지, 주문 한 건의 전체 이행 상태를 한
로우에 저장하기 위한 테이블. create_price_history_table.py와 동일한
구조/컨벤션(멱등 생성, 영문 snake_case 필드명)을 따른다.

사용법:
    python3 create_order_fulfillment_table.py
"""
import sys

import requests

import config

NOCODB_URL = config.NOCODB_URL.rstrip("/")
NOCODB_TOKEN = config.NOCODB_API_TOKEN
BASE_ID = "pqlruah70l8clo1"

HEADERS = {"xc-token": NOCODB_TOKEN, "Content-Type": "application/json"}

TABLE_NAME = "Order_Fulfillment"


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
    return next((t for t in tables if t["title"] == TABLE_NAME), None)


def main():
    existing = find_existing_table()
    if existing:
        print(f"이미 존재함: {TABLE_NAME} (table_id: {existing['id']})")
        print("\n.env / .env.example에 다음을 추가하세요:")
        print(f"NOCODB_ORDER_TABLE_ID={existing['id']}")
        return

    body = {
        "table_name": TABLE_NAME,
        "title": TABLE_NAME,
        "columns": [
            # 주문 (스마트스토어 API 자동 수집)
            {"title": "naver_product_order_id", "uidt": "SingleLineText"},
            {"title": "sku", "uidt": "SingleLineText"},
            {"title": "naver_order_date", "uidt": "DateTime"},
            {"title": "naver_product_name", "uidt": "SingleLineText"},
            {"title": "quantity", "uidt": "Number"},
            {"title": "orderer_name", "uidt": "SingleLineText"},
            {"title": "recipient_name_kr", "uidt": "SingleLineText"},
            {"title": "recipient_phone", "uidt": "SingleLineText"},
            {"title": "recipient_postal_code", "uidt": "SingleLineText"},
            {"title": "recipient_address", "uidt": "SingleLineText"},
            {"title": "personal_customs_code", "uidt": "SingleLineText"},
            # 발주 (수동 입력)
            {"title": "purchase_site", "uidt": "SingleLineText"},
            {"title": "local_order_number", "uidt": "SingleLineText"},
            {"title": "local_order_date", "uidt": "Date"},
            {"title": "local_unit_price_usd", "uidt": "Number"},
            {"title": "local_tracking_number", "uidt": "SingleLineText"},
            {"title": "purchase_status", "uidt": "SingleLineText"},
            # 배송대행지 신청 (에코트랜스 xlsx)
            {"title": "iecot_item_code", "uidt": "SingleLineText"},
            {"title": "repackaging_option", "uidt": "Number"},
            {"title": "business_customs", "uidt": "Checkbox"},
            {"title": "us_side_notes", "uidt": "LongText"},
            {"title": "domestic_courier_notes", "uidt": "LongText"},
            {"title": "iecot_group_key", "uidt": "SingleLineText"},
            {"title": "iecot_applied_at", "uidt": "DateTime"},
            # 국제배송/국내 발송 처리
            {"title": "intl_tracking_number", "uidt": "SingleLineText"},
            {"title": "intl_tracking_registered_at", "uidt": "DateTime"},
            {"title": "naver_dispatch_date", "uidt": "Date"},
            {"title": "naver_dispatch_delivery_company", "uidt": "SingleLineText"},
            {"title": "naver_dispatched_at", "uidt": "DateTime"},
            {"title": "naver_dispatch_result", "uidt": "LongText"},
        ],
    }
    result = request("POST", f"/api/v2/meta/bases/{BASE_ID}/tables", body)
    table_id = result["id"]
    print(f"생성 완료: {TABLE_NAME} (table_id: {table_id})")
    print("\n.env / .env.example에 다음을 추가하세요:")
    print(f"NOCODB_ORDER_TABLE_ID={table_id}")


if __name__ == "__main__":
    main()
