"""UniFi Mobile Router와 5G Max의 과도하게 크롭된 히어로 이미지를 원본으로 복구합니다."""
import shutil
from pathlib import Path
from PIL import Image

PRODUCT_IMAGES = Path("/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Images")
ASSETS_DIR = Path("/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/assets")

# 복구할 제품 정보
PRODUCTS = {
    "UniFi Mobile Router": {
        "folder": "UniFi Mobile Router",
        "original": "umr-us-1.png",
        "assets_folder": "umr",
        "hero_file": "umr_01-hero-front.png"
    },
    "UniFi 5G Max": {
        "folder": "UniFi 5G Max",
        "original": "u5g-max-1.png",
        "assets_folder": "u5g-max",
        "hero_file": "u5g-max_01-hero-front.png"
    }
}


def main():
    print("Integrations 히어로 이미지 복구 시작\n")

    for product_name, info in PRODUCTS.items():
        print(f"=== {product_name} ===")

        # 원본 경로
        original_path = PRODUCT_IMAGES / info["folder"] / info["original"]

        # assets 히어로 경로
        hero_path = ASSETS_DIR / info["assets_folder"] / info["hero_file"]

        if not original_path.exists():
            print(f"  ⚠️  원본 없음: {original_path}")
            continue

        # 원본 크기 확인
        img = Image.open(original_path)
        print(f"  원본: {img.size}")

        # 현재 히어로 크기 확인
        if hero_path.exists():
            current = Image.open(hero_path)
            print(f"  현재 히어로: {current.size}")
            print(f"  크롭 비율: {current.height / img.height * 100:.1f}%")

        # 원본을 히어로로 복사
        hero_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original_path, hero_path)
        print(f"  ✓ 원본으로 복구 완료")

        # 검증
        restored = Image.open(hero_path)
        print(f"  복구 후: {restored.size}")
        print()

    print("="*60)
    print("히어로 이미지 복구 완료.")
    print("\n다음 단계:")
    print("1. HTML/PNG 재생성")
    print("2. 네이버 히어로 이미지 업데이트")


if __name__ == "__main__":
    main()
