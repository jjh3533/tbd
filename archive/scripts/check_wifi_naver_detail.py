#!/usr/bin/env python3
"""네이버 WiFi 제품의 히어로 이미지 상세 확인"""

import re
import requests
from auth import get_bearer_token
import naver_config
import config
from PIL import Image
from io import BytesIO

API_BASE = "https://api.commerce.naver.com/external/v2/products/channel-products"

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
    
    wifi = [p for p in all_products if p.get("Category") == "WiFi"]
    return wifi

def get_channel_product(token: str, channel_no: int):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/{channel_no}", headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()

def extract_first_image_url(detail_content: str):
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
        print(f"❌ {name}: 미등록")
        continue
    
    try:
        data = get_channel_product(token, int(channel_no))
        detail = data["originProduct"]["detailContent"]
        img_url = extract_first_image_url(detail)
        
        if img_url:
            resp = requests.get(img_url, timeout=10)
            img = Image.open(BytesIO(resp.content))
            w, h = img.size
            
            # 높이 1500 이하는 잘린 것으로 판단
            status = "✓" if h > 1500 else "⚠️"
            print(f"{status} {name} ({slug}): {w}x{h}")
            
            if h <= 1500:
                problems.append((channel_no, slug, name, w, h))
            
        else:
            print(f"⚠️ {name}: 히어로 이미지 없음")
            
    except Exception as e:
        print(f"❌ {name}: {e}")

print(f"\n{'='*60}")
print(f"총 {len(products)}개 중 {len(problems)}개 문제 발견:")
for channel_no, slug, name, w, h in problems:
    print(f"  [{channel_no}] {name} ({slug}): {w}x{h}")

