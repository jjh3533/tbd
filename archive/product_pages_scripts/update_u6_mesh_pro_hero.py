#!/usr/bin/env python3
"""U6 Mesh Pro 히어로 이미지만 네이버에 업데이트"""

import re
import requests
import sys
import os

# 현재 디렉토리를 경로에 추가
sys.path.insert(0, '/Users/cheil/tbd')

from auth import get_bearer_token
import naver_config as config
from image_uploader import upload_with_retry

API_BASE = "https://api.commerce.naver.com/external/v2/products/channel-products"
EXPORTS_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/exports"

channel_no = 13686840101
slug = "u6-mesh-pro"

print(f"=== U6 Mesh Pro 히어로 이미지 업데이트 ===\n")

token = get_bearer_token(config.CLIENT_ID, config.CLIENT_SECRET)

# 1. 현재 제품 데이터 가져오기
headers = {"Authorization": f"Bearer {token}"}
resp = requests.get(f"{API_BASE}/{channel_no}", headers=headers, timeout=30)
resp.raise_for_status()
product_data = resp.json()

print(f"제품명: {product_data['originProduct']['name']}")

# 2. 새 히어로 이미지 업로드
new_hero_path = f"{EXPORTS_DIR}/{slug}/01-hero.png"
print(f"새 히어로: {new_hero_path}")

urls = upload_with_retry(token, [new_hero_path])
new_hero_url = urls[0]
print(f"업로드 완료: {new_hero_url}")

# 3. detailContent에서 첫 번째 이미지 교체
old_content = product_data["originProduct"]["detailContent"]
pattern = r'(<img\s+src=")([^"]+)("\s+style="[^"]*"\s*/?>)'
match = re.search(pattern, old_content)

if not match:
    print("❌ 첫 번째 이미지 태그를 찾을 수 없음")
    exit(1)

new_content = old_content[:match.start(2)] + new_hero_url + old_content[match.end(2):]

# 4. 전체 body에서 detailContent만 수정
product_data["originProduct"]["detailContent"] = new_content

# statusType이 OUTOFSTOCK이면 SALE로 변경
if product_data["originProduct"].get("statusType") == "OUTOFSTOCK":
    product_data["originProduct"]["statusType"] = "SALE"

# 5. PUT으로 업데이트
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
resp = requests.put(f"{API_BASE}/{channel_no}", json=product_data, headers=headers, timeout=30)

try:
    resp.raise_for_status()
    print("\n✓ 히어로 이미지 교체 완료")
except requests.exceptions.HTTPError:
    print(f"\n❌ 오류: {resp.status_code}")
    print(f"응답: {resp.text}")

