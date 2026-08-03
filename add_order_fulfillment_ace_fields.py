#!/usr/bin/env python3
"""Order_Fulfillment 테이블에 ACE Express 송장 자동조회 + 택배사 선택 필드를 추가합니다 (1회성 스크립트).

- intl_delivery_company: 국제배송 송장 등록 시 고른 택배사 코드(예: "ACE") - 이후
  스마트스토어 발송 처리 단계에서 재입력 없이 그대로 재사용된다.
- ace_customs_started_at / ace_domestic_started_at / ace_delivered_at: ACE
  Express 송장 조회 결과에서 확인한 통관 시작(항공기 도착)/국내배송 시작(반출)/
  배달완료 시각 - 한 번 확인되면 되돌아가지 않는 사실이라 저장해두고, 국내배송
  시작까지 확정된 주문은 다음 새로고침부터 재조회를 건너뛴다.
- ace_last_checked_at: 마지막으로 ACE 조회를 시도한 시각(디버깅용).

create_order_fulfillment_table.py와 동일한 멱등 생성 패턴.
"""
import sys

import requests

import config

NOCODB_URL = config.NOCODB_URL.rstrip("/")
NOCODB_TOKEN = config.NOCODB_API_TOKEN
TABLE_ID = config.NOCODB_ORDER_TABLE_ID

HEADERS = {"xc-token": NOCODB_TOKEN, "Content-Type": "application/json"}

NEW_COLUMNS = [
    {"title": "intl_delivery_company", "uidt": "SingleLineText"},
    {"title": "ace_customs_started_at", "uidt": "DateTime"},
    {"title": "ace_domestic_started_at", "uidt": "DateTime"},
    {"title": "ace_delivered_at", "uidt": "DateTime"},
    {"title": "ace_last_checked_at", "uidt": "DateTime"},
]


def request(method, path, body=None):
    url = f"{NOCODB_URL}{path}"
    resp = requests.request(method, url, json=body, headers=HEADERS, timeout=20)
    if not resp.ok:
        print(f"HTTP {resp.status_code} 에러 ({method} {path}):")
        print(resp.text)
        sys.exit(1)
    return resp.json() if resp.text else {}


def main():
    existing_columns = {c["title"] for c in request("GET", f"/api/v2/meta/tables/{TABLE_ID}")["columns"]}
    for col in NEW_COLUMNS:
        if col["title"] in existing_columns:
            print(f"이미 존재함: {col['title']}")
            continue
        request("POST", f"/api/v2/meta/tables/{TABLE_ID}/columns", col)
        print(f"추가 완료: {col['title']}")


if __name__ == "__main__":
    main()
