"""UniFi(store.ui.com) 상품 페이지 크롤러.

store.ui.com은 Next.js로 만들어져 있어 페이지 HTML에 `__NEXT_DATA__`
스크립트 태그로 그 페이지에 쓰인 props가 그대로 JSON으로 박혀있다. 별도
API 없이 이 블록만 파싱하면 title/가격/이미지/스펙을 구조화된 형태로 얻을
수 있다.

주의: __NEXT_DATA__ 안에서 실제 상품 데이터가 있는 경로가 페이지 종류에
따라 조금씩 다를 수 있다(단일상품 페이지 vs 컬렉션 내 상품 목록). 아래
_find_product()가 몇 가지 가능한 경로를 순서대로 시도한다 - 신규 상품 URL로
크롤링했을 때 결과가 비어있으면 이 함수부터 확인할 것.

실제 U6 Pro 상품으로 확인된 구조 (2026-08):
  - minDisplayPrice = {"amount": 15900, "currency": "USD"} - amount는 센트 단위
  - gallery = {"items": [{"data": {"url": ..., "mimeType": "image/png"}}, ...]}
    (mp4 항목도 섞여있어 mimeType으로 이미지만 골라내야 함)
  - technicalSpecification = {"sections": [{"features": [{"value": ..., "feature": {"label": ...}}]}]}
    (값 없는 비교표용 플래그 항목도 섞여있어 value가 있는 것만 사용)
"""
from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from official_scrapers.base import ProductData
from sync_engine import _scrapedo_get

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)


def _find_product(next_data: dict) -> dict | None:
  page_props = (next_data.get("props") or {}).get("pageProps") or {}

  product = page_props.get("product")
  if product:
    return product

  products = ((page_props.get("collection") or {}).get("products")) or []
  if not products:
    return None

  current_id = page_props.get("currentProductId")
  if current_id:
    for p in products:
      if p.get("id") == current_id:
        return p

  return products[0]


def _extract_images(product: dict) -> list[str]:
  images: list[str] = []
  gallery = product.get("gallery") or {}
  items = gallery.get("items") if isinstance(gallery, dict) else gallery
  for item in items or []:
    data = (item or {}).get("data") or {}
    mime = data.get("mimeType", "")
    if mime and not mime.startswith("image/"):
      continue  # mp4 등 이미지가 아닌 자산 제외
    src = data.get("url")
    if src:
      images.append(src)

  if not images and product.get("thumbnail"):
    thumb = product["thumbnail"]
    src = thumb.get("url") if isinstance(thumb, dict) else thumb
    if src:
      images.append(src)
  return images


def _extract_price(product: dict) -> float:
  price = product.get("minDisplayPrice") or product.get("minDisplayRegularPrice")
  if isinstance(price, dict):
    amount = price.get("amount")
    return float(amount) / 100 if amount else 0.0
  try:
    return float(re.sub(r"[^\d.]", "", str(price))) if price else 0.0
  except ValueError:
    return 0.0


def _flatten_tech_spec(spec) -> str:
  """{"sections": [{"features": [{"value": ..., "feature": {"label": ...}}]}]}
  형태를 "Label: value" 줄 목록으로 펼친다. value가 없는 항목(비교표용 플래그)은
  건너뛴다."""
  if not isinstance(spec, dict):
    return ""
  lines = []
  for section in spec.get("sections") or []:
    for feat in section.get("features") or []:
      value = feat.get("value")
      if not value:
        continue
      label = ((feat.get("feature") or {}).get("label")) or ""
      lines.append(f"{label}: {value}" if label else str(value))
  return "\n".join(lines)


def _html_to_text(html: str) -> str:
  return BeautifulSoup(html or "", "html.parser").get_text("\n", strip=True)


def fetch_unifi_product(url: str) -> ProductData:
  res = _scrapedo_get(url)
  if res is None:
    raise RuntimeError(f"UniFi 상품 페이지를 가져오지 못했습니다: {url}")

  match = _NEXT_DATA_RE.search(res.text)
  if not match:
    raise RuntimeError(f"__NEXT_DATA__를 찾을 수 없습니다: {url}")

  next_data = json.loads(match.group(1))
  product = _find_product(next_data)
  if product is None:
    raise RuntimeError(f"상품 데이터를 찾을 수 없습니다: {url}")

  description = "\n\n".join(
      p for p in (
          _html_to_text(product.get("description")),
          product.get("shortDescription") or "",
          _html_to_text(product.get("keyFeatures")),
          _flatten_tech_spec(product.get("technicalSpecification")),
      ) if p
  )

  return ProductData(
      title=product.get("title") or product.get("name") or "",
      price_usd=_extract_price(product),
      model_number=product.get("displaySku") or "",
      description=description,
      image_urls=_extract_images(product),
  )
