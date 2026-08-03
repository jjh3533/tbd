"""
상품 카테고리와 이름을 기반으로 검색 최적화 키워드를 생성합니다.
"""

from typing import List, Tuple


# 카테고리별 네이버 leafCategoryId 매핑
CATEGORY_TO_LEAF_ID = {
    'WiFi': '50001623',          # 네트워크장비 > AP
    'Switching': '50001506',     # 네트워크장비 > 스위칭허브
    'Physical Security': '50002707',  # TV/영상가전 > CCTV
    'Door Access': '50001623',   # 네트워크장비 > AP (KC 인증 문제로 디지털도어록 사용 불가)
    'Integrations': {
        'NAS': '50001602',       # 저장장치 > NAS
        'Router': '50001622',    # 네트워크장비 > 라우터
        'default': '50001623',   # 네트워크장비 > AP
    },
    'Cloud Gateways': '50003150',  # 네트워크장비 > 유무선공유기
    'Mobile Router': '50001622',  # 네트워크장비 > 라우터 (GL.inet 등)
    'Router': '50001622',        # 네트워크장비 > 라우터 (일반)
}


# 카테고리별 검색 키워드
CATEGORY_KEYWORDS = {
    'Mobile Router': {
        'common': ['라우터', '공유기', '모바일라우터', '무선인터넷'],
        'use_cases': ['이동형 라우터', '차량용 와이파이', '캠핑 인터넷', '임시 네트워크'],
        'tech_keywords': {
            '5G': ['5G', 'LTE', '이동통신'],
            'WiFi 6': ['와이파이6', 'Wi-Fi6'],
            'WiFi 7': ['와이파이7', 'Wi-Fi7'],
            'Dual Band': ['듀얼밴드', '2.4GHz', '5GHz'],
            'Portable': ['휴대용', '이동형'],
        }
    },
    'Router': {
        'common': ['라우터', '공유기', '네트워크장비', '기업용'],
        'use_cases': ['안정적인 공유기', '원격 관리', '네트워크 확장'],
        'tech_keywords': {
            '5G': ['5G', 'LTE', '이동통신'],
            'WiFi 6': ['와이파이6', 'Wi-Fi6'],
            'WiFi 7': ['와이파이7', 'Wi-Fi7'],
            'VPN': ['VPN', '보안'],
        }
    },
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


def get_leaf_category_id(product_name_en: str, category: str) -> str:
    """
    상품명과 카테고리를 기반으로 적합한 네이버 leafCategoryId를 반환합니다.

    Args:
        product_name_en: 영문 상품명
        category: 카테고리명 (WiFi, Switching, Physical Security 등)

    Returns:
        네이버 leafCategoryId (문자열)
    """
    if category not in CATEGORY_TO_LEAF_ID:
        print(f"[경고] '{category}'는 매핑되지 않은 카테고리입니다. 기본값(네트워크장비 > AP)을 사용합니다.")
        return '50001623'  # 기본값: 네트워크장비 > AP

    mapping = CATEGORY_TO_LEAF_ID[category]

    # Integrations는 상품명에 따라 다른 카테고리
    if isinstance(mapping, dict):
        product_lower = product_name_en.lower()

        if 'nas' in product_lower or 'unas' in product_lower:
            return mapping['NAS']
        elif any(kw in product_lower for kw in ['router', '5g', 'lte', 'mobile']):
            return mapping['Router']
        else:
            return mapping['default']

    return mapping


def generate_search_keywords(product_name_en: str, category: str) -> List[str]:
    """
    상품명과 카테고리를 기반으로 검색 최적화 키워드를 생성합니다.

    Args:
        product_name_en: 영문 상품명
        category: 카테고리명

    Returns:
        키워드 리스트 (최대 10개)
    """
    if category not in CATEGORY_KEYWORDS:
        # 알 수 없는 카테고리는 기본 키워드 반환
        return ['네트워크장비', '기업용', '원격관리']

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


def build_optimized_product_name(name_en: str, name_kr: str, category: str) -> str:
    """
    검색 최적화된 상품명을 생성합니다.

    Args:
        name_en: 영문 상품명
        name_kr: 한글 상품명
        category: 카테고리명

    Returns:
        최적화된 상품명 (형식: "영문명 / 한글명 키워드1 키워드2...")
    """
    # 기본 형식: "영문명 / 한글명"
    if name_kr:
        base = f"{name_en} / {name_kr}"
    else:
        base = name_en

    # 키워드 생성
    keywords = generate_search_keywords(name_en, category)

    # 키워드 추가 (스페이스로 구분)
    if keywords:
        keyword_str = ' '.join(keywords)
        return f"{base} {keyword_str}"

    return base


def infer_category_from_name(product_name_en: str) -> str:
    """
    상품명으로부터 카테고리를 추론합니다.

    Args:
        product_name_en: 영문 상품명

    Returns:
        카테고리명 (WiFi, Switching, Physical Security 등)
    """
    name_lower = product_name_en.lower()

    # WiFi 제품
    if any(kw in name_lower for kw in ['u6', 'u7', 'ac pro', 'wifi', 'access point', 'ap']):
        if 'switch' not in name_lower:  # "AP Switch"가 아닌 경우만
            return 'WiFi'

    # Switching 제품
    if 'switch' in name_lower:
        return 'Switching'

    # Physical Security 제품
    if any(kw in name_lower for kw in ['camera', 'nvr', 'sensor', 'g3', 'g4', 'g5', 'g6']):
        return 'Physical Security'

    # Door Access 제품
    if any(kw in name_lower for kw in ['reader', 'access', 'door', 'gate', 'intercom', 'lock']):
        return 'Door Access'

    # Cloud Gateways
    if any(kw in name_lower for kw in ['gateway', 'dream', 'cloudkey', 'express']):
        return 'Cloud Gateways'

    # Integrations (NAS, Router 등)
    if any(kw in name_lower for kw in ['nas', 'unas', 'router', '5g', 'lte', 'mobile', 'audio']):
        return 'Integrations'

    # 기본값
    return 'WiFi'
