#!/usr/bin/env python3
"""NocoDB에서 workspace와 base 정보를 조회합니다."""

import requests
from config import NOCODB_URL, NOCODB_API_TOKEN

def try_various_endpoints():
    """다양한 NocoDB API 엔드포인트를 시도합니다."""
    headers = {"xc-token": NOCODB_API_TOKEN}
    base_url = NOCODB_URL.rstrip('/')

    endpoints = [
        "/api/v1/db/meta/projects",  # v1 API
        "/api/v2/meta/bases",         # v2 메타
        "/api/v2/bases",              # v2 베이스
        "/api/v1/db/meta/tables",     # v1 테이블
    ]

    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            print(f"\n시도 중: {endpoint}")
            resp = requests.get(url, headers=headers, timeout=30)
            print(f"  상태 코드: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                print(f"  ✓ 성공! 응답:")
                import json
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                print("  ...")
            else:
                print(f"  응답: {resp.text[:200]}")

        except Exception as e:
            print(f"  ✗ 실패: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("NocoDB API 엔드포인트 탐색")
    print("=" * 60)
    try_various_endpoints()
