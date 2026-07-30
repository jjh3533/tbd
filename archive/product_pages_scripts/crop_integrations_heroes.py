"""Integrations 제품 8개의 히어로 이미지를 crop_hero.py로 일괄 처리합니다."""
import subprocess
from pathlib import Path

ASSETS_DIR = Path("/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/assets")
CROP_HERO_SCRIPT = Path("/Users/cheil/tbd/product_pages/scripts/crop_hero.py")

# 처리할 히어로 이미지 목록
HERO_IMAGES = [
    "umr-industrial/umr-industrial_01-hero-front.png",
    "unas-2/unas-2_01-hero-front.png",
    "uc-cast-lite/uc-cast-lite_01-hero-front.png",
    "umr/umr_01-hero-front.png",
    "u5g-max/u5g-max_01-hero-front.png",
    "umr-ultra/umr-ultra_01-hero-front.png",
    "upl-port/upl-port_01-hero-front.png",
    "u-lte-pro/u-lte-pro_01-hero-front.png",
]

if __name__ == "__main__":
    print("Integrations 히어로 이미지 크롭 시작\n")

    for hero_path in HERO_IMAGES:
        full_path = ASSETS_DIR / hero_path
        if not full_path.exists():
            print(f"⚠️  파일 없음: {hero_path}")
            continue

        print(f"처리 중: {hero_path}")
        # crop_hero.py는 src와 dst를 같은 경로로 지정하면 덮어씀
        result = subprocess.run(
            ["python3", str(CROP_HERO_SCRIPT), str(full_path), str(full_path)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"  ✓ 완료")
            if result.stdout:
                print(f"    {result.stdout.strip()}")
        else:
            print(f"  ⚠️  오류: {result.stderr.strip()}")

    print("\n" + "="*60)
    print("히어로 이미지 크롭 완료.")
