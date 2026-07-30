#!/usr/bin/env python3
"""WiFi 카테고리 히어로 이미지 크롭 검증"""

import os
from PIL import Image

# WiFi 제품 목록
WIFI_PRODUCTS = [
    "u7-pro-max", "u7-pro", "u7-pro-wall", "u7-outdoor",
    "u6-plus", "u6-mesh", "u6-extender", "u6-in-wall",
    "u6-enterprise-in-wall", "u6-enterprise", "u7-pro-xg",
    "building-to-building-bridge", "u6-lr", "u6-lite",
    "access-point-wifi-7-pro", "access-point-wifi-7-pro-max"
]

RAW_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/raw"
PROCESSED_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/processed"

def check_hero_crop(slug: str):
    """히어로 이미지 크롭 비율 체크"""
    raw_hero = f"{RAW_DIR}/{slug}/hero.png"
    processed_hero = f"{PROCESSED_DIR}/{slug}/hero.png"
    
    if not os.path.exists(raw_hero):
        return None, "raw hero 없음"
    if not os.path.exists(processed_hero):
        return None, "processed hero 없음"
    
    with Image.open(raw_hero) as raw_img:
        raw_w, raw_h = raw_img.size
    
    with Image.open(processed_hero) as proc_img:
        proc_w, proc_h = proc_img.size
    
    height_ratio = proc_h / raw_h if raw_h > 0 else 0
    
    return {
        "raw": (raw_w, raw_h),
        "processed": (proc_w, proc_h),
        "height_ratio": height_ratio
    }, None

print("WiFi 카테고리 히어로 이미지 크롭 검증\n")

problems = []
for slug in WIFI_PRODUCTS:
    result, error = check_hero_crop(slug)
    if error:
        print(f"❌ {slug}: {error}")
        continue
    
    ratio = result["height_ratio"]
    status = "✓" if ratio > 0.7 else "⚠️"
    
    print(f"{status} {slug}:")
    print(f"   원본: {result['raw'][0]}x{result['raw'][1]}")
    print(f"   처리: {result['processed'][0]}x{result['processed'][1]}")
    print(f"   높이 비율: {ratio:.1%}")
    
    if ratio < 0.7:
        problems.append((slug, ratio))

print(f"\n{'='*60}")
print(f"총 {len(WIFI_PRODUCTS)}개 중 {len(problems)}개 과도하게 크롭됨:")
for slug, ratio in problems:
    print(f"  - {slug}: {ratio:.1%}")
