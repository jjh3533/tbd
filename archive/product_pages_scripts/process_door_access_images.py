"""Door Access 제품 이미지 자동 처리 스크립트

Google Drive의 Product Images 폴더에서 Door Access 제품 이미지를 찾아
Product Pages_html/assets/ 폴더로 복사하고, 필요 시 크롭 처리합니다.
"""
import shutil
from pathlib import Path

# Google Drive 경로
PRODUCT_IMAGES_DIR = Path("/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Images")
PRODUCT_PAGES_DIR = Path("/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html")
ASSETS_DIR = PRODUCT_PAGES_DIR / "assets"

# Door Access 제품 매핑 (제품명 -> 이미지 폴더명 -> assets 폴더명)
DOOR_ACCESS_PRODUCTS = {
    # Batch 1: 핵심 제품
    "UniFi Reader Pro": ("UniFi Reader Pro", "ua-reader-pro"),
    "UniFi Reader Flex": ("UniFi Reader Flex", "ua-reader-flex"),
    "UniFi Access Ultra": ("UniFi Access Ultra", "ua-ultra"),
    "UniFi Door Hub": ("UniFi Door Hub", "ua-hub"),
    "UniFi Door Hub Mini": ("UniFi Door Hub Mini", "ua-hub-mini"),

    # Batch 2: 엔터프라이즈/인터콤
    "UniFi Enterprise Access Hub": ("UniFi Enterprise Access Hub", "ua-enterprise-hub"),
    "UniFi Intercom Viewer": ("UniFi Intercom Viewer", "ua-intercom-viewer"),
    "UniFi G6 Entry": ("UniFi G6 Entry", "g6-entry"),
    "UniFi Magnetic Lock": ("UniFi Magnetic Lock", "ua-magnetic-lock"),
    "UniFi Access Button": ("UniFi Access Button", "ua-button"),

    # Batch 3: 액세서리 (Simple)
    "UniFi Reader Junction Box": ("UniFi Reader Junction Box", "ua-reader-junction-box"),
    "UniFi Reader Pro Junction Box": ("UniFi Reader Pro Junction Box", "ua-reader-pro-junction-box"),
    "UniFi Reader Pro Angle Mount": ("UniFi Reader Pro Angle Mount", "ua-reader-pro-angle-mount"),
    "UniFi Intercom Viewer Table Stand": ("UniFi Intercom Viewer Table Stand", "ua-intercom-viewer-table-stand"),
    "UniFi Intercom Flush Mount": ("UniFi Intercom Flush Mount", "ua-intercom-flush-mount"),
    "UniFi Intercom Surface Angle Mount": ("UniFi Intercom Surface Angle Mount", "ua-intercom-surface-angle-mount"),
    "UniFi Intercom Wedge Mount": ("UniFi Intercom Wedge Mount", "ua-intercom-wedge-mount"),
    "UniFi Intercom Sunshield": ("UniFi Intercom Sunshield", "ua-intercom-sunshield"),
    "UniFi Gate Hub": ("UniFi Gate Hub", "ua-gate-hub"),
    "UniFi Junction Utility": ("UniFi Junction Utility", "ua-junction-utility"),
    "UniFi Door Lock Relay Cable": ("UniFi Door Lock Relay Cable", "ua-door-lock-relay-cable"),
    "UniFi Door Closer": ("UniFi Door Closer", "ua-door-closer"),
    "UniFi PoE Over 2-Wire Retrofit Extender": ("UniFi PoE Over 2-Wire Retrofit Extender", "ua-poe-2wire-extender"),
    "UniFi Retrofit Hub": ("UniFi Retrofit Hub", "ua-retrofit-hub"),
    "UniFi Retrofit PSU 12V": ("UniFi Retrofit PSU 12V", "ua-retrofit-psu-12v"),
    "UniFi Panic Bar": ("UniFi Panic Bar", "ua-panic-bar"),
    "UniFi Access Rescue KeySwitch": ("UniFi Access Rescue KeySwitch", "ua-rescue-keyswitch"),
    "UniFi Access Card (10-Pack)": ("UniFi Access Card", "ua-access-card-10pack"),
    "UniFi Pocket Keyfob, 10-Pack": ("UniFi Pocket Keyfob, 10-Pack", "ua-pocket-keyfob-10pack"),
    "UniFi Gate Starter Kit": ("UniFi Gate Starter Kit", "ua-gate-starter-kit"),
    "UniFi G3 Elevator Starter Kit": ("UniFi G3 Elevator Starter Kit", "ua-g3-elevator-starter-kit"),
}


def process_images():
    """모든 Door Access 제품 이미지를 처리합니다."""
    processed_count = 0
    skipped_count = 0

    for product_name, (source_folder, asset_folder) in DOOR_ACCESS_PRODUCTS.items():
        print(f"\n처리 중: {product_name}")

        source_dir = PRODUCT_IMAGES_DIR / source_folder
        target_dir = ASSETS_DIR / asset_folder

        if not source_dir.exists():
            print(f"  ⚠️  소스 폴더 없음: {source_dir}")
            skipped_count += 1
            continue

        # 타겟 디렉토리 생성
        target_dir.mkdir(parents=True, exist_ok=True)

        # 이미지 파일 복사
        image_files = list(source_dir.glob("*.png")) + list(source_dir.glob("*.jpg")) + list(source_dir.glob("*.jpeg"))

        if not image_files:
            print(f"  ⚠️  이미지 파일 없음: {source_dir}")
            skipped_count += 1
            continue

        for img_file in image_files:
            target_file = target_dir / img_file.name
            shutil.copy2(img_file, target_file)
            print(f"  ✓ 복사: {img_file.name}")

        processed_count += 1

    print(f"\n{'='*60}")
    print(f"✅ 처리 완료: {processed_count}개 제품")
    print(f"⚠️  건너뜀: {skipped_count}개 제품")
    print(f"{'='*60}")


if __name__ == "__main__":
    print("Door Access 제품 이미지 처리 시작...\n")
    process_images()
