#!/usr/bin/env python3
"""Order_Fulfillment 테이블에 "DB만 보고 렌더링" 전환에 필요한 필드를 추가합니다 (1회성 스크립트).

/orders 페이지가 열람/새로고침 시엔 네이버·ACE Express를 전혀 호출하지 않고
Order_Fulfillment에 저장된 값만 읽도록 바뀌면서, 예전엔 매번 라이브로 조회해
그 자리에서만 쓰고 버리던 값 두 가지를 저장해둘 곳이 필요해졌다:

- naver_order_status: 네이버 주문 상태(orderStatus) - "완료" 단계 판정에 필요.
  동기화 버튼을 누를 때마다 최신값으로 덮어쓴다(주문 상태는 되돌아갈 수 있는
  값이라 다른 ace_* 필드처럼 "한 번 확정되면 고정"이 아님).
- ace_intl_shipped_at: ACE Express 송장조회에서 이벤트가 처음 확인된 시각
  (통관 시작 이전, "국제배송 시작"의 근거) - 예전엔 매 새로고침마다 라이브로
  판정하던 것("이번에 조회했더니 이벤트가 있더라")을 이제는 동기화 시점에
  저장해둬야 페이지 열람 시 DB만 보고도 같은 판정을 할 수 있다.

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
    {"title": "naver_order_status", "uidt": "SingleLineText"},
    {"title": "ace_intl_shipped_at", "uidt": "DateTime"},
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
