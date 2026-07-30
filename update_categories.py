#!/usr/bin/env python3
"""
네이버 스마트스토어 상품의 카테고리를 더 적합한 카테고리로 업데이트합니다.

주요 변경사항:
1. Door Access 제품 (31개): 네트워크장비>AP (50001623) → 생활가전>디지털도어록>주키형 (50002359)
2. UNAS 2: 네트워크장비>AP (50001623) → 저장장치>NAS (50001602)
3. Mobile Router 제품: 네트워크장비>AP (50001623) → 네트워크장비>라우터 (50001622)

사용법:
  python3 update_categories.py --dry-run              # 미리보기
  python3 update_categories.py --limit 1              # 1개만 테스트
  python3 update_categories.py                        # 전체 실행
"""

import argparse
import sys
from typing import Dict, List

from auth import auth_headers, get_bearer_token
from naver_config import CLIENT_ID, CLIENT_SECRET
import requests


# 카테고리 매핑 (상품명 키워드 → 새 카테고리 ID)
CATEGORY_MAPPING = {
    # Door Access 제품 → 디지털도어록>주키형
    'door_access': {
        'category_id': 50002359,
        'category_name': '디지털/가전 > 생활가전 > 디지털도어록 > 주키형',
        'keywords': [
            'Reader', 'Access', 'Door', 'Gate', 'Intercom', 'Entry',
            'Lock', 'Button', 'KeySwitch', 'Card', 'Keyfob',
            '리더', '출입', '도어', '게이트', '인터콤', '잠금'
        ]
    },
    # NAS 제품 → 저장장치>NAS
    'nas': {
        'category_id': 50001602,
        'category_name': '디지털/가전 > 저장장치 > NAS',
        'keywords': ['UNAS', 'NAS']
    },
    # Mobile Router 제품 → 네트워크장비>라우터
    'router': {
        'category_id': 50001622,
        'category_name': '디지털/가전 > 네트워크장비 > 라우터',
        'keywords': ['Mobile Router', '5G Max', 'LTE Backup', '모바일 라우터']
    },
}


def get_product_category_type(product_name: str, category: str) -> tuple[str, int, str] | None:
    """상품명과 카테고리를 보고 적합한 카테고리 타입을 반환합니다."""
    product_name_lower = product_name.lower()

    # 우선순위: NAS > Router > Door Access (더 구체적인 것 먼저)
    if any(kw.lower() in product_name_lower for kw in CATEGORY_MAPPING['nas']['keywords']):
        return ('nas', CATEGORY_MAPPING['nas']['category_id'], CATEGORY_MAPPING['nas']['category_name'])

    if any(kw.lower() in product_name_lower for kw in CATEGORY_MAPPING['router']['keywords']):
        return ('router', CATEGORY_MAPPING['router']['category_id'], CATEGORY_MAPPING['router']['category_name'])

    # Door Access 카테고리인 경우만 처리 (키워드 매칭은 오탐이 많아서 제외)
    if category == 'Door Access':
        return ('door_access', CATEGORY_MAPPING['door_access']['category_id'], CATEGORY_MAPPING['door_access']['category_name'])

    return None


def get_channel_product(channel_product_no: str, headers: Dict) -> Dict | None:
    """네이버 채널상품 정보를 조회합니다."""
    url = f"https://api.commerce.naver.com/external/v2/products/channel-products/{channel_product_no}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ⚠️  조회 실패: {response.status_code} {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  ⚠️  조회 에러: {e}")
        return None


