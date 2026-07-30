"""Door Access 제품 히어로 이미지 파일명 표준화 스크립트

각 제품 폴더에서 첫 번째 이미지를 찾아 `{폴더명}_01-hero-front.png` 형식으로 복사합니다.
"""
import shutil
from pathlib import Path

PRODUCT_PAGES_DIR = Path("/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html")
ASSETS_DIR = PRODUCT_PAGES_DIR / "assets"

# Door Access 제품 assets 폴더명 리스트
DOOR_ACCESS_FOLDERS = [
    # Batch 1
    "ua-reader-pro", "ua-reader-flex", "ua-ultra", "ua-hub", "ua-hub-mini",
    # Batch 2
    "ua-enterprise-hub", "ua-intercom-viewer", "g6-entry", "ua-magnetic-lock", "ua-button",
    # Batch 3
    "ua-reader-junction-box", "ua-reader-pro-junction-box", "ua-reader-pro-angle-mount",
    "ua-intercom-viewer-table-stand", "ua-intercom-flush-mount", "ua-intercom-surface-angle-mount",
    "ua-intercom-wedge-mount", "ua-intercom-sunshield", "ua-gate-hub", "ua-junction-utility",
    "ua-door-lock-relay-cable", "ua-door-closer", "ua-poe-2wire-extender", "ua-retrofit-hub",
    "ua-retrofit-psu-12v", "ua-panic-bar", "ua-rescue-keyswitch", "ua-access-card-10pack",
    "ua-pocket-keyfob-10pack", "ua-gate-starter-kit", "ua-g3-elevator-starter-kit",
]


def standardize_hero_images():
    """각 제품 폴더의 첫 번째 이미지를 히어로 이미지로 복사합니다."""
    processed = 0
    skipped = 0

    for folder_name in DOOR_ACCESS_FOLDERS:
        folder_path = ASSETS_DIR / folder_name

        if not folder_path.exists():
            print(f"⚠️  폴더 없음: {folder_name}")
            skipped += 1
            continue

        # 모든 PNG 이미지 찾기 (숫자 순으로 정렬)
        image_files = sorted(folder_path.glob("*.png"))

        if not image_files:
            print(f"⚠️  이미지 없음: {folder_name}")
            skipped += 1
            continue

        # 첫 번째 이미지를 히어로 이미지로 복사
        first_image = image_files[0]
        hero_image = folder_path / f"{folder_name}_01-hero-front.png"

        if hero_image.exists():
            print(f"✓ 이미 존재: {folder_name}/{hero_image.name}")
        else:
            shutil.copy2(first_image, hero_image)
            print(f"✓ 생성: {folder_name}/{hero_image.name} (from {first_image.name})")

        processed += 1

    print(f"\n{'='*60}")
    print(f"✅ 처리 완료: {processed}개 제품")
    print(f"⚠️  건너뜀: {skipped}개 제품")
    print(f"{'='*60}")


if __name__ == "__main__":
    print("Door Access 히어로 이미지 표준화 시작...\n")
    standardize_hero_images()
