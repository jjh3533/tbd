"""리테일러(아마존/B&H/Adorama)에서 모델명으로 신규 상품 후보를 찾는 검색 모듈.

아마존은 Scrape.do 전용 검색 플러그인(/plugin/amazon/search)이 있어 정확한
결과를 받지만, B&H/Adorama는 그런 플러그인이 없어서 사이트 자체 검색결과
페이지를 sync_engine._scrapedo_get()으로 받아 HTML에서 상품 링크+제목을
파싱한다. 사이트 개편/차단으로 파싱이 깨지면 후보 0개를 반환하고, 호출부
(대시보드)에서 "확인 필요 - 직접 검색"으로 취급한다 (sync_engine의
fetch_bh_info 등이 실패를 check_needed로 처리하는 것과 동일한 철학).

search_amazon_candidates.py의 기존 아마존 검색 로직(search_candidates)이
search_amazon()으로 이 모듈에 이관됐다 - 그 파일은 하위호환을 위해 이 모듈을
import해서 그대로 쓴다.
"""
from __future__ import annotations

import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

import config
import sync_engine as se

AMAZON_SEARCH_URL = "https://api.scrape.do/plugin/amazon/search"
MAX_CANDIDATES_PER_PRODUCT = 2


def _title_for_matching(title: str) -> str:
  """하이픈은 그대로 두고(모델명 내부 구분자), 그 외 괄호/파이프 등 구두점은
  전부 공백으로 바꿉니다. "모델명 뒤에 설명 문구가 오는 경우"(공백으로 끊김)
  와 "모델명이 사실 더 긴 다른 모델명의 접두어일 뿐인 경우"(하이픈으로 계속
  이어짐, 예: U5G가 U5G-Max-Outdoor 안에 있는 경우)를 구분하기 위함."""
  return re.sub(r"[^a-z0-9-]", " ", (title or "").lower())


def is_model_match(model_number: str, title: str) -> bool:
  model_n = (model_number or "").lower().strip()
  if not model_n:
    return False
  title_n = _title_for_matching(title)
  pattern = r"(?<![a-z0-9-])" + re.escape(model_n) + r"(?![a-z0-9-])"
  return re.search(pattern, title_n) is not None


def search_amazon(query: str, model_number: str):
  """Scrape.do의 Amazon Search 플러그인으로 검색 후, 제목에 모델명이 정확히
  들어있는 후보만 position 순으로 최대 MAX_CANDIDATES_PER_PRODUCT개 반환.

  반환: (matches, error) - 성공하면 (list, None), 실패하면 (None, 에러메시지)"""
  with se._AMAZON_SEMAPHORE:
    resp = requests.get(
        AMAZON_SEARCH_URL,
        params={"token": config.SCRAPEDO_TOKEN, "keyword": query, "geocode": "us"},
        timeout=60,
    )
  if resp.status_code != 200:
    return None, f"HTTP {resp.status_code}"

  try:
    data = resp.json()
  except ValueError:
    return None, "JSON 파싱 실패"

  matches = []
  for p in data.get("products", []):
    title = p.get("title", "")
    if is_model_match(model_number, title):
      matches.append({
          "id": p.get("asin", ""),
          "title": title,
          "price": (p.get("price") or {}).get("amount"),
          "url": p.get("url", ""),
          "position": p.get("position", 999),
      })
  matches.sort(key=lambda m: m["position"])
  return matches[:MAX_CANDIDATES_PER_PRODUCT], None


def _title_from_slug(slug: str) -> str:
  return re.sub(r"[-_]+", " ", slug).strip().title()


def _slug_match(model_number: str, slug: str) -> bool:
  """검색결과 페이지의 상품 카드는 이미지만 감싼 빈 <a>인 경우가 많아, 제목
  대신 URL 슬러그(예: "ubiquiti-networks-unifi-u6-pro-...")로 매칭한다.
  슬러그는 하이픈/언더스코어를 "단어 사이 띄어쓰기" 자리로 쓰기 때문에,
  모델명(U6-Pro)의 하이픈도 실제로는 "U6 Pro"라는 띄어쓰기인 경우가
  대부분이다. 그래서 여기서는 하이픈을 (일반 사이트 제목을 비교하는
  is_model_match와 달리) 단어 안쪽 구분자로 보지 않고 전부 공백으로 바꾼
  뒤 비교한다."""
  normalized_model = re.sub(r"[-_]", " ", model_number)
  normalized_slug = re.sub(r"[-_]", " ", slug)
  return is_model_match(normalized_model, normalized_slug)


def _matches_from_links(soup: BeautifulSoup, href_pattern: str, id_group: int,
                         slug_group: int, model_number: str, base_url: str):
  matches = []
  seen_ids = set()
  for a in soup.find_all("a", href=True):
    href = a["href"]
    m = re.search(href_pattern, href, re.IGNORECASE)
    if not m:
      continue
    product_id = m.group(id_group)
    if product_id in seen_ids:
      continue
    slug = m.group(slug_group)
    if not _slug_match(model_number, slug):
      continue
    seen_ids.add(product_id)
    matches.append({
        "id": product_id,
        "title": _title_from_slug(slug),
        "price": None,
        "url": href if href.startswith("http") else f"{base_url}{href}",
    })
    if len(matches) >= MAX_CANDIDATES_PER_PRODUCT:
      break
  return matches


def search_bh(query: str, model_number: str):
  """B&H 검색결과 페이지(캡차/차단이 잦아 force_super로 통과)를 파싱해 상품
  링크(/c/product/{id}/{slug}.html)에서 id+슬러그를 뽑고, 슬러그에 모델명이
  들어있는 후보만 반환.

  반환: (matches, error)"""
  search_url = f"https://www.bhphotovideo.com/c/search?Ntt={quote(query)}"
  res = se._scrapedo_get(search_url, force_super=True, max_retries=2)
  if res is None:
    return None, "request_failed"

  soup = BeautifulSoup(res.text, "html.parser")
  matches = _matches_from_links(
      soup, r"/c/product/([^/]+)/([a-z0-9_]+)\.html", 1, 2, model_number,
      "https://www.bhphotovideo.com",
  )
  return matches, None


def search_adorama(query: str, model_number: str):
  """Adorama 검색결과 페이지를 파싱해 상품 링크(/{slug}/p/{id})에서
  슬러그+id를 뽑고, 슬러그에 모델명이 들어있는 후보만 반환. 여기서 얻는
  id는 기존 fetch_adorama_info()가 기대하는 ADORAMA_ID(=adorama.com/{id}.html)
  형식과 동일하다.

  반환: (matches, error)"""
  search_url = f"https://www.adorama.com/l/?searchinfo={quote(query)}"
  res = se._scrapedo_get(search_url, fast_free_tier=True)
  if res is None:
    return None, "request_failed"

  soup = BeautifulSoup(res.text, "html.parser")
  matches = _matches_from_links(
      soup, r"/([a-z0-9-]+)/p/([a-z0-9]+)(?:[/?]|$)", 2, 1, model_number,
      "https://www.adorama.com",
  )
  return matches, None
