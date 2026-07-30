#!/usr/bin/env python3
"""U6 Mesh Pro 히어로 이미지 수정 - 크롭 없이 원본 그대로 사용"""

import os
import shutil
from PIL import Image

RAW_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Images"
ASSETS_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/assets"
EXPORTS_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/exports"

slug = "u6-mesh-pro"
raw_folder = "UniFi U6 Mesh Pro"
hero_src = "u6-mesh-pro-1.png"

print(f"=== {slug} 히어로 이미지 수정 ===\n")

# 1. 원본 이미지 확인
hero_in = os.path.join(RAW_DIR, raw_folder, hero_src)
if not os.path.exists(hero_in):
    print(f"❌ 원본 이미지 없음: {hero_in}")
    exit(1)

with Image.open(hero_in) as img:
    w, h = img.size
    print(f"1. 원본 이미지: {w}x{h}")

# 2. assets 폴더에 크롭 없이 복사
asset_dir = os.path.join(ASSETS_DIR, slug)
os.makedirs(asset_dir, exist_ok=True)
hero_out = os.path.join(asset_dir, f"{slug}_01-hero-front.png")

shutil.copy2(hero_in, hero_out)
print(f"2. ✓ assets에 원본 복사 완료")

with Image.open(hero_out) as img:
    print(f"   크기: {img.size[0]}x{img.size[1]}")

print(f"\n완료. 이제 export_wifi_pages.py를 실행해서 PNG를 재생성해야 합니다.")

