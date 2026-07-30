#!/usr/bin/env python3
"""네이버 WiFi 제품의 히어로 이미지 확인"""

import re
import requests
from auth import get_bearer_token
import naver_config
import config
from PIL import Image
from io import BytesIO

API_BASE = "https://api.commerce.naver.com/external/v2/products/channel-products"

# NocoDB에서 WiFi 제품 목록 가져오기
def get_wifi_products():
    headers = {"xc-token": config.NOCODB_API_TOKEN}
    url = f"{config.NOCODB_URL}/api/v2/tables/{config.NOCODB_TABLE_ID}/records"
    
    all_products = []
    offset = 0
    limit = 100
    
    while True:
        params = {"offset": offset, "limit": limit}
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        
        records = data.get("list", [])
        if not records:
            break
            
        all_products.extend(records)
        offset += limit
        
        if len(records) < limit:
            break
    
    # WiFi 카테고리만 필터링
    wifi = []
    for p in all_products:
        category = p.get("Category")
        if category == "WiFi":
            wifi.append(p)
    
    return wifi

def get_channel_product(token: str, channel_no: int):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/{channel_no}", headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()

def extract_first_image_url(detail_content: str):
    """detailContent에서 첫 번째 img src 추출"""
    pattern = r'<img\s+src="([^"]+)"'
    match = re.search(pattern, detail_content)
    return match.group(1) if match else None

token = get_bearer_token(naver_config.CLIENT_ID, naver_config.CLIENT_SECRET)
products = get_wifi_products()

print(f"WiFi 카테고리 네이버 등록 제품: {len(products)}개\n")

problems = []

for p in products:
    name = p.get("Product_Name", "")
    slug = p.get("Slug", "")
    channel_no = p.get("Naver_Product_No")
    
    if not channel_no:
        continue
    
    try:
        data = get_channel_product(token, int(channel_no))
        detail = data["originProduct"]["detailContent"]
        img_url = extract_first_image_url(detail)
        
        if img_url:
            resp = requests.get(img_url, timeout=10)
            img = Image.open(BytesIO(resp.content))
            w, h = img.size
            
            status = "✓" if h > 1000 else "⚠️"
            print(f"{status} {name}: {w}x{h}")
            
            if h <= 1000:
                problems.append((channel_no, slug, name, w, h))
            
        else:
            print(f"⚠️ {name}: 히어로 이미지 없음")
            
    except Exception as e:
        print(f"❌ {name}: {e}")

print(f"\n{'='*60}")
print(f"총 {len(products)}개 중 {len(problems)}개 문제 발견:")
for channel_no, slug, name, w, h in problems:
    print(f"  - {name} ({slug}): {w}x{h}")

