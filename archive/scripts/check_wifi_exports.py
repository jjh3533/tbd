#!/usr/bin/env python3
"""WiFi exports에서 히어로 이미지 크기 확인"""

from PIL import Image
import os

WIFI_PRODUCTS = [
    "u7-pro-max", "u7-pro", "u7-pro-wall", "u7-outdoor",
    "u6-plus", "u6-mesh", "u6-extender", "u6-in-wall",
    "u6-enterprise-in-wall", "u6-enterprise", "u7-pro-xg",
    "building-to-building-bridge", "u6-lr", "u6-lite",
    "access-point-wifi-7-pro", "access-point-wifi-7-pro-max"
]

EXPORTS_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/exports"

print("WiFi 제품 히어로 이미지 크기 확인\n")

for slug in WIFI_PRODUCTS:
    hero_path = f"{EXPORTS_DIR}/{slug}/01-hero.png"
    
    if not os.path.exists(hero_path):
        print(f"❌ {slug}: 파일 없음")
        continue
    
    with Image.open(hero_path) as img:
        w, h = img.size
        
    # 정상 크기는 860x1153 (1500x1500 원본을 860 너비로 스케일)
    # 잘린 경우 높이가 훨씬 작을 것
    status = "✓" if h > 1000 else "⚠️"
    print(f"{status} {slug}: {w}x{h}")

