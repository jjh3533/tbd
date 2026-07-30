#!/usr/bin/env python3
"""Physical Security 히어로 이미지 크롭 검증 및 재처리"""

from PIL import Image
import os

RAW_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Images"
ASSETS_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/assets"

# (제품명, assets slug, raw 폴더명, hero 원본 파일명)
PRODUCTS = [
    ("G6 Pro 360", "uvc-g6-pro-360", "UniFi G6 Pro 360", "uvc-g6-pro-360-1.png"),
    ("AI PTZ Industrial", "uvc-ai-ptz", "UniFi AI PTZ Industrial", "uvc-ai-ptz-1.png"),
    ("G5 Turret Ultra", "uvc-g5-turret-ultra", "UniFi G5 Turret Ultra", "uvc-g5-turret-ultra-1.png"),
    ("G6 Dome", "uvc-g6-dome", "UniFi G6 Dome", "uvc-g6-dome-1.png"),
    ("AI Theta", "uvc-ai-theta-hub", "UniFi AI Theta", "uvc-ai-theta-hub-1.png"),
    ("All-In-One Sensor", "up-sense", "UniFi All-In-One Sensor", "up-sense-1.png"),
    ("Glass Break Sensor", "usl-glassbreak", "UniFi Glass Break Sensor", "usl-glassbreak-1.png"),
    ("Motion Sensor", "usl-motion", "UniFi Motion Sensor", "usl-motion-1.png"),
    ("NVR Instant", "unvr-instant", "UniFi Network Video Recorder Instant", "unvr-instant-1.png"),
    ("CloudKey+", "uck-g2-ssd", "UniFi CloudKey+", "uck-g2-ssd-1.png"),
    ("AI Horn Speaker", "up-ai-horn-speaker", "UniFi AI Horn Speaker", "up-ai-horn-speaker-1.png"),
    ("SuperLink Gateway", "usl-gateway", "UniFi SuperLink Gateway", "usl-gateway-1.png"),
    ("Floodlight", "up-floodlight", "UniFi Floodlight", "up-floodlight-1.png"),
]

print("히어로 이미지 크롭 검증:\n")

for name, slug, raw_folder, hero_src in PRODUCTS:
    hero_in = os.path.join(RAW_DIR, raw_folder, hero_src)
    hero_out = os.path.join(ASSETS_DIR, slug, f"{slug}_01-hero-front.png")

    if not os.path.exists(hero_in):
        print(f"❌ {name}: 원본 없음")
        continue

    if not os.path.exists(hero_out):
        print(f"❌ {name}: 크롭본 없음")
        continue

    # 이미지 크기 비교
    img_in = Image.open(hero_in)
    img_out = Image.open(hero_out)

    w_in, h_in = img_in.size
    w_out, h_out = img_out.size

    # 높이 비율 계산 (크롭 후 / 원본)
    height_ratio = h_out / h_in

    # 높이가 50% 미만으로 크롭되었다면 문제 가능성
    if height_ratio < 0.5:
        print(f"⚠️  {name:25s} 원본: {w_in}x{h_in} → 크롭: {w_out}x{h_out} (높이 {height_ratio:.1%}) - 제품 잘림 가능성")
    else:
        print(f"✓ {name:25s} 원본: {w_in}x{h_in} → 크롭: {w_out}x{h_out} (높이 {height_ratio:.1%})")
