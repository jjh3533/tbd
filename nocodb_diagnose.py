#!/usr/bin/env python3
"""NocoDB Products 테이블 필드 목록을 점검하는 스크립트.

사용법 (터미널에서, 본인 Mac에서 실행):
    NOCODB_URL="http://jayjeon.net:8081" NOCODB_TOKEN="여기에_토큰" python3 nocodb_diagnose.py

토큰 발급 방법:
    NocoDB 우측 상단 프로필 아이콘 클릭 -> Account Settings -> Tokens -> Create New Token
"""
import json
import os
import sys
import urllib.request
import urllib.error

NOCODB_URL = os.environ.get("NOCODB_URL", "").rstrip("/")
NOCODB_TOKEN = os.environ.get("NOCODB_TOKEN", "")

if not NOCODB_URL or not NOCODB_TOKEN:
    print("NOCODB_URL과 NOCODB_TOKEN 환경변수를 설정해주세요.")
    print('예: NOCODB_URL="http://jayjeon.net:8081" NOCODB_TOKEN="xxxx" python3 nocodb_diagnose.py')
    sys.exit(1)


def get(path):
    url = f"{NOCODB_URL}{path}"
    req = urllib.request.Request(url, headers={"xc-token": NOCODB_TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} 에러: {url}")
        print(e.read().decode("utf-8"))
        sys.exit(1)


def main():
    bases = get("/api/v2/meta/bases")["list"]
    base = next((b for b in bases if "unifi" in b["title"].lower()), None)
    if not base:
        print("Base를 찾을 수 없습니다. 전체 목록:", [b["title"] for b in bases])
        sys.exit(1)
    print(f"Base: {base['title']}  (id={base['id']})")

    tables = get(f"/api/v2/meta/bases/{base['id']}/tables")["list"]
    table = next((t for t in tables if t["title"] == "Products"), None)
    if not table:
        print("Products 테이블을 찾을 수 없습니다. 전체 목록:", [t["title"] for t in tables])
        sys.exit(1)
    print(f"Table: {table['title']}  (id={table['id']})")

    detail = get(f"/api/v2/meta/tables/{table['id']}")
    print("\n현재 필드 목록:")
    for col in detail["columns"]:
        print(f"  - title={col['title']!r:35s} uidt={col.get('uidt'):15s} id={col['id']}")


if __name__ == "__main__":
    main()
