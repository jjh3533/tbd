"""Shopify 기반 브랜드 공통 크롤러.

Shopify 스토어는 모든 상품 페이지에 대해 `{product_url}.json` 형태의 공개
JSON 엔드포인트를 기본 제공한다 (인증 불필요, 스토어프론트 기본 기능). 브랜드
마다 새로 파서를 만들 필요 없이, Shopify 기반 신규 브랜드가 추가돼도 이 함수
하나로 그대로 커버된다 (GL.inet이 첫 사례).
"""
from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from official_scrapers.base import ProductData
from sync_engine import _scrapedo_get


def _product_json_url(url: str) -> str:
  """쿼리 파라미터를 제거하고 .json 엔드포인트 URL 생성.

  예: https://gl-inet.com/products/gl-be10000?_pos=1&_fid=...
   → https://gl-inet.com/products/gl-be10000.json

  상품 목록/검색 결과에서 복사한 URL은 `/en-us/products/...`처럼 로케일
  프리픽스가 붙어 있는 경우가 있는데, Shopify의 .json 엔드포인트는 로케일
  프리픽스가 붙으면 404를 낸다 (`/products/...` 경로에만 존재). 그래서 경로
  전체를 쓰지 않고 `/products/` 이후 핸들만 뽑아 정규 경로로 재조립한다.
  """
  parsed = urlparse(url)
  path = parsed.path.rstrip("/")
  if "/products/" in path:
    handle = path.split("/products/", 1)[1]
    path = f"/products/{handle}"
  return f"{parsed.scheme}://{parsed.netloc}{path}.json"


def _guess_model_number(title: str) -> str:
  """"Slate 7 Pro (GL-BE10000) Tri-band..." 처럼 괄호 안에 모델명이 오는
  흔한 컨벤션에 대한 최선 추정치. 못 찾으면 빈 문자열 - 대시보드에서 사람이
  직접 채우면 됨."""
  if "(" in title and ")" in title:
    return title.split("(", 1)[1].split(")", 1)[0].strip()
  return ""


def fetch_shopify_product(url: str) -> ProductData:
  json_url = _product_json_url(url)
  res = _scrapedo_get(json_url)
  if res is None:
    raise RuntimeError(f"Shopify 상품 정보를 가져오지 못했습니다: {url}")

  product = res.json()["product"]

  variants = product.get("variants") or []
  price_usd = float(variants[0]["price"]) if variants and variants[0].get("price") else 0.0

  image_urls = [img["src"] for img in (product.get("images") or []) if img.get("src")]

  description = BeautifulSoup(
      product.get("body_html") or "", "html.parser"
  ).get_text("\n", strip=True)

  title = product.get("title", "")
  return ProductData(
      title=title,
      price_usd=price_usd,
      model_number=_guess_model_number(title),
      description=description,
      image_urls=image_urls,
  )