def update_channel_product_category(
    channel_product_no: str,
    new_category_id: int,
    current_data: Dict,
    headers: Dict,
    dry_run: bool = False
) -> bool:
    """네이버 채널상품의 카테고리를 업데이트합니다."""
    if dry_run:
        print(f"  [DRY-RUN] 카테고리를 {new_category_id}로 변경할 예정")
        return True

    # 현재 데이터를 복사하고 카테고리만 변경
    update_payload = current_data.copy()

    # originProduct.leafCategoryId를 새 카테고리로 변경
    if 'originProduct' in update_payload:
        update_payload['originProduct']['leafCategoryId'] = str(new_category_id)
    else:
        print(f"  ⚠️  originProduct 정보가 없습니다")
        return False

    # statusType: OUTOFSTOCK은 PUT에서 거부되므로 SALE로 정규화
    if update_payload.get('originProduct', {}).get('statusType') == 'OUTOFSTOCK':
        update_payload['originProduct']['statusType'] = 'SALE'

    # PUT 요청
    url = f"https://api.commerce.naver.com/external/v2/products/channel-products/{channel_product_no}"

    try:
        response = requests.put(url, json=update_payload, headers=headers, timeout=30)
        if response.status_code == 200:
            print(f"  ✅ 카테고리 업데이트 성공")
            return True
        else:
            print(f"  ❌ 업데이트 실패: {response.status_code}")
            print(f"     응답: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"  ❌ 업데이트 에러: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='네이버 스마트스토어 상품의 카테고리를 더 적합한 카테고리로 업데이트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--dry-run', action='store_true', help='실제로 업데이트하지 않고 미리보기만')
    parser.add_argument('--limit', type=int, help='처리할 상품 수 제한 (테스트용)')
    parser.add_argument('--channel-product-no', help='특정 채널상품번호만 업데이트')

    args = parser.parse_args()

    if args.dry_run:
        print("🔍 DRY-RUN 모드: 실제로 업데이트하지 않습니다\n")

    # 네이버 API 토큰 발급
    try:
        token = get_bearer_token(CLIENT_ID, CLIENT_SECRET)
        headers = {"Authorization": f"Bearer {token}"}
    except Exception as e:
        print(f"❌ 토큰 발급 실패: {e}")
        print("\n💡 네이버 커머스API 센터에서 현재 IP를 허용 목록에 추가하세요:")
        print("   https://sell.smartstore.naver.com/#/api/application")
        return 1

    # NocoDB에서 네이버 등록 상품 목록 조회
    from config import NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID
    from nocodb_client import NocoDBTable

    table = NocoDBTable(
        base_url=NOCODB_URL,
        api_token=NOCODB_API_TOKEN,
        table_id=NOCODB_TABLE_ID
    )

    products = table.all()
    naver_products = [p for p in products if p.get('fields', {}).get('Naver_Product_No')]

    print(f"📦 네이버 등록 상품 수: {len(naver_products)}\n")

    # 특정 상품만 업데이트하는 경우
    if args.channel_product_no:
        naver_products = [p for p in naver_products
                         if str(p.get('fields', {}).get('Naver_Product_No')) == args.channel_product_no]
        if not naver_products:
            print(f"❌ 채널상품번호 {args.channel_product_no}를 찾을 수 없습니다")
            return 1

    # 카테고리 변경이 필요한 상품 필터링
    products_to_update = []

    for p in naver_products:
        fields = p.get('fields', {})
        product_name = fields.get('SKU', '')
        category = fields.get('Category', '')
        naver_no = fields.get('Naver_Product_No')

        category_info = get_product_category_type(product_name, category)
        if category_info:
            cat_type, new_cat_id, new_cat_name = category_info
            products_to_update.append({
                'naver_no': naver_no,
                'product_name': product_name,
                'category': category,
                'category_type': cat_type,
                'new_category_id': new_cat_id,
                'new_category_name': new_cat_name
            })

    if not products_to_update:
        print("✅ 카테고리 변경이 필요한 상품이 없습니다")
        return 0

    print(f"🔄 카테고리 변경 대상: {len(products_to_update)}개\n")

    # limit 적용
    if args.limit:
        products_to_update = products_to_update[:args.limit]
        print(f"⚠️  limit={args.limit} 적용: {len(products_to_update)}개만 처리\n")

    # 카테고리별 통계
    from collections import Counter
    category_stats = Counter(p['category_type'] for p in products_to_update)
    print("카테고리별 변경 대상:")
    for cat_type, count in category_stats.items():
        cat_name = CATEGORY_MAPPING[cat_type]['category_name']
        print(f"  - {cat_type}: {count}개 → {cat_name}")
    print()

    # 업데이트 실행
    success_count = 0
    fail_count = 0

    for idx, product in enumerate(products_to_update, 1):
        naver_no = product['naver_no']
        product_name = product['product_name']
        new_cat_id = product['new_category_id']
        new_cat_name = product['new_category_name']

        print(f"[{idx}/{len(products_to_update)}] {product_name}")
        print(f"  채널상품번호: {naver_no}")
        print(f"  새 카테고리: {new_cat_name} ({new_cat_id})")

        # 현재 상품 정보 조회
        current_data = get_channel_product(naver_no, headers)
        if not current_data:
            print(f"  ❌ 상품 조회 실패\n")
            fail_count += 1
            continue

        # 현재 카테고리 확인
        current_cat_id = current_data.get('originProduct', {}).get('leafCategoryId')

        # 카테고리 이름 조회 (v2 API는 wholeCategoryName을 제공하지 않으므로 ID만 표시)
        print(f"  현재 카테고리 ID: {current_cat_id}")

        # 이미 올바른 카테고리인 경우 스킵
        if current_cat_id and str(current_cat_id) == str(new_cat_id):
            print(f"  ⏭️  이미 올바른 카테고리입니다\n")
            success_count += 1
            continue

        # 카테고리 업데이트
        if update_channel_product_category(naver_no, new_cat_id, current_data, headers, args.dry_run):
            success_count += 1
        else:
            fail_count += 1

        print()

    # 결과 요약
    print("\n" + "="*60)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"📊 전체: {len(products_to_update)}개")

    if args.dry_run:
        print("\n🔍 DRY-RUN 모드였습니다. 실제로 변경하려면 --dry-run 없이 실행하세요")

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
