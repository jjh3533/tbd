"""브랜드 공홈에서 신규 상품 정보(이미지/가격/설명)를 가져오는 크롤러 레지스트리.

브랜드별 실제 파싱 로직은 shopify.py(Shopify 기반 브랜드 공통)/unifi.py(UniFi
전용)에 있고, 여기서는 브랜드 이름 -> 크롤러 함수 매핑만 담당한다. 새 브랜드가
추가되면 _BRAND_SCRAPERS에 한 줄만 추가하면 된다 (Shopify 기반이면
fetch_shopify_product를 그대로 재사용 가능).
"""
from __future__ import annotations

from official_scrapers.base import ProductData
from official_scrapers.shopify import fetch_shopify_product
from official_scrapers.unifi import fetch_unifi_product

_BRAND_SCRAPERS = {
    "UniFi": fetch_unifi_product,
    "GL.inet": fetch_shopify_product,
}


def fetch_product(brand: str, url: str) -> ProductData:
  scraper = _BRAND_SCRAPERS.get(brand)
  if scraper is None:
    raise ValueError(f"지원하지 않는 브랜드입니다: {brand}")
  return scraper(url)


def supported_brands() -> list[str]:
  return list(_BRAND_SCRAPERS.keys())
