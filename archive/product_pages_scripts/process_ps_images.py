"""13개 Physical Security 제품의 이미지를 자동으로 처리해 assets 폴더에 배치.

각 제품마다:
1. assets/<slug>/ 디렉토리 생성
2. Hero 이미지 (제품 정면, -1.png) → crop_hero.py로 반사 제거 → _01-hero-front.png
3. Diagram 이미지 (포트/구성도, 적절한 원본) → 복사 → _02-diagram.png
"""
import os
import shutil
import subprocess

RAW_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Images"
ASSETS_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/assets"
CROP_SCRIPT = "/Users/cheil/tbd/product_pages/scripts/crop_hero.py"

# (제품명, assets slug, raw 폴더명, hero 원본 파일명, diagram 원본 파일명)
PRODUCTS = [
    # Batch 1: 카메라 5개
    ("G6 Pro 360", "uvc-g6-pro-360", "UniFi G6 Pro 360", "uvc-g6-pro-360-1.png", "uvc-g6-pro-360-2.png"),
    ("AI PTZ Industrial", "uvc-ai-ptz", "UniFi AI PTZ Industrial", "uvc-ai-ptz-1.png", "uvc-ai-ptz-2.png"),
    ("G5 Turret Ultra", "uvc-g5-turret-ultra", "UniFi G5 Turret Ultra", "uvc-g5-turret-ultra-1.png", "uvc-g5-turret-ultra-2.png"),
    ("G6 Dome", "uvc-g6-dome", "UniFi G6 Dome", "uvc-g6-dome-1.png", "uvc-g6-dome-2.png"),
    ("AI Theta", "uvc-ai-theta-hub", "UniFi AI Theta", "uvc-ai-theta-hub-1.png", "uvc-ai-theta-hub-2.png"),

    # Batch 2: 센서 3개
    ("All-In-One Sensor", "up-sense", "UniFi All-In-One Sensor", "up-sense-1.png", "up-sense-2.png"),
    ("Glass Break Sensor", "usl-glassbreak", "UniFi Glass Break Sensor", "usl-glassbreak-1.png", "usl-glassbreak-2.png"),
    ("Motion Sensor", "usl-motion", "UniFi Motion Sensor", "usl-motion-1.png", "usl-motion-2.png"),

    # Batch 3: 녹화/컨트롤 2개
    ("Network Video Recorder Instant", "unvr-instant", "UniFi Network Video Recorder Instant", "unvr-instant-1.png", "unvr-instant-2.png"),
    ("CloudKey+", "uck-g2-ssd", "UniFi CloudKey+", "uck-g2-ssd-1.png", "uck-g2-ssd-2.png"),

    # Batch 4: 기타 3개
    ("AI Horn Speaker", "up-ai-horn-speaker", "UniFi AI Horn Speaker", "up-ai-horn-speaker-1.png", "up-ai-horn-speaker-2.png"),
    ("SuperLink Gateway", "usl-gateway", "UniFi SuperLink Gateway", "usl-gateway-1.png", "usl-gateway-2.png"),
    ("Floodlight", "up-floodlight", "UniFi Floodlight", "up-floodlight-1.png", "up-floodlight-2.png"),
]

for name, slug, raw_folder, hero_src, diagram_src in PRODUCTS:
    print(f"\n=== {name} ({slug}) ===")

    # 1. assets 디렉토리 생성
    asset_dir = os.path.join(ASSETS_DIR, slug)
    os.makedirs(asset_dir, exist_ok=True)

    # 2. Hero 이미지 크롭
    hero_in = os.path.join(RAW_DIR, raw_folder, hero_src)
    hero_out = os.path.join(asset_dir, f"{slug}_01-hero-front.png")

    if not os.path.exists(hero_in):
        print(f"  ❌ Hero 원본 없음: {hero_in}")
        continue

    try:
        result = subprocess.run(
            ["python3", CROP_SCRIPT, hero_in, hero_out],
            capture_output=True, text=True, check=True
        )
        print(f"  ✓ Hero cropped: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Hero crop 실패: {e.stderr}")
        continue

    # 3. Diagram 이미지 복사
    diagram_in = os.path.join(RAW_DIR, raw_folder, diagram_src)
    diagram_out = os.path.join(asset_dir, f"{slug}_02-diagram.png")

    if not os.path.exists(diagram_in):
        print(f"  ⚠️  Diagram 원본 없음: {diagram_in}")
        continue

    shutil.copy2(diagram_in, diagram_out)
    print(f"  ✓ Diagram copied")

print("\n\n=== 완료 ===")
print(f"{len(PRODUCTS)}개 제품 이미지 처리 완료")
