"""Door Access 제품 다이어그램 이미지 표준화 스크립트

각 제품 폴더에서 두 번째 이미지를 찾아 `{폴더명}_02-diagram.png` 형식으로 복사합니다.
(Simple 액세서리는 히어로만 있으므로 제외)
"""
import shutil
from pathlib import Path

PRODUCT_PAGES_DIR = Path("/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html")
ASSETS_DIR = PRODUCT_PAGES_DIR / "assets"

# 다이어그램이 필요한 제품 (Batch 1, 2만 - Simple 제외)
PRODUCTS_WITH_DIAGRAM = [
    # Batch 1
    "ua-reader-pro", "ua-reader-flex", "ua-ultra", "ua-hub", "ua-hub-mini",
    # Batch 2
    "ua-enterprise-hub", "ua-intercom-viewer", "g6-entry", "ua-magnetic-lock", "ua-button",
]


def standardize_diagram_images():
    """각 제품 폴더의 두 번째 이미지를 다이어그램 이미지로 복사합니다."""
    processed = 0
    skipped = 0

    for folder_name in PRODUCTS_WITH_DIAGRAM:
        folder_path = ASSETS_DIR / folder_name

        if not folder_path.exists():
            print(f"⚠️  폴더 없음: {folder_name}")
            skipped += 1
            continue

        # 모든 PNG 이미지 찾기 (숫자 순으로 정렬)
        image_files = sorted(folder_path.glob("*.png"))

        if len(image_files) < 2:
            print(f"⚠️  이미지 부족: {folder_name} (only {len(image_files)} files)")
            skipped += 1
            continue

        # 두 번째 이미지를 다이어그램 이미지로 복사
        second_image = image_files[1]
        diagram_image = folder_path / f"{folder_name}_02-diagram.png"

        if diagram_image.exists():
            print(f"✓ 이미 존재: {folder_name}/{diagram_image.name}")
        else:
            shutil.copy2(second_image, diagram_image)
            print(f"✓ 생성: {folder_name}/{diagram_image.name} (from {second_image.name})")

        processed += 1

    print(f"\n{'='*60}")
    print(f"✅ 처리 완료: {processed}개 제품")
    print(f"⚠️  건너뜀: {skipped}개 제품")
    print(f"{'='*60}")


if __name__ == "__main__":
    print("Door Access 다이어그램 이미지 표준화 시작...\n")
    standardize_diagram_images()
