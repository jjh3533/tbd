#!/usr/bin/env python3
"""
네이버 스마트스토어 상품명을 검색 최적화된 키워드와 함께 업데이트합니다.

상품명 형식: "영문명 / 한글명 주요키워드1 키워드2 키워드3"
예: "UniFi U7 Pro Max / 유니파이 U7 프로 맥스 와이파이7 메시 공유기"

사용법:
  python3 update_product_names_with_keywords.py --dry-run              # 미리보기
  python3 update_product_names_with_keywords.py --limit 1              # 1개만 테스트
  python3 update_product_names_with_keywords.py                        # 전체 실행
  python3 update_product_names_with_keywords.py --category WiFi        # WiFi 카테고리만
"""

import argparse
import sys
import time
from typing import Dict, List

from auth import get_bearer_token
from naver_config import CLIENT_ID, CLIENT_SECRET
from config import NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID
from nocodb_client import NocoDBTable
import requests


# 카테고리별 검색 키워드 매핑
CATEGORY_KEYWORDS = {
    'WiFi': {
        'common': ['와이파이', '무선AP', '기업용', '안정적인', 'PoE'],
        'use_cases': ['와이파이 끊김 해결', '메시 네트워크', '대규모 네트워크', '호텔 와이파이', '사무실 와이파이'],
        'tech_keywords': {
            'WiFi 7': ['와이파이7', 'Wi-Fi7', '최신'],
            'WiFi 6E': ['와이파이6E', 'Wi-Fi6E', '6GHz'],
            'WiFi 6': ['와이파이6', 'Wi-Fi6'],
            'WiFi 5': ['와이파이5', 'Wi-Fi5'],
            'Mesh': ['메시', '로밍'],
            'Outdoor': ['옥외', '실외', '방수'],
            'In-Wall': ['매립형', '벽면'],
            'Pro': ['프로', '고성능'],
        }
    },
    'Switching': {
        'common': ['스위치', '스위칭허브', '네트워크스위치', '기업용', 'PoE'],
        'use_cases': ['네트워크 확장', 'PoE 급전', 'CCTV 연결', 'IP전화'],
        'tech_keywords': {
            'PoE': ['PoE', '전원공급', '급전'],
            '10G': ['10기가', '10Gbps', '고속'],
            '2.5G': ['2.5기가', '2.5Gbps'],
            'Flex': ['플렉스', '소형'],
            'Pro': ['프로', '고성능'],
            'Enterprise': ['엔터프라이즈', '기업'],
        }
    },
    'Physical Security': {
        'common': ['CCTV', 'IP카메라', '보안카메라', '감시카메라', 'NVR'],
        'use_cases': ['실시간 모니터링', '야간촬영', '원격 감시', '스마트 홈'],
        'tech_keywords': {
            'AI': ['AI', '인공지능', '스마트감지'],
            'PTZ': ['PTZ', '팬틸트줌', '회전'],
            '360': ['360도', '전방위'],
            '4K': ['4K', '고화질'],
            'Sensor': ['센서', '감지'],
            'NVR': ['NVR', '녹화기'],
        }
    },
    'Door Access': {
        'common': ['출입통제', '스마트도어', '출입관리', '보안시스템'],
        'use_cases': ['사무실 출입', '무인 출입', '스마트 오피스', '건물 보안'],
        'tech_keywords': {
            'Reader': ['리더기', '카드리더'],
            'Access': ['출입통제', '액세스'],
            'Intercom': ['인터콤', '인터폰', '화상통화'],
            'Door': ['도어', '출입문'],
            'Gate': ['게이트', '차량출입'],
            'Lock': ['도어락', '잠금'],
        }
    },
    'Integrations': {
        'common': ['네트워크장비', '통합솔루션', '기업용'],
        'use_cases': ['IoT 네트워크 구축', '원격 관리', '통합 관리'],
        'tech_keywords': {
            'NAS': ['NAS', '스토리지', '네트워크저장장치', '백업'],
            'Router': ['라우터', '공유기', 'LTE', '5G', '이동통신'],
            '5G': ['5G', 'LTE', '이동통신', '무선'],
            'Mobile': ['모바일', '이동형', '휴대용'],
        }
    },
    'Cloud Gateways': {
        'common': ['게이트웨이', '공유기', '라우터', '통합컨트롤러'],
        'use_cases': ['안정적인 공유기', '통합 네트워크 관리', '중앙 제어'],
        'tech_keywords': {
            'Gateway': ['게이트웨이', '통합'],
            'Dream': ['드림', '올인원'],
            'Cloud': ['클라우드', '원격관리'],
        }
    },
}


def generate_keywords_for_product(product_name_en: str, category: str) -> List[str]:
    """상품명과 카테고리를 기반으로 최적 키워드 생성"""
    if category not in CATEGORY_KEYWORDS:
        return []

    cat_data = CATEGORY_KEYWORDS[category]
    keywords = []

    # 공통 키워드에서 1-2개
    keywords.extend(cat_data['common'][:2])

    # 기술 키워드 매칭 (상품명에 해당 키워드가 있으면 추가)
    for tech_key, tech_keywords in cat_data.get('tech_keywords', {}).items():
        if tech_key.lower() in product_name_en.lower():
            keywords.extend(tech_keywords[:2])
            if len(keywords) >= 8:  # 최대 8개
                break

    # 유즈케이스 키워드 1-2개 추가
    use_cases = cat_data.get('use_cases', [])
    remaining = min(10 - len(keywords), 2)
    keywords.extend(use_cases[:remaining])

    return keywords[:10]  # 최대 10개


