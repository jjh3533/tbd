"""UniFi Mobile Router와 5G Max의 네이버 히어로 이미지를 업데이트합니다."""
import argparse
import requests
import json
import sys
sys.path.insert(0, '../..')

from naver_config import CLIENT_ID, CLIENT_SECRET
from auth import get_bearer_token
from image_uploader import upload_images

# 업데이트할 제품 정보 (채널상품번호)
PRODUCTS = {
    "13686935205": {  # Mobile Router
        "name": "UniFi Mobile Router",
        "image_path": "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Images/UniFi Mobile Router/umr-us-1.png"
    },
    "13686935032": {  # 5G Max
        "name": "UniFi 5G Max",
        "image_path": "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Images/UniFi 5G Max/u5g-max-1.png"
    }
}


def get_origin_product_no(channel_product_no):
    """registered_log.json에서 originProductNo를 찾습니다."""
    with open('registered_log.json', 'r', encoding='utf-8') as f:
        log = json.load(f)

    for key, value in log.items():
        if str(value.get('smartstoreChannelProductNo')) == str(channel_product_no):
            return value.get('originProductNo')

    return None


def update_hero_image(channel_product_no, image_path, dry_run=False):
    """네이버 상품의 히어로 이미지를 업데이트합니다."""
    token = get_bearer_token(CLIENT_ID, CLIENT_SECRET)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    # 1. registered_log.json에서 originProductNo 찾기
    origin_product_no = get_origin_product_no(channel_product_no)
    if not origin_product_no:
        raise ValueError(f"registered_log.json에서 채널상품번호 {channel_product_no}를 찾을 수 없습니다")

    print(f"  originProductNo: {origin_product_no}")

    # 2. 현재 상품 정보 조회
    get_url = f'https://api.commerce.naver.com/external/v2/products/origin-products/{origin_product_no}'
    resp = requests.get(get_url, headers=headers, timeout=30)
    resp.raise_for_status()
    current = resp.json()

    origin_product = current.get('originProduct', {})

    if dry_run:
        print(f"  [dry-run] 이미지 업로드 및 업데이트 건너뜀")
        return

    # 3. 새 이미지 업로드
    print(f"  이미지 업로드 중...")
    new_image_url = upload_images(token, [image_path])[0]
    print(f"  ✓ 업로드 완료: {new_image_url[:80]}...")

    # 4. 대표 이미지만 교체
    origin_product['images']['representativeImage']['url'] = new_image_url

    # 5. PUT 요청
    put_url = f'https://api.commerce.naver.com/external/v2/products/origin-products/{origin_product_no}'

    # statusType 정규화
    if origin_product.get('statusType') == 'OUTOFSTOCK':
        origin_product['statusType'] = 'SALE'

    put_resp = requests.put(
        put_url,
        headers=headers,
        json={'originProduct': origin_product},
        timeout=30
    )
    put_resp.raise_for_status()

    print(f"  ✓ 네이버 히어로 이미지 업데이트 완료")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='실제 변경 없이 미리보기만')
    args = parser.parse_args()

    print(f"Integrations 히어로 이미지 네이버 업데이트 {'(DRY-RUN)' if args.dry_run else ''}\n")

    for channel_no, info in PRODUCTS.items():
        print(f"=== {info['name']} (채널번호: {channel_no}) ===")

        try:
            update_hero_image(channel_no, info['image_path'], args.dry_run)
            print()
        except Exception as e:
            print(f"  ⚠️  오류: {e}\n")
            continue

    print("완료!")


if __name__ == '__main__':
    main()
