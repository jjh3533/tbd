"""Integrations 6개 제품의 네이버 판매가를 NocoDB '판매금액'으로 수정합니다.

네이버에 등록된 가격이 '구매원가'로 잘못 등록되어 있어서,
'판매금액'(실제 판매가)으로 수정합니다. 할인 없이 판매금액만 설정합니다.
"""
import argparse
import sys
sys.path.insert(0, '.')

from nocodb_client import NocoDBTable
from config import NOCODB_URL, NOCODB_TABLE_ID, NOCODB_API_TOKEN
from naver_config import CLIENT_ID, CLIENT_SECRET
from auth import get_bearer_token
import requests

# Integrations 제품 매핑
PRODUCTS = {
    '13686935032': 'UniFi 5G Max',
    '13686935179': 'UniFi LTE Backup Pro',
    '13686935205': 'UniFi Mobile Router',
    '13686935223': 'UniFi Mobile Router Ultra',
    '13686935266': 'UniFi PoE Audio Port',
    '13686935352': 'UniFi UNAS 2',
}


def update_naver_price(channel_product_no, new_price, dry_run=False):
    """네이버 상품의 판매가를 업데이트합니다."""
    token = get_bearer_token(CLIENT_ID, CLIENT_SECRET)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    # 1. 현재 상품 정보 조회
    get_url = f'https://api.commerce.naver.com/external/v2/products/channel-products/{channel_product_no}'
    resp = requests.get(get_url, headers=headers, timeout=30)
    resp.raise_for_status()
    current = resp.json()

    origin_product = current.get('originProduct', {})
    current_price = origin_product.get('salePrice', 0)

    print(f"  현재 네이버 판매가: {current_price:,}원")
    print(f"  변경할 판매가: {new_price:,}원")

    if dry_run:
        print(f"  [dry-run] 변경하지 않음")
        return

    # 2. 판매가만 변경하여 PUT
    origin_product['salePrice'] = new_price

    # customerBenefit에 할인 정보가 있으면 제거
    if 'customerBenefit' in origin_product:
        del origin_product['customerBenefit']

    put_url = f'https://api.commerce.naver.com/external/v2/products/origin-products/{origin_product["id"]}'
    put_resp = requests.put(
        put_url,
        headers=headers,
        json={'originProduct': origin_product},
        timeout=30
    )
    put_resp.raise_for_status()

    print(f"  ✓ 네이버 판매가 업데이트 완료")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='실제 변경 없이 미리보기만')
    parser.add_argument('--limit', type=int, help='처음 N개만 처리')
    args = parser.parse_args()

    # NocoDB에서 판매금액 가져오기
    table = NocoDBTable(
        base_url=NOCODB_URL,
        api_token=NOCODB_API_TOKEN,
        table_id=NOCODB_TABLE_ID
    )

    all_records = table.all()

    print(f"Integrations 제품 네이버 가격 수정 {'(DRY-RUN)' if args.dry_run else ''}\n")

    processed = 0
    for channel_no, sku in PRODUCTS.items():
        if args.limit and processed >= args.limit:
            break

        # NocoDB에서 판매금액 찾기
        record = [r for r in all_records if r['fields'].get('SKU') == sku]
        if not record:
            print(f"⚠️  {sku}: NocoDB에서 찾을 수 없음")
            continue

        sale_price = record[0]['fields'].get('판매금액', 0)
        if not sale_price:
            print(f"⚠️  {sku}: 판매금액이 0원")
            continue

        print(f"=== {sku} (채널번호: {channel_no}) ===")

        try:
            update_naver_price(channel_no, sale_price, args.dry_run)
            processed += 1
            print()
        except Exception as e:
            print(f"  ⚠️  오류: {e}\n")
            continue

    print(f"총 {processed}개 처리 완료")


if __name__ == '__main__':
    main()
