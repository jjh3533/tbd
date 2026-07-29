"""16개 WiFi 제품의 이미지를 자동으로 처리해 assets 폴더에 배치.

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
    ("AC Pro", "uap-ac-pro", "UniFi AC Pro", "uap-ac-pro-1.png", "uap-ac-pro-2.png"),
    ("Building Bridge XG", "ubb-xg", "UniFi Building Bridge XG", "ubb-xg-1.png", "ubb-xg-2.png"),
    ("Device Bridge", "udb", "UniFi Device Bridge", "udb-1.png", "udb-2.png"),
    ("Device Bridge Switch", "udb-switch", "UniFi Device Bridge Switch", "udb-switch-1.png", "udb-switch-2.png"),
    ("E7 Campus", "e7-campus", "UniFi E7 Campus", "e7-campus-us-1.png", "e7-campus-us-2.png"),
    ("U6 Enterprise", "u6-enterprise", "UniFi U6 Enterprise", "u6-enterprise-1.png", "u6-enterprise-2.png"),
    ("U6 Enterprise In-Wall", "u6-enterprise-iw", "UniFi U6 Enterprise In-Wall", "u6-enterprise-iw-1.png", "u6-enterprise-iw-2.png"),
    ("U6 In-Wall", "u6-iw", "UniFi U6 In-Wall", "u6-iw-1.png", "u6-iw-2.png"),
    ("U6 Mesh", "u6-mesh", "UniFi U6 Mesh", "u6-mesh-1.png", "u6-mesh-2.png"),
    ("U6 Mesh Pro", "u6-mesh-pro", "UniFi U6 Mesh Pro", "u6-mesh-pro-1.png", "u6-mesh-pro-2.png"),
    ("U6+", "u6-plus", "UniFi U6+", "u6-plus-1.png", "u6-plus-2.png"),
    ("U7 Outdoor", "u7-outdoor", "UniFi U7 Outdoor", "u7-outdoor-1.png", "u7-outdoor-2.png"),
    ("U7 Pro Outdoor", "u7-pro-outdoor", "UniFi U7 Pro Outdoor", "u7-pro-outdoor-us-1.png", "u7-pro-outdoor-us-2.png"),
    ("U7 Pro Wall", "u7-pro-wall", "UniFi U7 Pro Wall", "u7-pro-wall-1.png", "u7-pro-wall-2.png"),
    ("U7 Pro XG Wall", "u7-pro-xg-wall", "UniFi U7 Pro XG Wall", "u7-pro-xg-wall-1.png", "u7-pro-xg-wall-2.png"),
    ("U7 Pro XGS", "u7-pro-xgs", "UniFi U7 Pro XGS", "u7-pro-xgs-1.png", "u7-pro-xgs-2.png"),
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