def build_optimized_product_name(name_en: str, name_kr: str, keywords: List[str]) -> str:
    """검색 최적화된 상품명 생성"""
    # 기본 형식: "영문명 / 한글명 키워드들"
    if name_kr:
        base = f"{name_en} / {name_kr}"
    else:
        base = name_en

    # 키워드 추가 (스페이스로 구분)
    if keywords:
        keyword_str = ' '.join(keywords)
        return f"{base} {keyword_str}"

    return base


def update_product_name(
    channel_product_no: str,
    new_name: str,
    current_data: Dict,
    headers: Dict,
    dry_run: bool = False
) -> bool:
    """네이버 채널상품의 상품명을 업데이트합니다."""
    if dry_run:
        print(f"  [DRY-RUN] 상품명을 변경할 예정")
        return True

    # 현재 데이터를 복사하고 상품명만 변경
    update_payload = current_data.copy()

    if 'originProduct' in update_payload:
        update_payload['originProduct']['name'] = new_name
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
            print(f"  ✅ 상품명 업데이트 성공")
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
        description='네이버 스마트스토어 상품명을 검색 최적화된 키워드와 함께 업데이트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--dry-run', action='store_true', help='실제로 업데이트하지 않고 미리보기만')
    parser.add_argument('--limit', type=int, help='처리할 상품 수 제한 (테스트용)')
    parser.add_argument('--category', help='특정 카테고리만 업데이트 (예: WiFi, Switching)')
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

    # 카테고리 필터링
    if args.category:
        naver_products = [p for p in naver_products
                         if p.get('fields', {}).get('Category') == args.category]
        print(f"🔍 카테고리 필터: {args.category} ({len(naver_products)}개)\n")

    # 상품명 업데이트 대상 준비
    products_to_update = []

    for p in naver_products:
        fields = p.get('fields', {})
        product_name_en = fields.get('SKU', '')
        category = fields.get('Category', '')
        naver_no = fields.get('Naver_Product_No')

        # 키워드 생성
        keywords = generate_keywords_for_product(product_name_en, category)

        if keywords:  # 키워드가 있는 경우만 업데이트
            products_to_update.append({
                'naver_no': naver_no,
                'product_name_en': product_name_en,
                'category': category,
                'keywords': keywords
            })

    if not products_to_update:
        print("✅ 업데이트할 상품이 없습니다")
        return 0

    print(f"🔄 상품명 업데이트 대상: {len(products_to_update)}개\n")

    # limit 적용
    if args.limit:
        products_to_update = products_to_update[:args.limit]
        print(f"⚠️  limit={args.limit} 적용: {len(products_to_update)}개만 처리\n")

    # 카테고리별 통계
    from collections import Counter
    category_stats = Counter(p['category'] for p in products_to_update)
    print("카테고리별 업데이트 대상:")
    for cat, count in category_stats.items():
        print(f"  - {cat}: {count}개")
    print()

    # 업데이트 실행
    success_count = 0
    fail_count = 0

    for idx, product in enumerate(products_to_update, 1):
        naver_no = product['naver_no']
        product_name_en = product['product_name_en']
        category = product['category']
        keywords = product['keywords']

        print(f"[{idx}/{len(products_to_update)}] {product_name_en}")
        print(f"  채널상품번호: {naver_no}")
        print(f"  카테고리: {category}")
        print(f"  추가 키워드: {', '.join(keywords)}")

        # 현재 상품 정보 조회
        url = f"https://api.commerce.naver.com/external/v2/products/channel-products/{naver_no}"
        try:
            response = requests.get(url, headers=headers, timeout=10)

            # API 요청 제한을 피하기 위한 딜레이
            time.sleep(0.5)

            if response.status_code != 200:
                print(f"  ❌ 상품 조회 실패: {response.status_code}\n")
                fail_count += 1
                continue

            current_data = response.json()
            current_name = current_data.get('originProduct', {}).get('name', '')
            print(f"  현재 상품명: {current_name}")

            # 한글명 추출 (현재 상품명에서)
            name_kr = ''
            if ' / ' in current_name:
                parts = current_name.split(' / ', 1)
                if len(parts) > 1:
                    # 기존 키워드가 있으면 제거하고 한글명만 추출
                    kr_part = parts[1].strip()
                    # 첫 3-5 단어만 한글명으로 추출 (나머지는 기존 키워드로 간주)
                    kr_words = kr_part.split()
                    # 유니파이/UniFi로 시작하는 경우 최대 5단어, 아니면 3단어
                    max_words = 5 if kr_words and ('유니파이' in kr_words[0] or 'UniFi' in kr_words[0]) else 3
                    name_kr = ' '.join(kr_words[:max_words])

            # 새 상품명 생성
            new_name = build_optimized_product_name(product_name_en, name_kr, keywords)
            print(f"  새 상품명: {new_name}")

            # 이미 동일한 상품명인 경우 스킵
            if current_name == new_name:
                print(f"  ⏭️  이미 최적화된 상품명입니다\n")
                success_count += 1
                continue

            # 상품명 업데이트
            if update_product_name(naver_no, new_name, current_data, headers, args.dry_run):
                success_count += 1
            else:
                fail_count += 1

        except Exception as e:
            print(f"  ❌ 에러: {e}\n")
            fail_count += 1
            continue

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
