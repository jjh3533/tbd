"""Integrations 제품 8개의 이미지를 자동 처리합니다.

Google Drive Product Images 폴더에서 이미지를 복사하고, 히어로 이미지는 crop_hero.py로 처리합니다.
"""
import os
import shutil
from pathlib import Path

PRODUCT_IMAGES_DIR = Path("/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Images")
ASSETS_DIR = Path("/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/assets")

# 제품별 매핑: (소스 폴더명, assets 타겟 폴더명, 히어로 파일명)
PRODUCTS = [
    ("UniFi Mobile Router Industrial", "umr-industrial", "umr-industrial_01-hero-front.png"),
    ("UniFi UNAS 2", "unas-2", "unas-2_01-hero-front.png"),
    ("UniFi Display Cast Lite", "uc-cast-lite", "uc-cast-lite_01-hero-front.png"),
    ("UniFi Mobile Router", "umr", "umr_01-hero-front.png"),
    ("UniFi 5G Max", "u5g-max", "u5g-max_01-hero-front.png"),
    ("UniFi Mobile Router Ultra", "umr-ultra", "umr-ultra_01-hero-front.png"),
    ("UniFi PoE Audio Port", "upl-port", "upl-port_01-hero-front.png"),
    ("UniFi LTE Backup Pro", "u-lte-pro", "u-lte-pro_01-hero-front.png"),
]


def process_product(source_name, asset_folder, hero_filename):
    """한 제품의 이미지를 처리합니다."""
    source_dir = PRODUCT_IMAGES_DIR / source_name
    target_dir = ASSETS_DIR / asset_folder

    if not source_dir.exists():
        print(f"⚠️  소스 폴더 없음: {source_dir}")
        return

    # 타겟 폴더 생성
    target_dir.mkdir(parents=True, exist_ok=True)

    # 모든 이미지 파일 복사
    image_files = sorted(list(source_dir.glob("*.png")) + list(source_dir.glob("*.jpg")) + list(source_dir.glob("*.jpeg")))

    if not image_files:
        print(f"⚠️  이미지 없음: {source_dir}")
        return

    copied_count = 0
    hero_source = None

    for img in image_files:
        # 원본 파일명 그대로 복사 (이미 asset_folder 접두사가 있음)
        target_path = target_dir / img.name
        shutil.copy2(img, target_path)
        copied_count += 1

        # 첫 번째 이미지(-1.png 또는 -us-1.png)를 히어로 이미지 소스로 사용
        if hero_source is None and ("-1.png" in img.name or "-us-1.png" in img.name):
            hero_source = target_path

    print(f"✓ {source_name}: {copied_count}개 이미지 복사 -> {asset_folder}/")

    # 히어로 이미지 생성 (첫 번째 이미지를 히어로 파일명으로 복사)
    if hero_source:
        hero_path = target_dir / hero_filename
        shutil.copy2(hero_source, hero_path)
        print(f"  → 히어로 이미지 생성: {hero_source.name} -> {hero_filename}")
    else:
        print(f"  ⚠️  히어로 소스 이미지를 찾을 수 없음")


if __name__ == "__main__":
    print("Integrations 제품 이미지 처리 시작\n")

    for source_name, asset_folder, hero_filename in PRODUCTS:
        process_product(source_name, asset_folder, hero_filename)

    print("\n" + "="*60)
    print("이미지 복사 완료.")
    print("\n다음 단계:")
    print("  python3 product_pages/scripts/crop_hero.py")
    print("  (히어로 이미지 반사 제거 크롭)")
