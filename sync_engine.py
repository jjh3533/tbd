"""가격/재고 스크래핑, NocoDB 동기화, 상품 테이블 렌더링 등 UI 프레임워크에
독립적인 백엔드 로직. 원래 app.py(Streamlit) 안에 인라인으로 있던 걸 그대로
옮긴 것으로, 로직은 한 줄도 바꾸지 않았다 (Streamlit 전용 호출(st.error,
st.cache_data)만 콜백/일반 캐시로 치환).

app.py(Streamlit)와 dashboard/(NiceGUI)가 동일하게 import해서 쓴다 - 스크래핑/
동기화 로직을 두 곳에 중복시키지 않기 위함.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from functools import lru_cache
from html import escape as html_escape
import json
import re
import threading
import time
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from bs4 import BeautifulSoup
from nocodb_client import NocoDBTable
import pytz
import requests
import yfinance as yf

from config import (
    NOCODB_URL,
    NOCODB_API_TOKEN,
    NOCODB_TABLE_ID,
    NOCODB_HISTORY_TABLE_ID,
    SCRAPEDO_TOKEN,
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
)

table = NocoDBTable(NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID)
# 가격/재고 변동 이력(EAV 스타일) 테이블. NOCODB_HISTORY_TABLE_ID가 설정 안
# 돼 있으면(마이그레이션 전 로컬 환경 등) None으로 두고, _log_change가 그냥
# 건너뜁니다 - 메인 동기화 기능은 이 테이블 없이도 항상 동작해야 합니다.
history_table = (
    NocoDBTable(NOCODB_URL, NOCODB_API_TOKEN, NOCODB_HISTORY_TABLE_ID)
    if NOCODB_HISTORY_TABLE_ID else None
)

# UniFi Store 카테고리 (What's New 제외, NocoDB Category 필드와 동일)
CATEGORIES = [
    "Cloud Gateways",
    "Switching",
    "WiFi",
    "Physical Security",
    "Door Access",
    "Integrations",
]

# ==========================================
# 🎨 UniFi Site Manager 벤치마크 컬러 토큰
# (unifi.ui.com의 실제 렌더링된 computed style에서 직접 추출)
# ==========================================
THEMES = {
    "light": {
        "bg": "#FFFFFF",
        "bg_secondary": "#F4F5F6",
        "surface": "#FFFFFF",
        "surface_tint": "rgba(33, 35, 39, 0.04)",
        "surface_tint_strong": "rgba(33, 35, 39, 0.08)",
        "border": "rgba(33, 35, 39, 0.10)",
        "text": "#212327",
        "text_secondary": "#71757F",
        "accent": "#006FFF",
        "accent_soft_bg": "#E8F1FF",
        "success": "#1A9E4F",
        "success_soft_bg": "#E4F7EC",
        "danger": "#E5484D",
        "danger_soft_bg": "#FDEBEC",
        "warning": "#B25E09",
        "warning_soft_bg": "#FBF0E1",
        "shadow": "0 1px 2px rgba(33, 35, 39, 0.06)",
    },
    "dark": {
        "bg": "#0D0D0D",
        "bg_secondary": "#282B2F",
        "surface": "#17191C",
        "surface_tint": "rgba(249, 250, 250, 0.04)",
        "surface_tint_strong": "rgba(249, 250, 250, 0.08)",
        "border": "rgba(249, 250, 250, 0.10)",
        "text": "#F9FAFA",
        "text_secondary": "#DEE0E3",
        "accent": "#4797FF",
        "accent_soft_bg": "#05254D",
        "success": "#30D158",
        "success_soft_bg": "#0F2E1B",
        "danger": "#FF6259",
        "danger_soft_bg": "#3A1414",
        "warning": "#F0A83C",
        "warning_soft_bg": "#3A2B0F",
        "shadow": "0 1px 2px rgba(0, 0, 0, 0.4)",
    },
}


# ==========================================
# 백엔드 핵심 함수 (기존 스크래핑/알림 로직 그대로 유지)
# ==========================================
def get_current_exchange_rate():
  try:
    ticker = yf.Ticker("KRW=X")
    todays_data = ticker.history(period="1d")
    base_rate = todays_data["Close"].iloc[-1]
    return round(base_rate + 10, 1)
  except Exception:
    return 1380.0


def send_telegram_msg(text: str, on_error=print):
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": text,
      "parse_mode": "Markdown",
      "disable_web_page_preview": True,
  }
  try:
    requests.post(url, json=payload, timeout=5)
  except Exception as e:
    on_error(f"텔레그램 발송 실패: {e}")


_SCRAPEDO_USAGE_CACHE = {"data": None, "at": 0.0}
_SCRAPEDO_USAGE_TTL = 60


def get_scrapedo_usage():
  """Scrape.do 계정의 남은 크레딧 현황을 조회합니다 (분당 호출 제한이 있어 60초 캐싱)."""
  now = time.monotonic()
  if now - _SCRAPEDO_USAGE_CACHE["at"] < _SCRAPEDO_USAGE_TTL:
    return _SCRAPEDO_USAGE_CACHE["data"]
  try:
    res = requests.get(
        "https://api.scrape.do/info",
        params={"token": SCRAPEDO_TOKEN},
        timeout=10,
    )
    if res.status_code == 200:
      _SCRAPEDO_USAGE_CACHE["data"] = res.json()
      _SCRAPEDO_USAGE_CACHE["at"] = now
      return _SCRAPEDO_USAGE_CACHE["data"]
  except Exception:
    pass
  return None


# Amazon PDP 플러그인 엔드포인트는 토큰당 동시 요청 1개 제한이 있어 세마포어로 직렬화.
_AMAZON_SEMAPHORE = threading.Semaphore(1)

# Scrape.do 대시보드(dashboard.scrape.do)에서 확인한 실제 계정 동시 요청 한도는
# Hobby 플랜 기준 10. Amazon이 항상 1개를 쓰므로 Adorama/B&H 합산 한도를
# 5로 잡아 (5 + 1 = 6) 계정 한도(10)에 여유를 넉넉히 남깁니다. 예전에 9까지
# 밀어붙였다가 Adorama가 대량 502(약 57초 지연 후 실패)를 뱉은 적이 있어서,
# 이번엔 계정 한도에 딱 맞추기보다 여유를 두는 쪽을 택했습니다.
_SCRAPEDO_SEMAPHORE = threading.Semaphore(5)


def _scrapedo_get(target_url, timeout=60, max_retries=1, retry_delay=2.0,
                   try_super_on_failure=True, force_super=False,
                   fast_free_tier=False):
  """Scrape.do 요청 공용 래퍼 (재시도 + 비용 절감 escalation 포함).

  fast_free_tier=True: 무료 티어(super=false)에서 타임아웃/재시도 횟수를
  줄여서 "어차피 막힐 요청"에 오래 매달리지 않고 super 티어로 더 빨리
  넘어가게 합니다. super를 상시로 켜는 것과 달리, 무료 티어에서 성공하는
  건(=차단 안 걸리는 상품) 여전히 정상가로 처리되니 크레딧은 그대로 아낍니다.
  Adorama처럼 무료 티어가 자주/오래 막혀서 502로 시간을 잡아먹는 곳에 사용.
  """
  if force_super:
    tiers = [(True, timeout, max_retries, 15000)]
  else:
    if fast_free_tier:
      free_tier = (False, min(timeout, 10), 0, 5000)
    else:
      free_tier = (False, timeout, max_retries, 15000)
    super_tier = (True, timeout, max_retries, 15000)
    tiers = [free_tier, super_tier] if try_super_on_failure else [free_tier]

  for use_super, tier_timeout, tier_retries, retry_timeout_ms in tiers:
    for attempt in range(tier_retries + 1):
      try:
        with _SCRAPEDO_SEMAPHORE:
          res = requests.get(
              "https://api.scrape.do/",
              params={
                  "token": SCRAPEDO_TOKEN,
                  "url": target_url,
                  "geoCode": "us",
                  "super": "true" if use_super else "false",
                  # 무료 티어는 "빨리 확인하고 다음 티어로 넘어가는" 게
                  # 목적이라 scrape.do 자체 내부 재시도 주기도 짧게 잡음.
                  "retryTimeout": retry_timeout_ms,
              },
              timeout=tier_timeout,
          )
        if res.status_code == 200:
          return res
      except Exception:
        pass
      if attempt < tier_retries:
        time.sleep(retry_delay)
  return None


# 사이트가 요청을 거부/차단했을 때 나타나는 흔한 문구. 200 응답이어도 실제
# 내용이 아니라 이런 인터스티셜/캡차 페이지일 수 있어서, 이걸 감지하면
# "품절"이 아니라 "확인 필요"로 분류합니다.
_BLOCK_KEYWORDS = [
    "pardon our interruption",
    "access denied",
    "are you a robot",
    "unusual traffic",
    "px-captcha",
    "distil_r_captcha",
    "request unsuccessful",
    "reference #",
    "verify you are a human",
    "attention required",
    "checking your browser",
]

_OOS_KEYWORDS = [
    "out of stock",
    "discontinued",
    "sold out",
    "coming soon",
    "notify when available",
    "special order",
    "backordered",
    "pre-order",
    "preorder",
    "no longer available",
]


def fetch_adorama_info(adorama_id):
  if not adorama_id:
    return None

  clean_id = str(adorama_id).strip().lower()
  target_url = f"https://www.adorama.com/{clean_id}.html"

  try:
    # Adorama는 무료 티어가 자주/오래 막혀서(502, ~57초) super로 넘어가는
    # 시간이 병목이었음. super를 상시로 켜는 대신, 무료 티어에서 빨리
    # 포기하고(20초/1회) super로 넘어가도록 fast_free_tier만 켬.
    res = _scrapedo_get(target_url, fast_free_tier=True)
    if res is None:
      # 재시도까지 다 실패 - 진짜 품절인지 사이트가 막았는지 알 수 없으니
      # 0으로 확정 짓지 않고 "확인 필요"로만 표시합니다.
      return {"price": 0.0, "in_stock": False, "status": "check_needed",
              "detail": "request_failed"}

    soup = BeautifulSoup(res.text, "html.parser")
    adorama_usd = 0.0
    in_stock = True
    confirmed_oos = False

    page_text_lower = soup.get_text(" ", strip=True).lower()
    blocked = any(kw in page_text_lower for kw in _BLOCK_KEYWORDS)

    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
      try:
        data = json.loads(script.string)
        if isinstance(data, list):
          data = data[0]
        offers = data.get("offers", {})
        if isinstance(offers, list):
          offers = offers[0]

        price = offers.get("price") or offers.get("lowPrice")
        if price:
          adorama_usd = float(price)
          availability = str(offers.get("availability", "")).lower()
          if "outofstock" in availability:
            in_stock = False
            confirmed_oos = True
          break
      except Exception:
        pass

    if adorama_usd == 0.0:
      price_selectors = [
          ".your-price",
          '[itemprop="price"]',
          ".price",
          "span.value",
      ]
      for sel in price_selectors:
        elems = soup.select(sel)
        for elem in elems:
          clean_p = re.sub(r"[^\d.]", "", elem.get_text().strip())
          if clean_p:
            try:
              val = float(clean_p)
              if 5.0 <= val <= 10000.0:
                adorama_usd = val
                break
            except ValueError:
              pass
        if adorama_usd > 0:
          break

    if any(kw in page_text_lower for kw in _OOS_KEYWORDS):
      in_stock = False
      confirmed_oos = True

    if blocked:
      status, detail = "check_needed", "blocked"
    elif confirmed_oos:
      status, detail = "oos", ""
    elif adorama_usd > 0:
      status, detail = "ok", ""
    else:
      # 가격도 못 찾고, 차단 문구도 품절 문구도 없음 - 페이지 구조가 바뀌었을
      # 수 있으니 이것도 확정하지 않고 확인 필요로 남겨둡니다.
      status, detail = "check_needed", "no_price_found"

    return {"price": adorama_usd, "in_stock": in_stock, "status": status,
            "detail": detail}
  except Exception:
    return {"price": 0.0, "in_stock": False, "status": "check_needed",
            "detail": "exception"}


def fetch_amazon_info(asin, timeout=60, max_retries=2, retry_delay=2.0):
  """Scrape.do의 Amazon PDP 플러그인(요청당 1크레딧, 토큰당 동시 1개 제한)으로 조회."""
  if not asin:
    return None

  clean_asin = str(asin).strip().upper()

  for attempt in range(max_retries + 1):
    try:
      with _AMAZON_SEMAPHORE:
        res = requests.get(
            "https://api.scrape.do/plugin/amazon/pdp",
            params={
                "token": SCRAPEDO_TOKEN,
                "asin": clean_asin,
                "geocode": "US",
            },
            timeout=timeout,
        )
      if res.status_code == 200:
        data = res.json()
        if data.get("status") == "success":
          price = data.get("price")
          amazon_usd = float(price) if price is not None else 0.0
          # 플러그인이 정상적으로 페이지를 읽어서 "success"를 준 경우라 가격이
          # 0이어도(=페이지에 가격이 없음) 이건 확정된 정보로 취급합니다.
          status = "ok" if amazon_usd > 0 else "oos"
          return {"price": amazon_usd, "in_stock": amazon_usd > 0,
                  "status": status, "detail": ""}
        # 플러그인 자체가 이 ASIN을 못 읽었다는 뜻 - 품절 확정이 아니라
        # 재조회가 필요한 상태.
        return {"price": 0.0, "in_stock": False, "status": "check_needed",
                "detail": "plugin_failed"}
    except Exception:
      pass
    if attempt < max_retries:
      time.sleep(retry_delay)
  return {"price": 0.0, "in_stock": False, "status": "check_needed",
          "detail": "request_failed"}


_WEIGHT_UNIT_TO_KG = {
    "kg": 1.0,
    "g": 0.001,
    "lb": 0.453592,
    "lbs": 0.453592,
    "oz": 0.0283495,
}


_PACKAGE_CORRECTION_KG = 0.3  # General > Weight(제품 자체 무게)에 더해 패키지 무게를 추정

# "Weight" 단독 라벨(General 섹션의 제품 자체 무게)과 "Package Weight" 라벨을
# 구분해서 찾음. 둘 다 같은 helper(_extract_bh_weight_kg)로 파싱.
_GENERAL_WEIGHT_LABEL_RE = re.compile(r"^\s*weight\s*$", re.IGNORECASE)
_PACKAGE_WEIGHT_LABEL_RE = re.compile(r"package\s*weight", re.IGNORECASE)
_WEIGHT_VALUE_RE = re.compile(r"([\d.]+)\s*(kg|lbs|lb|oz|g)\b", re.IGNORECASE)


def _extract_bh_weight_kg(soup, label_pattern):
  """B&H Specs 표에서 라벨(label_pattern)에 해당하는 무게 값을 kg로 추출."""
  for row in soup.find_all("tr"):
    cells = row.find_all(["td", "th"])
    if len(cells) < 2:
      continue
    if label_pattern.search(cells[0].get_text(strip=True)):
      match = _WEIGHT_VALUE_RE.search(cells[1].get_text(strip=True))
      if match:
        value, unit = float(match.group(1)), match.group(2).lower()
        return round(value * _WEIGHT_UNIT_TO_KG.get(unit, 1.0), 3)

  for dt in soup.find_all("dt"):
    if label_pattern.search(dt.get_text(strip=True)):
      dd = dt.find_next_sibling("dd")
      if dd:
        match = _WEIGHT_VALUE_RE.search(dd.get_text(strip=True))
        if match:
          value, unit = float(match.group(1)), match.group(2).lower()
          return round(value * _WEIGHT_UNIT_TO_KG.get(unit, 1.0), 3)

  return None


def _parse_bh_package_weight_kg(soup):
  """B&H Specs에서 배송 패키지 무게를 kg로 추출.

  우선순위:
  1) 'Packaging Info > Package Weight' - 있으면 이게 실제 패키지 무게 그
     자체라 가장 정확함. 1순위로 사용(보정값 더하지 않음).
  2) 위에서 못 찾았을 때만 General 섹션의 'Weight'(제품 자체 무게, 박스
     미포함)를 대신 사용. 실제 배송 패키지는 이보다 무거우니 보정값
     (_PACKAGE_CORRECTION_KG=0.3kg)을 더해 추정치로 씀.
  """
  package_weight = _extract_bh_weight_kg(soup, _PACKAGE_WEIGHT_LABEL_RE)
  if package_weight is not None:
    return package_weight

  general_weight = _extract_bh_weight_kg(soup, _GENERAL_WEIGHT_LABEL_RE)
  if general_weight is not None:
    return round(general_weight + _PACKAGE_CORRECTION_KG, 3)

  return None


def fetch_bh_info(bh_id):
  if not bh_id:
    return None

  clean_id = str(bh_id).strip().upper()
  target_url = f"https://www.bhphotovideo.com/c/product/{clean_id}/"

  try:
    # B&H는 다른 곳보다 캡차/차단에 자주 걸리는 편이라 재시도를 한 번 더 줍니다.
    res = _scrapedo_get(target_url, force_super=True, max_retries=2)
    if res is None:
      return {"price": 0.0, "in_stock": False, "weight_kg": None,
              "status": "check_needed", "detail": "request_failed"}

    soup = BeautifulSoup(res.text, "html.parser")
    bh_usd = 0.0
    in_stock = True
    confirmed_oos = False

    page_text_lower = soup.get_text(" ", strip=True).lower()
    blocked = any(kw in page_text_lower for kw in _BLOCK_KEYWORDS)

    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
      try:
        data = json.loads(script.string)
        if isinstance(data, list):
          data = data[0]
        offers = data.get("offers", {})
        if isinstance(offers, list):
          offers = offers[0]

        price = offers.get("price") or offers.get("lowPrice")
        if price:
          bh_usd = float(price)
          availability = str(offers.get("availability", "")).lower()
          if "outofstock" in availability or "discontinued" in availability:
            in_stock = False
            confirmed_oos = True
          break
      except Exception:
        pass

    if bh_usd == 0.0:
      price_selectors = [
          '[itemprop="price"]',
          '[data-selenium="pricingPrice"]',
          ".price",
          "span.value",
      ]
      for sel in price_selectors:
        elems = soup.select(sel)
        for elem in elems:
          clean_p = re.sub(r"[^\d.]", "", elem.get_text().strip())
          if clean_p:
            try:
              val = float(clean_p)
              if 5.0 <= val <= 10000.0:
                bh_usd = val
                break
            except ValueError:
              pass
        if bh_usd > 0:
          break

    if any(kw in page_text_lower for kw in _OOS_KEYWORDS):
      in_stock = False
      confirmed_oos = True

    weight_kg = _parse_bh_package_weight_kg(soup)

    if blocked:
      status, detail = "check_needed", "blocked"
    elif confirmed_oos:
      status, detail = "oos", ""
    elif bh_usd > 0:
      status, detail = "ok", ""
    else:
      status, detail = "check_needed", "no_price_found"

    return {"price": bh_usd, "in_stock": in_stock, "weight_kg": weight_kg,
            "status": status, "detail": detail}
  except Exception:
    return {"price": 0.0, "in_stock": False, "weight_kg": None,
            "status": "check_needed", "detail": "exception"}


RETAILER_NAMES = ("Adorama", "Amazon", "B&H")
_RETAILER_PRICE_FIELD = {"Adorama": "Adorama_USD", "Amazon": "Amazon_USD", "B&H": "BH_USD"}
# 사이트별로 "그 사이트 자체에 재고가 있는지"를 따로 저장하는 체크박스 필드.
# 예전엔 가격(>0)으로 재고 여부를 추측했는데, 품절이어도 마지막 확인된 가격이
# 남아있는 경우가 있어서(사이트가 세일가를 보여준 채 품절 표시) 개별
# 리테일러만 Sync할 때 다른 두 곳 상태를 잘못 추측하는 원인이었음. 이제
# fetch_*_info()가 실제로 판단한 in_stock을 이 필드에 그대로 저장해두고,
# 재조회 안 하는 라운드에는 가격 대신 이 필드를 그대로 읽어옵니다.
_RETAILER_STOCK_FIELD = {
    "Adorama": "Adorama_In_Stock", "Amazon": "Amazon_In_Stock", "B&H": "BH_In_Stock",
}


def _log_change(sku, naver_id, field_name, old_value, new_value):
  """Price_History에 변화 1건을 기록합니다. history_table이 없거나(마이그레이션
  전) API 호출이 실패해도, 기존 table.update() 실패 무시 패턴과 동일하게
  메인 동기화를 절대 막지 않습니다."""
  if history_table is None:
    return
  try:
    history_table.create({
        "SKU": sku,
        "Naver_Product_No": str(naver_id) if naver_id else "",
        "Field_Name": field_name,
        "Old_Value": "" if old_value is None else str(old_value),
        "New_Value": "" if new_value is None else str(new_value),
        "Changed_At": datetime.now(timezone.utc).isoformat(),
    })
  except Exception:
    pass


def _stale_retailer_data(name, product_id, fields):
  """이번 라운드에 다시 조회하지 않는 리테일러의 데이터를, NocoDB에 마지막으로
  저장된 값(가격 + 사이트별 재고 체크박스)으로 흉내냅니다. 개별 리테일러만
  Sync할 때도 전체 재고/확인필요 판단(In_Stock, Needs_Check)은 계속 3곳 기준
  으로 일관되게 나오게 하기 위함 - 단, 이 리테일러의 필드들은 이번에 새로
  쓰지 않습니다(밑에서 처리)."""
  if not product_id:
    return None
  price = fields.get(_RETAILER_PRICE_FIELD[name], 0.0) or 0.0
  stock = bool(fields.get(_RETAILER_STOCK_FIELD[name], False))
  check_note = fields.get("Check_Note") or ""
  if f"{name} 확인 필요" in check_note:
    return {"price": price, "in_stock": stock, "status": "check_needed",
            "detail": "stale"}
  return {"price": price, "in_stock": stock, "status": "ok" if stock else "oos",
          "detail": ""}


def process_single_record(r, current_rate, retailers=RETAILER_NAMES, generation=None):
  """워커 스레드에서 실행되므로 UI 프레임워크 호출 없이 로그 문자열만 만들어
  반환합니다.

  retailers: 이번 라운드에 실제로 재조회할 리테일러 이름 집합/튜플
  ("Adorama", "Amazon", "B&H" 중 일부 또는 전체). 나머지는 NocoDB에 저장된
  마지막 값을 그대로 사용합니다(개별 Sync 버튼용).

  generation: 지정하면, NocoDB에 쓰기 직전에 자기 세대가 여전히 최신인지
  확인합니다(run_sync_guarded._bump_sync_generation 참고) - 취소된 이전
  Sync의 워커가 뒤늦게 끝나 새로 시작된 Sync의 결과를 덮어쓰는 걸 막기 위함."""
  record_id = r["id"]
  fields = r["fields"]
  sku = fields.get("SKU", "무명 상품")

  adorama_id = fields.get("ADORAMA_ID")
  asin = fields.get("ASIN")
  bh_id = fields.get("BH_ID")

  msrp_usd = fields.get("MSRP_USD", 0.0)
  prev_stock = fields.get("In_Stock", False)
  prev_needs_check = fields.get("Needs_Check", False)
  naver_id = fields.get("Naver_Product_No", "-")
  max_threshold = msrp_usd if msrp_usd > 0 else 99999.0

  # 이번에 실제로 재조회할 곳만 스레드로 동시에 요청. 실제 네트워크 동시
  # 요청 개수는 _AMAZON_SEMAPHORE(1)와 _SCRAPEDO_SEMAPHORE(5)가 계정 한도
  # (Hobby 플랜 10) 안에서 제한하므로, 안전합니다.
  fresh_results = {}
  with ThreadPoolExecutor(max_workers=max(len(retailers), 1)) as retailer_executor:
    futures = {}
    if "Adorama" in retailers:
      futures["Adorama"] = retailer_executor.submit(fetch_adorama_info, adorama_id)
    if "Amazon" in retailers:
      futures["Amazon"] = retailer_executor.submit(fetch_amazon_info, asin)
    if "B&H" in retailers:
      futures["B&H"] = retailer_executor.submit(fetch_bh_info, bh_id)
    for name, future in futures.items():
      fresh_results[name] = future.result()

  adorama_data = (
      fresh_results["Adorama"] if "Adorama" in retailers
      else _stale_retailer_data("Adorama", adorama_id, fields)
  )
  amazon_data = (
      fresh_results["Amazon"] if "Amazon" in retailers
      else _stale_retailer_data("Amazon", asin, fields)
  )
  bh_data = (
      fresh_results["B&H"] if "B&H" in retailers
      else _stale_retailer_data("B&H", bh_id, fields)
  )

  adorama_price = adorama_data["price"] if adorama_data else 0.0
  amazon_price = amazon_data["price"] if amazon_data else 0.0
  bh_price = bh_data["price"] if bh_data else 0.0

  valid_retailers = []
  if (
      adorama_data
      and adorama_data.get("status") == "ok"
      and 0 < adorama_price <= max_threshold
  ):
    valid_retailers.append("Adorama")
  if (
      amazon_data
      and amazon_data.get("status") == "ok"
      and 0 < amazon_price <= max_threshold
  ):
    valid_retailers.append("Amazon")
  if (
      bh_data
      and bh_data.get("status") == "ok"
      and 0 < bh_price <= max_threshold
  ):
    valid_retailers.append("B&H")

  # ID가 설정된 곳(=data가 None이 아님) 중 이번에 "확인 필요"로 끝난 곳들.
  # 하나라도 있으면 이번 결과만으로 재고 상태를 확정할 수 없다는 뜻입니다.
  check_needed_sources = [
      name for name, data in (
          ("Adorama", adorama_data), ("Amazon", amazon_data), ("B&H", bh_data)
      )
      if data and data.get("status") == "check_needed"
  ]
  any_check_needed = bool(check_needed_sources)

  if valid_retailers:
    curr_stock = True
  elif not any_check_needed:
    # 시도한 곳들이 전부 확정적인 답(정상가 또는 품절/사이트 자체 신고)을
    # 줬는데 유효한 판매처가 없다면, 진짜 품절/MSRP 초과로 확정합니다.
    curr_stock = False
  else:
    # 일부는 사이트가 막았거나 파싱에 실패해서 확답을 못 받은 상태 - 이전
    # 재고 상태를 그대로 유지하고 "품절"이 아니라 "확인 필요"로만 표시합니다.
    curr_stock = prev_stock

  # B&H 패키지 무게 - 배송비(Shipping_KRW) 계산의 입력값이라, 못 찾았을 때
  # 방치하면(공란/음수 임시값 등) 배송비 계산식이 이상한 값을 뱉습니다.
  # 유효한(양수) 무게가 이미 있으면 건드리지 않고, 없을 때만 1.0kg 기본값을
  # 채워 넣습니다. 크롤링 실패 자체는 매 라운드 Check_Note에 남겨서 눈에
  # 보이게 합니다(값을 덮어쓰든 안 쓰든, "이건 추정치일 수 있다"는 신호).
  bh_weight_kg = (
      bh_data.get("weight_kg") if (bh_data and "B&H" in retailers) else None
  )
  prev_check_note = fields.get("Check_Note") or ""
  weight_note_was_active = "Weight_KG 크롤링 실패" in prev_check_note
  weight_fallback_applied = False
  if bh_weight_kg is not None:
    # 이번에 실제로 찾음 - 예전 실패 메모는 자연히 사라짐(check_note_parts에서 제외)
    weight_update = {"Weight_KG": bh_weight_kg}
  else:
    weight_update = {}
    if "B&H" in retailers and bh_data is not None:
      # 이번 라운드에 B&H를 다시 시도했지만 여전히 못 찾음
      weight_fallback_applied = True
      existing_weight = fields.get("Weight_KG")
      if not existing_weight or existing_weight <= 0:
        weight_update["Weight_KG"] = 1.0
    elif weight_note_was_active:
      # 이번 라운드엔 B&H를 건드리지 않았지만, 예전에 크롤링 실패로 기본값을
      # 쓰고 있었다는 사실 자체는 여전히 유효하니 메모를 계속 유지
      weight_fallback_applied = True

  check_note_parts = [f"{name} 확인 필요" for name in check_needed_sources]
  if weight_fallback_applied:
    check_note_parts.append("Weight_KG 크롤링 실패 - 기본값 1.0kg 사용 중")

  update_data = {
      "In_Stock": curr_stock,
      "Needs_Check": any_check_needed,
      "Check_Note": ", ".join(check_note_parts),
      "Exchange_Rate": current_rate,
      **weight_update,
  }
  # 사이트가 막혀서 확정 못 한 가격은 이전 값을 0으로 덮어쓰지 않고 그대로
  # 둡니다 (마지막으로 확인된 값이 남아있는 게, 잘못된 $0보다 낫습니다).
  # 이번 라운드에 실제로 재조회하지 않은 리테일러의 가격 필드는 건드리지
  # 않습니다(개별 Sync 버튼 - 다른 두 곳 값은 그대로 유지).
  # 가격과 함께, 그 사이트 자체의 재고 여부(_RETAILER_STOCK_FIELD)도 이번에
  # 실제로 재조회한 리테일러만 갱신합니다. 이게 있어야 다음번에 이 리테일러를
  # 건너뛸 때(_stale_retailer_data) 가격>0 추측이 아니라 진짜 마지막 재고
  # 상태를 정확히 읽어올 수 있습니다.
  if "Adorama" in retailers and (
      adorama_data is None or adorama_data.get("status") != "check_needed"
  ):
    update_data["Adorama_USD"] = adorama_price
    update_data["Adorama_In_Stock"] = bool(adorama_data and adorama_data.get("in_stock"))
  if "Amazon" in retailers and (
      amazon_data is None or amazon_data.get("status") != "check_needed"
  ):
    update_data["Amazon_USD"] = amazon_price
    update_data["Amazon_In_Stock"] = bool(amazon_data and amazon_data.get("in_stock"))
  if "B&H" in retailers and (
      bh_data is None or bh_data.get("status") != "check_needed"
  ):
    update_data["BH_USD"] = bh_price
    update_data["BH_In_Stock"] = bool(bh_data and bh_data.get("in_stock"))

  # 취소된 이전 Sync 세대의 워커가 뒤늦게 여기 도달한 경우 - 그 사이 새 Sync가
  # 시작되어 이미 최신 데이터를 쓰고 있으므로, 오래된 결과로 덮어쓰지 않고
  # 조용히 건너뜁니다(에러 아님 - ok=True로 반환).
  if generation is not None and not _is_current_sync_generation(generation):
    return f"⏭️ [{sku}] 이전 Sync가 취소된 뒤 뒤늦게 끝나 건너뜀 (최신 Sync가 이미 진행 중)", None, True

  # 본 테이블(Products) 갱신을 Price_History 기록보다 먼저 시도합니다.
  # 갱신이 실패하면 Price_History도 기록하지 않습니다 - 두 테이블 상태가
  # 서로 어긋나는 걸(이력엔 남았는데 실제 상품 데이터는 안 바뀜) 막기 위함.
  update_error = None
  try:
    table.update(record_id, update_data)
  except Exception as e:
    update_error = e

  # 실제로 값이 바뀐 것만 Price_History에 영구 기록 (추가 크롤링 없이, 이번
  # 라운드에 이미 조회한 값을 버리지 않고 쌓는 것이 목적). 재조회 안 한
  # 리테일러의 가격은 update_data에 아예 안 들어있으므로 자동으로 제외됨.
  if update_error is None:
    if curr_stock != prev_stock:
      _log_change(sku, naver_id, "In_Stock", prev_stock, curr_stock)
    for _name, _field in _RETAILER_PRICE_FIELD.items():
      if _field not in update_data:
        continue
      _old_price = fields.get(_field, 0.0) or 0.0
      _new_price = update_data[_field]
      if _old_price != _new_price:
        _log_change(sku, naver_id, _field, _old_price, _new_price)

  def _fmt(label, name, data, price):
    if data and data.get("status") == "check_needed":
      return f"{label}:⚠({data.get('detail') or 'check'})"
    suffix = "" if name in retailers else "(cached)"
    return f"{label}:${price}{suffix}"

  if update_error is not None:
    log_line = f"❌ [{sku}] NocoDB 갱신 실패: {update_error}"
  else:
    log_line = (
        f"✅ [{sku}] Complete | {_fmt('Ado', 'Adorama', adorama_data, adorama_price)} /"
        f" {_fmt('Amz', 'Amazon', amazon_data, amazon_price)} /"
        f" {_fmt('BH', 'B&H', bh_data, bh_price)}"
    )

  # NocoDB 갱신이 실패했으면 curr_stock/any_check_needed 등은 실제로 저장되지
  # 않은 값이므로, 상태 변화 알림(재입고/품절/확인필요 텔레그램)은 보내지 않음
  # - 안 그러면 "반영 안 된 변화"를 이미 반영된 것처럼 알리게 됨.
  status_change = None
  if update_error is None:
    if any_check_needed and not prev_needs_check:
      status_change = (
          "CHECK",
          f"⚠️ **[확인 필요]** *{sku}*\n• {', '.join(check_needed_sources)} 접속/파싱"
          f" 실패 - 사이트를 직접 확인해주세요",
      )
    elif prev_stock != curr_stock:
      if not curr_stock:
        status_change = (
            "OOS",
            f"🔴 **[OUT OF STOCK - Above MSRP]** *{sku}*\n• SmartStore"
            f" ID({naver_id}) Action Required",
        )
      else:
        updated_record = table.get(record_id)
        new_sell_price = updated_record["fields"].get("sale_price", 0)
        available_sources = ", ".join(valid_retailers)
        status_change = (
            "IN_STOCK",
            f"🟢 **[BACK IN STOCK]** *{sku}*\n• Valid Retailers:"
            f" **{available_sources}**\n• Target Price (MSRP Based):"
            f" **`{new_sell_price:,}원`**",
        )

  return log_line, status_change, update_error is None


def run_tbd_tracker(log_container, retailers=RETAILER_NAMES, only_needs_check=False, cancel_event=None, generation=None):
  """retailers: 이번 라운드에 재조회할 리테일러 이름 집합/튜플. 기본값은 3곳
  전체(전체 Sync 버튼). 개별 Sync 버튼은 {"Adorama"} 처럼 1곳만 넘겨줍니다.
  only_needs_check=True면 Needs_Check=True인 상품만 골라 재조회합니다
  ("확인 필요만 Sync" 버튼).

  log_container: .write(msg) 메서드만 있으면 되는 아무 객체 (Streamlit
  st.empty()든, NiceGUI ui.log든 상관없음 - duck typing).

  cancel_event: threading.Event를 넘기면, 매 결과가 들어올 때마다 확인해서
  set()돼 있으면 남은 작업을 더 기다리지 않고 조기 종료합니다. 이미 실행
  중인(네트워크 요청이 나간) 항목은 끝까지 진행되지만(스레드를 강제로 죽일
  수는 없음), 아직 시작 안 한 항목은 스레드풀에서 그대로 취소됩니다.

  generation: run_sync_guarded가 발급한 이번 Sync의 세대 번호. 각 워커는
  자기 세대가 여전히 최신(_is_current_sync_generation)일 때만 NocoDB에 씁니다
  - 취소된 이전 세대의 워커가 뒤늦게 끝나 새 세대의 결과를 덮어쓰는 걸 막기
  위함."""
  retailers_label = (
      " / ".join(retailers) if len(retailers) < len(RETAILER_NAMES)
      else "Adorama / Amazon / B&H Triple-Channel"
  )
  log_container.write(f"⚡ [UI.com Engine] {retailers_label} Syncing...")
  current_rate = get_current_exchange_rate()
  log_container.write(f"💱 Applied Exchange Rate: ₩{current_rate}")

  records = table.all()
  if only_needs_check:
    records = [r for r in records if r["fields"].get("Needs_Check")]
    log_container.write(f"🔍 확인 필요 상품만 재조회 대상: {len(records)}건")
    if not records:
      log_container.write("✨ 확인 필요한 상품이 없습니다.")
      return 0

  total_count = len(records)
  log_container.write(f"📦 Active Inventory Records: {total_count}")

  out_of_stock_count = 0
  back_in_stock_count = 0
  check_needed_count = 0
  update_error_count = 0
  detail_messages = []
  updated_count = len(records)

  # 바깥쪽 풀은 그저 "동시에 대기줄에 들어갈 수 있는 상품 개수"이고, 실제
  # 네트워크 동시 요청 한도는 위 세마포어들이 지킵니다. 10개면 상품 10개가
  # 동시에 세마포어 대기줄에 들어가 충분히 파이프라인을 채웁니다.
  executor = ThreadPoolExecutor(max_workers=10)
  cancelled = False
  try:
    futures = [
        executor.submit(process_single_record, r, current_rate, retailers, generation)
        for r in records
    ]
    for future in as_completed(futures):
      if cancel_event is not None and cancel_event.is_set():
        cancelled = True
        log_container.write("⏹️ 중지 요청 - 이미 시작된 항목만 마저 반영하고 나머지는 건너뜁니다.")
        break
      log_line, res, ok = future.result()
      log_container.write(log_line)
      if not ok:
        update_error_count += 1
      if res:
        st_type, msg = res
        if st_type == "OOS":
          out_of_stock_count += 1
        elif st_type == "IN_STOCK":
          back_in_stock_count += 1
        elif st_type == "CHECK":
          check_needed_count += 1
        detail_messages.append(msg)
  finally:
    # 취소된 경우 아직 시작 안 한 항목은 그대로 취소하고(cancel_futures),
    # 이미 네트워크 요청이 나간 항목들이 끝나길 기다리지 않습니다(wait=False)
    # - 어차피 스레드를 강제로 죽일 수는 없어 백그라운드에서 알아서 끝납니다.
    executor.shutdown(wait=not cancelled, cancel_futures=cancelled)

  changed_total = out_of_stock_count + back_in_stock_count

  summary_header = [
      "📊 **[UI.com Supply Monitor] Sync Report**" + (" (중간에 중지됨)" if cancelled else ""),
      f"• **Synced Retailers**: {' / '.join(retailers)}",
      f"• **Monitored Items**: {total_count} units",
      f"• **Status Shift**: {changed_total} (🔴 Out of Stock {out_of_stock_count}"
      f" / 🟢 Normal {back_in_stock_count})",
      f"• **Needs Manual Check**: {check_needed_count} (사이트 접속/파싱 실패 - 품절"
      " 확정 아님)",
  ]
  if update_error_count:
    summary_header.append(
        f"• **⚠️ NocoDB 갱신 실패**: {update_error_count}건 - 위 항목 로그에서 ❌ 표시 확인"
        " (이 항목들은 이번 Sync에서 실제로 반영되지 않았습니다)"
    )
  summary_header.append("\n---")

  if detail_messages:
    final_msg = "\n\n".join(["\n".join(summary_header)] + detail_messages)
    final_msg += (
        "\n\n👉 [Naver Commerce Admin](https://sell.smartstore.naver.com/)"
    )
  elif update_error_count:
    # 재고/가격 변화는 없었지만 NocoDB 갱신 자체가 실패한 항목이 있으면
    # "이상 없음"으로 조용히 넘어가지 않고 알림
    final_msg = "\n".join(summary_header)
  else:
    final_msg = (
        "\n".join(summary_header)
        + "\n\n✨ All inventory & price levels optimal."
    )

  if cancelled:
    log_container.write("⏹️ Sync 중지됨")
  else:
    send_telegram_msg(final_msg)
    log_container.write("🎉 Fast Parallel Sync Complete!")
  return updated_count


def safe_fetch_records(on_error=print):
  """NocoDB 호출이 실패해도(토큰 만료/권한 부족/네트워크 오류) 대시보드 전체가
  죽지 않고, 원인을 바로 알 수 있게 에러 메시지를 보여준 뒤 빈 목록으로 계속 진행.

  on_error: 에러 힌트 문자열을 하나 받는 콜백 (Streamlit이면 st.error,
  NiceGUI면 ui.notify 등으로 바꿔 끼울 수 있음)."""
  try:
    return table.all()
  except requests.exceptions.HTTPError as e:
    status = e.response.status_code if e.response is not None else "?"
    if status == 401:
      hint = "NOCODB_API_TOKEN이 만료/무효합니다. NocoDB Account Settings > Tokens에서 새 토큰을 발급하세요."
    elif status == 403:
      hint = "토큰에 이 Base('UniFi Supply')/Products 테이블에 대한 접근 권한이 없습니다."
    elif status == 404:
      hint = "NOCODB_URL 또는 NOCODB_TABLE_ID가 올바른지 확인하세요."
    elif status == 429:
      hint = "NocoDB API 요청 한도를 초과했습니다. 잠시 후 다시 시도하세요."
    else:
      hint = "NocoDB API 호출 중 오류가 발생했습니다."
    on_error(f"⚠️ NocoDB 연결 실패 (HTTP {status}): {hint}")
    return []
  except Exception as e:
    on_error(f"⚠️ NocoDB 연결 실패: {e}")
    return []


# ==========================================
# 테이블/카드용 순수 포맷팅 함수 (Streamlit 의존성 없음)
# ==========================================
_COLOR_KEY_GOOD = "accent"    # MSRP보다 저렴
_COLOR_KEY_SAME = "success"   # MSRP와 동일
_COLOR_KEY_BAD = "danger"     # 가격정보 없음 / MSRP보다 비쌈

_PRICE_COL_TO_RETAILER = {"B&H ($)": "B&H", "Adorama ($)": "Adorama", "Amazon ($)": "Amazon"}


def _rgba_from_hex(hex_color, alpha):
  hex_color = hex_color.lstrip("#")
  r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
  return f"rgba({r}, {g}, {b}, {alpha})"


def _adorama_url(adorama_id):
  if not adorama_id:
    return None
  return f"https://www.adorama.com/{str(adorama_id).strip().lower()}.html"


def _amazon_url(asin):
  if not asin:
    return None
  return f"https://www.amazon.com/dp/{str(asin).strip().upper()}"


def _bh_url(bh_id):
  if not bh_id:
    return None
  return f"https://www.bhphotovideo.com/c/product/{str(bh_id).strip().upper()}/"


# UniFi Store(store.ui.com) 제품 URL은 카테고리 없이 슬러그만으로 접근 가능함
# (예: https://store.ui.com/us/en/products/u6-pro). 이 슬러그는 techspecs.ui.com
# 크롤링 프로젝트 때 만들어둔 product_slug_map.json의 techspecs_slug와 동일한
# 값이라(실측 확인함) 그 파일을 그대로 재사용합니다.
# NocoDB로 이전하면서 레코드 id 체계가 완전히 바뀌었으므로(Airtable recXXXX ->
# NocoDB 정수 Id), 더 이상 record id로 매칭할 수 없습니다. 대신 두 데이터
# 모두에 안정적으로 존재하는 product_slug_map.json의 "name" <-> NocoDB의
# "SKU" 필드(실제로는 제품명을 담고 있음, 예: "UniFi U6 Mesh")로 매칭합니다.
_PRODUCT_SLUG_MAP_FILE = Path(__file__).parent / "product_slug_map.json"


def _normalize_store_name(name):
  """product_slug_map.json의 "name"과 NocoDB SKU 표기가 살짝 다른 경우(슬래시
  vs 하이픈, "(10-Pack)"/"2-Pack" 같은 수량 표기 유무)를 완화해서 다시 매칭하기
  위한 정규화. SKU가 비어있는(None) 레코드가 있어도 대시보드가 죽지 않도록
  빈 문자열로 방어."""
  if not name:
    return ""
  name = name.replace("/", "-")
  name = re.sub(r"\s*\(\d+-Pack\)\s*$", "", name)
  name = re.sub(r"\s+\d+-Pack\s*$", "", name)
  return name.strip()


@lru_cache(maxsize=1)
def _load_unifi_store_slug_map():
  if not _PRODUCT_SLUG_MAP_FILE.exists():
    return {}, {}
  try:
    records = json.loads(_PRODUCT_SLUG_MAP_FILE.read_text(encoding="utf-8"))
    exact = {
        r["name"]: r["techspecs_slug"]
        for r in records if r.get("name") and r.get("techspecs_slug")
    }
    normalized = {_normalize_store_name(name): slug for name, slug in exact.items()}
    return exact, normalized
  except Exception:
    return {}, {}


def _unifi_store_url(product_name):
  exact, normalized = _load_unifi_store_slug_map()
  slug = exact.get(product_name) or normalized.get(_normalize_store_name(product_name))
  if not slug:
    return None
  return f"https://store.ui.com/us/en/products/{slug}"


def _naver_url(naver_id):
  if not naver_id or str(naver_id).strip() in ("", "-"):
    return None
  return f"https://smartstore.naver.com/tbdseoul/products/{str(naver_id).strip()}"


def fmt_usd(v):
  try:
    return f"${float(v):,.2f}"
  except (TypeError, ValueError):
    return "-"


def fmt_krw(v):
  try:
    return f"₩ {float(v):,.0f}"
  except (TypeError, ValueError):
    return "-"


def sort_records_by_category_then_name(records):
  """메인 대시보드 '전체 상품' 표 정렬: 1) 왼쪽 메뉴의 카테고리 순서,
  2) 같은 카테고리 안에서는 이름(SKU) 오름차순."""
  def _key(r):
    fields = r["fields"]
    category = fields.get("Category")
    category_rank = (
        CATEGORIES.index(category) if category in CATEGORIES else len(CATEGORIES)
    )
    name = str(fields.get("SKU") or "").lower()
    return (category_rank, name)

  return sorted(records, key=_key)


def sort_records_by_name(records):
  """카테고리별 페이지 표 정렬: 상품 이름(SKU) 오름차순."""
  return sorted(records, key=lambda r: str(r["fields"].get("SKU") or "").lower())


def exclude_clone_rows(records):
  """`Product_Page == "Clone"`인 로우(색상 옵션 클론 - 화이트 로우의 옵션일 뿐,
  독립된 네이버 상품이 아님)를 제외합니다. 대시보드의 "상품 개수/판매 가능/
  품절" 같은 카운트와 목록은 실제 등록 상품 기준이어야 하는데, 이 로우들을
  그대로 포함하면 화이트+블랙이 옵션 하나로 묶인 네이버 상품 1개가 NocoDB
  로우 2개로 잡혀 중복 카운트됩니다. 반대로 재고/가격 이력처럼 색상별 추적
  자체가 목적인 곳(`get_long_oos_products`/`get_price_history`)에서는 이
  필터를 쓰지 않고 원본 레코드를 그대로 사용해야 합니다."""
  return [r for r in records if r["fields"].get("Product_Page") != "Clone"]


def status_counts(records):
  """판매 가능 / 품절 / 확인 필요 3분류 카운트. build_products_table_html의 Status
  뱃지 우선순위(확인 필요 > 판매가능/품절)와 동일한 기준으로 집계해, 카드 숫자와
  표에 실제로 보이는 뱃지 개수가 항상 일치하게 합니다."""
  active = out_of_stock = needs_check = 0
  for r in records:
    f = r["fields"]
    if f.get("Needs_Check"):
      needs_check += 1
    elif f.get("In_Stock"):
      active += 1
    else:
      out_of_stock += 1
  return active, out_of_stock, needs_check


def _price_arrow_html(delta, t):
  """price_deltas에서 찾은 (이전값, 새값) 쌍으로 오름/내림 화살표 span을
  만듭니다. 값을 못 만들거나 변동이 없으면 빈 문자열."""
  if not delta:
    return ""
  old_v, new_v = delta
  try:
    old_f, new_f = float(old_v), float(new_v)
  except (TypeError, ValueError):
    return ""
  if new_f > old_f:
    return (
        f' <span style="color:{t["danger"]};font-size:10px;"'
        f' title="이전 ${old_f:,.2f}에서 상승">▲</span>'
    )
  if new_f < old_f:
    return (
        f' <span style="color:{t["success"]};font-size:10px;"'
        f' title="이전 ${old_f:,.2f}에서 하락">▼</span>'
    )
  return ""


def build_products_table_html(records, theme_name, show_category=True, price_deltas=None):
  """Adorama / Amazon / B&H 가격, Best Price(클릭 시 최저가 판매처로 이동),
  Sale Price/Purchase Cost/Profit까지 보여주는 Site Manager 스타일 테이블의 HTML을
  문자열로 만들어 반환합니다 (렌더링은 호출부에서: Streamlit이면
  st.markdown(html, unsafe_allow_html=True), NiceGUI면 ui.html(html)).

  price_deltas: get_latest_price_deltas()가 반환하는 {(SKU, 필드명): (이전값,
  새값)} 딕셔너리를 넘기면, B&H/Adorama/Amazon 가격 옆에 오름/내림 화살표를
  표시합니다. 넘기지 않으면(기본값) 화살표 없이 기존과 동일하게 렌더링합니다.

  records가 비어있으면 None을 반환합니다 - 호출부가 "등록된 상품이 없습니다"
  같은 안내를 프레임워크에 맞는 방식으로 보여주면 됩니다."""
  if not records:
    return None
  price_deltas = price_deltas or {}

  t = THEMES[theme_name]

  columns = ["SKU / Model"]
  if show_category:
    columns.append("Category")
  columns += [
      "Naver ID", "UniFi Store ($)", "B&H ($)", "Adorama ($)", "Amazon ($)",
      "Best Price ($)", "Status", "Sale Price", "Purchase Cost", "Profit",
  ]
  final_price_col = "Purchase Cost"

  rows_html = []
  for r in records:
    f = r["fields"]
    sku = f.get("SKU") or "-"
    category = f.get("Category") or "미분류"
    is_active = bool(f.get("In_Stock"))
    msrp = f.get("MSRP_USD", 0.0) or 0.0
    best_usd = f.get("Best_USD", 0.0) or 0.0
    bh_usd = f.get("BH_USD", 0.0) or 0.0
    adorama_usd = f.get("Adorama_USD", 0.0) or 0.0
    amazon_usd = f.get("Amazon_USD", 0.0) or 0.0

    bh_url = _bh_url(f.get("BH_ID"))
    adorama_url = _adorama_url(f.get("ADORAMA_ID"))
    amazon_url = _amazon_url(f.get("ASIN"))

    best_price_url = None
    for price, url in (
        (bh_usd, bh_url), (adorama_usd, adorama_url), (amazon_usd, amazon_url)
    ):
      if url and price > 0 and abs(price - best_usd) < 0.01:
        best_price_url = url
        break

    # 가격 정보가 아예 없는 경우(0달러)는 "비싸다(빨강)"가 아니라 "데이터
    # 없음(회색)"으로 표시 - 아래 다른 $0 셀들과 같은 규칙.
    best_is_zero = best_usd <= 0
    if not best_is_zero:
      if round(best_usd, 2) < round(msrp, 2):
        color_key = _COLOR_KEY_GOOD
      elif round(best_usd, 2) == round(msrp, 2):
        color_key = _COLOR_KEY_SAME
      else:
        color_key = _COLOR_KEY_BAD
      best_color = t[color_key]

    needs_check = bool(f.get("Needs_Check"))
    check_note = f.get("Check_Note") or ""
    # Status 뱃지는 마우스를 올리면 항상 Check_Note를 보여줍니다(재고
    # 확인이 안 됐을 때뿐 아니라, Active/Out of Stock 상태에서도 예를 들어
    # "무게 크롤링 실패로 배송비 추정치 사용 중" 같은 메모가 있으면 보이게).
    tooltip_note = check_note or (
        "사이트 접속/파싱 실패 - 직접 확인해주세요" if needs_check else ""
    )
    tooltip_attr = f' title="{html_escape(tooltip_note)}"' if tooltip_note else ""
    # Check_Note에서 "Adorama 확인 필요"처럼 이번에 확인이 안 된 개별
    # 리테일러를 뽑아냄. 그 리테일러의 가격 셀은 회색으로 표시해서, 이게
    # 이번에 새로 확인된 값이 아니라 마지막으로 확인됐던 값(stale)이라는
    # 걸 한눈에 알 수 있게 합니다.
    blocked_retailers = {
        name for name in RETAILER_NAMES if f"{name} 확인 필요" in check_note
    }
    if needs_check:
      status_html = f'<span class="uic-pill check"{tooltip_attr}>⚠ Check Needed</span>'
    elif is_active:
      status_html = f'<span class="uic-pill ok"{tooltip_attr}>Active</span>'
    else:
      status_html = f'<span class="uic-pill bad"{tooltip_attr}>Out of Stock</span>'
    cat_html = f'<span class="uic-pill cat">{html_escape(category)}</span>'

    unifi_store_url = _unifi_store_url(sku)
    naver_url = _naver_url(f.get("Naver_Product_No"))

    cell_values = {
        "SKU / Model": html_escape(sku),
        "Category": cat_html,
        "Naver ID": html_escape(str(f.get("Naver_Product_No", "-"))),
        "UniFi Store ($)": fmt_usd(msrp),
        "B&H ($)": fmt_usd(bh_usd) + _price_arrow_html(price_deltas.get((sku, "BH_USD")), t),
        "Adorama ($)": fmt_usd(adorama_usd) + _price_arrow_html(price_deltas.get((sku, "Adorama_USD")), t),
        "Amazon ($)": fmt_usd(amazon_usd) + _price_arrow_html(price_deltas.get((sku, "Amazon_USD")), t),
        "Best Price ($)": fmt_usd(best_usd),
        "Status": status_html,
        "Sale Price": fmt_krw(f.get("sale_price", 0)),
        "Purchase Cost": fmt_krw(f.get("purchase_cost", 0)),
        "Profit": fmt_krw(f.get("profit", 0)),
    }
    cell_links = {
        "Naver ID": naver_url,
        "UniFi Store ($)": unifi_store_url,
        "B&H ($)": bh_url,
        "Adorama ($)": adorama_url,
        "Amazon ($)": amazon_url,
        "Best Price ($)": best_price_url,
    }
    # $0(가격 정보 없음)인 칸을 회색으로 표시하기 위한 컬럼->실제 값 매핑.
    zero_check_values = {
        "UniFi Store ($)": msrp,
        "B&H ($)": bh_usd,
        "Adorama ($)": adorama_usd,
        "Amazon ($)": amazon_usd,
        "Best Price ($)": best_usd,
    }

    tds = []
    for col in columns:
      value = cell_values[col]
      link_url = cell_links.get(col)
      if link_url:
        value = (
            f'<a href="{html_escape(link_url)}" target="_blank"'
            f' rel="noopener noreferrer">{value}</a>'
        )

      classes = []
      style = ""
      if col == "SKU / Model":
        classes.append("uic-sku")
      if col == "Naver ID":
        classes.append("uic-divider")
      if col == final_price_col:
        classes.append("uic-final-price")
      if col == "Best Price ($)" and not best_is_zero:
        style = (
            f' style="color:{best_color};'
            f' background-color:{_rgba_from_hex(best_color, 0.14)};'
            ' font-weight:700;"'
        )
      elif col in _PRICE_COL_TO_RETAILER and _PRICE_COL_TO_RETAILER[col] in blocked_retailers:
        style = (
            f' style="color:{_rgba_from_hex(t["text_secondary"], 0.45)};" '
            f'title="확인 필요 - 마지막으로 확인된 값"'
        )
      elif col in zero_check_values and zero_check_values[col] <= 0:
        style = f' style="color:{_rgba_from_hex(t["text_secondary"], 0.6)};"'

      cls_attr = f' class="{" ".join(classes)}"' if classes else ""
      tds.append(f"<td{cls_attr}{style}>{value}</td>")
    rows_html.append("<tr>" + "".join(tds) + "</tr>")

  thead_cells = []
  for col in columns:
    classes = []
    if col == "Naver ID":
      classes.append("uic-divider")
    if col == final_price_col:
      classes.append("uic-final-price")
    cls_attr = f' class="{" ".join(classes)}"' if classes else ""
    thead_cells.append(f"<th{cls_attr}>{html_escape(col)}</th>")

  return f"""
  <div class="uic-table-wrap">
    <div class="uic-table-scroll">
      <table class="uic-table">
        <thead><tr>{''.join(thead_cells)}</tr></thead>
        <tbody>{''.join(rows_html)}</tbody>
      </table>
    </div>
  </div>
  """


def get_long_oos_products(records, min_days=15):
  """현재 In_Stock=False인 상품 중, Price_History에 기록된 In_Stock 전이
  이력을 근거로 min_days일 이상 품절 상태인 것만 골라 반환합니다.

  Price_History 도입 이전부터 이미 품절이었던 상품은 "언제 품절이 시작됐는지"
  알 방법이 없으므로(과거 이력이 없음), 별도 리스트로 분리해서 반환합니다 -
  호출부(대시보드)가 이 상품들을 "기록 이전부터 품절"로 눈에 띄게 표시할 수
  있게 하기 위함입니다.

  반환: (long_oos, unknown_since) 튜플.
  - long_oos: {"sku", "naver_id", "category", "days_oos"} 딕셔너리 리스트,
    품절일수 내림차순 정렬.
  - unknown_since: {"sku", "naver_id", "category"} 딕셔너리 리스트 (품절
    시작 시점 불명)."""
  if history_table is None:
    return [], []

  try:
    history = history_table.all()
  except Exception:
    return [], []

  # SKU별로 가장 최근에 In_Stock이 False로 바뀐 시점을 찾습니다.
  last_oos_start = {}
  for h in history:
    hf = h["fields"]
    if hf.get("Field_Name") != "In_Stock" or str(hf.get("New_Value")) != "False":
      continue
    sku = hf.get("SKU")
    changed_at = hf.get("Changed_At")
    if not sku or not changed_at:
      continue
    try:
      dt = datetime.fromisoformat(str(changed_at).replace("Z", "+00:00"))
    except ValueError:
      continue
    if dt.tzinfo is None:
      dt = pytz.UTC.localize(dt)
    if sku not in last_oos_start or dt > last_oos_start[sku]:
      last_oos_start[sku] = dt

  now = datetime.now(pytz.UTC)
  long_oos, unknown_since = [], []
  for r in records:
    f = r["fields"]
    if f.get("In_Stock"):
      continue
    sku = f.get("SKU", "무명 상품")
    entry = {
        "sku": sku,
        "naver_id": f.get("Naver_Product_No", "-"),
        "category": f.get("Category") or "미분류",
    }
    start = last_oos_start.get(sku)
    if start is None:
      unknown_since.append(entry)
      continue
    days_oos = (now - start).days
    if days_oos >= min_days:
      long_oos.append({**entry, "days_oos": days_oos})

  long_oos.sort(key=lambda e: e["days_oos"], reverse=True)
  return long_oos, unknown_since


def get_price_history(limit=50):
  """Price_History에서 Changed_At 기준 최신순으로 최근 limit건을 반환합니다
  (대시보드 '최근 변동' 피드용). Changed_At은 표시용으로 KST 문자열 변환."""
  if history_table is None:
    return []

  try:
    history = history_table.all()
  except Exception:
    return []

  history.sort(key=lambda h: h["fields"].get("Changed_At") or "", reverse=True)

  result = []
  for h in history[:limit]:
    hf = h["fields"]
    changed_at = hf.get("Changed_At")
    result.append({
        "sku": hf.get("SKU", "-"),
        "naver_id": hf.get("Naver_Product_No", "-"),
        "field_name": hf.get("Field_Name", "-"),
        "old_value": hf.get("Old_Value", "-"),
        "new_value": hf.get("New_Value", "-"),
        "changed_at_kst": (
            NocoDBTable._convert_timestamp_to_kst(changed_at) if changed_at else "-"
        ),
    })
  return result


def get_latest_price_deltas():
  """SKU + 리테일러 가격 필드(Adorama_USD/Amazon_USD/BH_USD)별로 가장 최근
  Price_History 변동 1건의 (이전값, 새값)을 반환합니다. 대시보드 표에서 가격
  옆에 오름/내림 화살표를 표시하는 데 씁니다. In_Stock 변동은 대상이 아니라
  제외합니다."""
  if history_table is None:
    return {}

  try:
    history = history_table.all()
  except Exception:
    return {}

  price_fields = set(_RETAILER_PRICE_FIELD.values())
  latest = {}
  for h in history:
    hf = h["fields"]
    sku = hf.get("SKU")
    field = hf.get("Field_Name")
    changed_at = hf.get("Changed_At") or ""
    if not sku or field not in price_fields:
      continue
    key = (sku, field)
    if key not in latest or changed_at > latest[key][0]:
      latest[key] = (changed_at, hf.get("Old_Value"), hf.get("New_Value"))

  return {key: (old, new) for key, (_, old, new) in latest.items()}


# ==========================================
# 자동 동기화 스케줄러 (매일 09:00 KST 전체 / 4시간마다 확인 필요만) +
# 수동 Sync 버튼과 공유하는 "겹쳐 돌기 방지 + 중지" 상태
# ==========================================
_KST_TZ = pytz.timezone("Asia/Seoul")
_sync_lock = threading.Lock()
_sync_cancel_event = threading.Event()
# Sync 취소 시 executor.shutdown(wait=False)로 이미 시작된 워커를 백그라운드에
# 남겨둔 채 run_sync_guarded가 곧바로 락을 반환하는데, 사용자가 그 직후 새
# Sync를 시작하면 취소된 이전 세대의 워커와 새 세대의 워커가 동시에 NocoDB를
# 쓸 수 있었음. 새 Sync가 시작될 때마다 세대를 올리고, 각 워커는 자기 세대가
# 여전히 최신일 때만 NocoDB에 씁니다 - 취소된 세대의 뒤늦은 쓰기를 막기 위함
# (스레드를 강제로 죽일 수는 없으니, 결과를 버리는 방식으로 처리).
_sync_generation_lock = threading.Lock()
_sync_generation = 0


def _bump_sync_generation() -> int:
  global _sync_generation
  with _sync_generation_lock:
    _sync_generation += 1
    return _sync_generation


def _is_current_sync_generation(generation: int) -> bool:
  with _sync_generation_lock:
    return generation == _sync_generation
# 대시보드가 폴링해서 스피너/버튼 비활성화/중지 버튼을 그리는 데 쓰는 전역
# 상태. 여러 브라우저 탭에서 봐도 항상 "지금 뭐가 도는지"가 일치해야 하므로
# (수동 버튼 여러 개를 동시에 눌러서 겹쳐 도는 사고를 겪은 뒤 도입) 클라이언트별
# 상태가 아니라 프로세스 전역 상태로 관리합니다.
_sync_status = {"running": False, "label": None}
_scheduler = None


class _HeadlessLogAdapter:
  """대시보드 UI 없이(스케줄러/cron에서) run_tbd_tracker를 돌릴 때 쓰는
  log_container 대역 - .write(msg)를 그냥 print로 흘려보내 docker-compose
  logs에서 보이게 합니다."""

  def write(self, msg) -> None:
    print(msg, flush=True)


def is_sync_running() -> bool:
  return _sync_status["running"]


def get_sync_label():
  return _sync_status["label"]


def request_sync_cancel() -> None:
  """대시보드의 "중지" 버튼이 호출. 이미 시작된 네트워크 요청은 강제로 죽일
  수 없어 끝까지 실행되지만, run_tbd_tracker의 결과 처리 루프가 이 시점
  이후로는 남은 항목을 더 기다리지 않고 조기 종료합니다."""
  _sync_cancel_event.set()


def run_sync_guarded(log_container, retailers=RETAILER_NAMES, only_needs_check=False, label=None):
  """수동 Sync 버튼과 스케줄러가 공통으로 쓰는 진입점. 겹쳐 도는 걸 막기
  위해 락을 non-blocking으로 잡고, 이미 다른 동기화(수동 버튼이든 스케줄이든)
  가 진행 중이면 이번 실행은 건너뜁니다. 실행 중에는 is_sync_running()이
  True를 반환해 대시보드가 버튼을 비활성화/스피너 표시를 할 수 있고,
  request_sync_cancel()로 중지를 요청할 수 있습니다."""
  if not _sync_lock.acquire(blocking=False):
    log_container.write("⏭️ 이미 다른 동기화가 진행 중입니다 - 끝난 뒤 다시 시도해주세요.")
    return 0

  generation = _bump_sync_generation()
  _sync_cancel_event.clear()
  _sync_status["running"] = True
  _sync_status["label"] = label or (
      " / ".join(retailers) if len(retailers) < len(RETAILER_NAMES) else "전체"
  )
  try:
    return run_tbd_tracker(
        log_container, retailers, only_needs_check=only_needs_check,
        cancel_event=_sync_cancel_event, generation=generation,
    )
  finally:
    _sync_status["running"] = False
    _sync_status["label"] = None
    _sync_cancel_event.clear()
    _sync_lock.release()


def _run_scheduled_sync(only_needs_check: bool) -> None:
  """스케줄러가 호출하는 실제 작업 - run_sync_guarded를 그대로 재사용해
  수동 버튼과 동일한 겹침 방지/상태 관리를 받습니다. 이미 다른 동기화가
  진행 중이면 이번 회차는 건너뛰고 다음 스케줄에서 자연히 다시 시도됩니다."""
  run_sync_guarded(
      _HeadlessLogAdapter(), RETAILER_NAMES, only_needs_check=only_needs_check,
      label=f"자동 스케줄({'확인 필요만' if only_needs_check else '전체'})",
  )


def start_background_scheduler():
  """앱 프로세스 시작 시 1회 호출 - 매일 09:00 KST 전체 동기화 +
  4시간마다 확인 필요 상품만 재조회하는 백그라운드 스케줄러를 띄웁니다.
  이미 떠 있으면 다시 만들지 않고 기존 인스턴스를 그대로 반환합니다
  (NiceGUI reload 등으로 이 함수가 중복 호출되는 사고를 방지)."""
  global _scheduler
  if _scheduler is not None:
    return _scheduler

  scheduler = BackgroundScheduler(timezone=_KST_TZ)
  scheduler.add_job(
      _run_scheduled_sync,
      trigger=CronTrigger(hour=9, minute=0, timezone=_KST_TZ),
      kwargs={"only_needs_check": False},
      id="daily_full_sync",
      max_instances=1,
      coalesce=True,
  )
  scheduler.add_job(
      _run_scheduled_sync,
      trigger=IntervalTrigger(hours=4),
      kwargs={"only_needs_check": True},
      id="needs_check_sync",
      max_instances=1,
      coalesce=True,
  )
  scheduler.start()
  _scheduler = scheduler
  return scheduler
