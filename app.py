from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape as html_escape
import json
import math
import re
import textwrap
import threading
import time
from bs4 import BeautifulSoup
import pandas as pd
from pyairtable import Api
import requests
import streamlit as st
import yfinance as yf

from config import (
    AIRTABLE_API_TOKEN,
    AIRTABLE_BASE_ID,
    AIRTABLE_TABLE_NAME,
    SCRAPEDO_TOKEN,
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
)

# ==========================================
# 1. 페이지 및 환경 설정
# ==========================================
st.set_page_config(
    page_title="UniFi Supply Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 시크릿은 하드코딩하지 않고 config.py(환경변수/Streamlit Secrets)에서 가져옵니다.
api = Api(AIRTABLE_API_TOKEN)
table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

# ==========================================
# 🎨 UI.com Custom CSS Injector
# ==========================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background-color: #f8fafc;
        color: #0f172a;
    }

    .uic-header {
        background: linear-gradient(135deg, #0b132b 0%, #1c2541 100%);
        padding: 24px 32px;
        border-radius: 12px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .uic-title {
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #ffffff;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .uic-subtitle {
        font-size: 13px;
        color: #94a3b8;
        margin-top: 4px;
        font-weight: 400;
    }

    .uic-badge {
        background-color: #0066ff;
        color: #ffffff;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #0066ff !important;
    }

    .stButton > button {
        background-color: #0066ff !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 8px rgba(0, 102, 255, 0.2) !important;
    }

    .stButton > button:hover {
        background-color: #0052cc !important;
        box-shadow: 0 4px 12px rgba(0, 102, 255, 0.35) !important;
        transform: translateY(-1px);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #e2e8f0;
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 14px;
        color: #64748b;
        padding: 12px 4px;
    }

    .stTabs [aria-selected="true"] {
        color: #0066ff !important;
        border-bottom-color: #0066ff !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. 백엔드 핵심 함수
# ==========================================
def get_current_exchange_rate():
  try:
    ticker = yf.Ticker("KRW=X")
    todays_data = ticker.history(period="1d")
    base_rate = todays_data["Close"].iloc[-1]
    return round(base_rate + 10, 1)
  except Exception:
    return 1380.0


def send_telegram_msg(text: str):
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
    st.error(f"텔레그램 발송 실패: {e}")


@st.cache_data(ttl=60)
def get_scrapedo_usage():
  """Scrape.do 계정의 남은 크레딧/동시요청 현황을 조회합니다.

  이 엔드포인트는 분당 최대 10회 호출 제한이 있는데, Streamlit은 상호작용마다
  스크립트를 처음부터 재실행하므로 매번 호출하면 금방 한도를 넘길 수 있습니다.
  st.cache_data(ttl=60)로 60초에 한 번만 실제로 호출하도록 캐싱합니다.
  """
  try:
    res = requests.get(
        "https://api.scrape.do/info",
        params={"token": SCRAPEDO_TOKEN},
        timeout=10,
    )
    if res.status_code == 200:
      return res.json()
  except Exception:
    pass
  return None


# Amazon PDP 플러그인 엔드포인트는 토큰당 동시 요청 1개 제한이 있어,
# ThreadPoolExecutor의 여러 워커가 동시에 Amazon을 호출하지 못하도록
# 세마포어로 직렬화합니다. (Adorama/B&H는 일반 프록시 엔드포인트라 해당 없음)
_AMAZON_SEMAPHORE = threading.Semaphore(1)


def _scrapedo_get(target_url, timeout=60, max_retries=1, retry_delay=2.0,
                   try_super_on_failure=True, force_super=False):
  """Scrape.do 요청 공용 래퍼 (재시도 + 비용 절감 escalation 포함).

  Scrape.do는 일반 프록시가 1크레딧, 봇 차단 우회용 residential/mobile
  프록시(super=true)는 10크레딧입니다. Adorama/B&H는 Scrape.do의 자동
  도메인별 요금표에 없는 사이트라, 매번 super=true로 쏘면 불필요하게
  비쌉니다. 그래서 기본적으로는 먼저 super=false(1크레딧)로 시도하고, 그게
  실패(봇 차단 등으로 200이 안 옴)할 때만 super=true(10크레딧)로 한 번 더
  시도하는 방식으로 평균 비용을 낮춥니다.

  force_super=True로 호출하면 이 escalation 단계를 건너뛰고 바로
  super=true로 요청합니다. B&H는 실측 결과 super=false가 매번 실패해서
  (실패 자체는 과금되는 상태코드가 아니라 크레딧 손해는 없지만) 매번 왕복
  한 번을 낭비하므로, 여기서는 바로 super로 쏘는 게 더 빠릅니다.

  timeout=60: 응답이 오래 걸리는 봇 차단 우회 요청도 넉넉히 기다립니다.
  """
  if force_super:
    tiers = [True]
  else:
    tiers = [False, True] if try_super_on_failure else [False]
  for use_super in tiers:
    for attempt in range(max_retries + 1):
      try:
        res = requests.get(
            "https://api.scrape.do/",
            params={
                "token": SCRAPEDO_TOKEN,
                "url": target_url,
                "geoCode": "us",
                "super": "true" if use_super else "false",
            },
            timeout=timeout,
        )
        if res.status_code == 200:
          return res
      except Exception:
        pass
      if attempt < max_retries:
        time.sleep(retry_delay)
  return None


def fetch_adorama_info(adorama_id):
  if not adorama_id:
    return None

  clean_id = str(adorama_id).strip().lower()
  target_url = f"https://www.adorama.com/{clean_id}.html"

  try:
    res = _scrapedo_get(target_url)
    if res is None:
      return None

    soup = BeautifulSoup(res.text, "html.parser")
    adorama_usd = 0.0
    in_stock = True

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

    return {"price": adorama_usd, "in_stock": in_stock}
  except Exception:
    return None


def fetch_amazon_info(asin, timeout=60, max_retries=2, retry_delay=2.0):
  """Scrape.do의 Amazon Scraper API(PDP 플러그인)로 아마존 상품 정보를 가져옵니다.

  일반 프록시로 아마존 HTML을 긁어 CSS 셀렉터로 파싱하던 방식 대신,
  Scrape.do가 아마존 전용으로 제공하는 구조화 JSON 엔드포인트
  (`/plugin/amazon/pdp`, 요청당 1크레딧)를 사용합니다. 이 엔드포인트는
  토큰당 동시 요청 1개 제한이 있어 `_AMAZON_SEMAPHORE`로 직렬화합니다.

  PDP 응답에는 명시적인 재고 여부 필드가 없어서, price가 비어있으면
  구매 불가(품절/판매중단 등)로 간주합니다.
  """
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
          return {"price": amazon_usd, "in_stock": amazon_usd > 0}
        return {"price": 0.0, "in_stock": False}
    except Exception:
      pass
    if attempt < max_retries:
      time.sleep(retry_delay)
  return None


_WEIGHT_UNIT_TO_KG = {
    "kg": 1.0,
    "g": 0.001,
    "lb": 0.453592,
    "lbs": 0.453592,
    "oz": 0.0283495,
}


def _parse_bh_package_weight_kg(soup):
  """B&H Specs의 'Packaging Info > Package Weight' 행에서 배송 패키지 무게를

  kg 단위로 추출합니다. (예: "1.83 lb" -> 0.83kg)
  스펙 테이블 마크업(class/id)을 직접 확인하지 못했으므로, 페이지의 모든
  표/정의목록을 순회하며 라벨 텍스트로 행을 찾는 방식으로 구현했습니다.
  """
  label_pattern = re.compile(r"package\s*weight", re.IGNORECASE)
  weight_pattern = re.compile(r"([\d.]+)\s*(kg|lbs|lb|oz|g)\b", re.IGNORECASE)

  # 1) <table> 형태의 스펙 테이블
  for row in soup.find_all("tr"):
    cells = row.find_all(["td", "th"])
    if len(cells) < 2:
      continue
    if label_pattern.search(cells[0].get_text(strip=True)):
      match = weight_pattern.search(cells[1].get_text(strip=True))
      if match:
        value, unit = float(match.group(1)), match.group(2).lower()
        return round(value * _WEIGHT_UNIT_TO_KG.get(unit, 1.0), 3)

  # 2) <dl><dt>Package Weight</dt><dd>1.83 lb</dd></dl> 형태의 폴백
  for dt in soup.find_all("dt"):
    if label_pattern.search(dt.get_text(strip=True)):
      dd = dt.find_next_sibling("dd")
      if dd:
        match = weight_pattern.search(dd.get_text(strip=True))
        if match:
          value, unit = float(match.group(1)), match.group(2).lower()
          return round(value * _WEIGHT_UNIT_TO_KG.get(unit, 1.0), 3)

  return None


def fetch_bh_info(bh_id):
  if not bh_id:
    return None

  # BH_ID(예: "1815010-REG")만 있으면 슬러그 없이도 B&H가 정식 URL로
  # 리다이렉트해줍니다. 상품별 슬러그를 따로 저장/관리할 필요가 없습니다.
  clean_id = str(bh_id).strip().upper()
  target_url = f"https://www.bhphotovideo.com/c/product/{clean_id}/"

  try:
    # 실측 결과 B&H는 super=false가 항상 실패해서 바로 super=true로 요청.
    res = _scrapedo_get(target_url, force_super=True)
    if res is None:
      return None

    soup = BeautifulSoup(res.text, "html.parser")
    bh_usd = 0.0
    in_stock = True

    # 1) JSON-LD(schema.org Product/Offer) 우선 파싱 — Adorama와 동일한 전략.
    # B&H도 SEO/Google Shopping 목적으로 대부분 상품 페이지에 이 마크업을 포함합니다.
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
          break
      except Exception:
        pass

    # 2) JSON-LD가 없거나 가격을 못 찾은 경우 CSS 셀렉터 폴백.
    # ⚠️ B&H 실제 마크업의 class/attribute를 직접 확인하지 못한 상태로 작성한
    # 일반적인 셀렉터입니다. 이 경로로 가격이 0으로 나오면 실제 페이지의
    # 개발자도구로 가격 엘리먼트를 확인해서 셀렉터를 갱신해야 합니다.
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

    # "Coming Soon"/"Notify When Available" 같은 신제품 사전공개 페이지는
    # 가격은 표시되지만 실제로 구매가 불가능합니다. JSON-LD가 이를 놓치거나
    # 부정확하게 InStock으로 표기하는 경우를 대비해, 이 문구들은 JSON-LD 결과와
    # 무관하게 항상 우선 확인해서 in_stock을 덮어씁니다.
    if bh_usd > 0:
      page_text = soup.get_text(" ", strip=True).lower()
      oos_keywords = [
          "out of stock",
          "discontinued",
          "sold out",
          "coming soon",
          "notify when available",
          "special order",
          "backordered",
          "pre-order",
          "preorder",
      ]
      if any(kw in page_text for kw in oos_keywords):
        in_stock = False

    weight_kg = _parse_bh_package_weight_kg(soup)

    return {"price": bh_usd, "in_stock": in_stock, "weight_kg": weight_kg}
  except Exception:
    return None


def process_single_record(r, current_rate):
  record_id = r["id"]
  fields = r["fields"]
  sku = fields.get("SKU", "무명 상품")

  adorama_id = fields.get("ADORAMA_ID")
  asin = fields.get("ASIN")
  bh_id = fields.get("BH_ID")

  msrp_usd = fields.get("MSRP_USD", 0.0)
  prev_stock = fields.get("In_Stock", False)
  naver_id = fields.get("Naver_Product_No", "-")
  max_threshold = msrp_usd if msrp_usd > 0 else 99999.0

  adorama_data = fetch_adorama_info(adorama_id)
  amazon_data = fetch_amazon_info(asin)
  bh_data = fetch_bh_info(bh_id)

  adorama_price = adorama_data["price"] if adorama_data else 0.0
  amazon_price = amazon_data["price"] if amazon_data else 0.0
  bh_price = bh_data["price"] if bh_data else 0.0

  valid_retailers = []
  if (
      adorama_data
      and adorama_data["in_stock"]
      and 0 < adorama_price <= max_threshold
  ):
    valid_retailers.append("Adorama")
  if (
      amazon_data
      and amazon_data["in_stock"]
      and 0 < amazon_price <= max_threshold
  ):
    valid_retailers.append("Amazon")
  if (
      bh_data
      and bh_data["in_stock"]
      and 0 < bh_price <= max_threshold
  ):
    valid_retailers.append("B&H")

  curr_stock = True if valid_retailers else False

  update_data = {
      "Adorama_USD": adorama_price,
      "Amazon_USD": amazon_price,
      "BH_USD": bh_price,
      "In_Stock": curr_stock,
      "Exchange_Rate": current_rate,
  }

  # B&H 배송 패키지 무게(kg)로 매번 덮어씁니다. B&H가 가장 정확한 스펙
  # 출처라고 판단해 동기화할 때마다 최신 값으로 갱신합니다.
  bh_weight_kg = bh_data.get("weight_kg") if bh_data else None
  if bh_weight_kg is not None:
    update_data["Weight_KG"] = bh_weight_kg

  try:
    table.update(record_id, update_data)
  except Exception:
    pass

  # 주의: 이 함수는 ThreadPoolExecutor 워커 스레드에서 실행됩니다.
  # Streamlit의 st.* 호출은 스크립트 실행 컨텍스트가 있는 메인 스레드에서만
  # 가능하므로(NoSessionContext 에러), 여기서는 로그 문자열만 만들어 반환하고
  # 실제 log_container.write()는 run_tbd_tracker()의 메인 스레드 루프에서 호출합니다.
  log_line = (
      f"✅ [{sku}] Complete | Ado:${adorama_price} / Amz:${amazon_price} /"
      f" BH:${bh_price}"
  )

  status_change = None
  if prev_stock != curr_stock:
    if not curr_stock:
      status_change = (
          "OOS",
          f"🔴 **[OUT OF STOCK - Above MSRP]** *{sku}*\n• SmartStore"
          f" ID({naver_id}) Action Required",
      )
    else:
      updated_record = table.get(record_id)
      new_sell_price = updated_record["fields"].get("판매금액", 0)
      available_sources = ", ".join(valid_retailers)
      status_change = (
          "IN_STOCK",
          f"🟢 **[BACK IN STOCK]** *{sku}*\n• Valid Retailers:"
          f" **{available_sources}**\n• Target Price (MSRP Based):"
          f" **`{new_sell_price:,}원`**",
      )

  return log_line, status_change


def run_tbd_tracker(log_container):
  log_container.write(
      "⚡ [UI.com Engine] Adorama / Amazon / B&H Triple-Channel Syncing..."
  )
  current_rate = get_current_exchange_rate()
  log_container.write(f"💱 Applied Exchange Rate: ₩{current_rate}")

  records = table.all()
  total_count = len(records)
  log_container.write(f"📦 Active Inventory Records: {total_count}")

  out_of_stock_count = 0
  back_in_stock_count = 0
  detail_messages = []
  updated_count = len(records)

  # Scrape.do Hobby Plan은 계정 전체 동시 요청 10개까지 허용합니다. Amazon
  # PDP 요청은 별도로 _AMAZON_SEMAPHORE(동시 1개)로 직렬화되어 이 한도와
  # 무관하게 돌아가므로, 나머지 Adorama/B&H 일반 프록시 요청 기준으로 여유를
  # 좀 남겨 max_workers=8로 설정합니다. (Airtable 쓰기는 pyairtable이 429를
  # 자동 재시도하므로 워커 수를 늘려도 크게 문제되지 않습니다.)
  with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [
        executor.submit(process_single_record, r, current_rate)
        for r in records
    ]
    for future in as_completed(futures):
      log_line, res = future.result()
      # log_container.write()는 메인 스레드(스크립트 실행 컨텍스트)에서만 호출합니다.
      log_container.write(log_line)
      if res:
        st_type, msg = res
        if st_type == "OOS":
          out_of_stock_count += 1
        elif st_type == "IN_STOCK":
          back_in_stock_count += 1
        detail_messages.append(msg)

  changed_total = out_of_stock_count + back_in_stock_count

  summary_header = [
      "📊 **[UI.com Supply Monitor] Sync Report**",
      f"• **Monitored Items**: {total_count} units",
      f"• **Status Shift**: {changed_total} (🔴 Out of Stock {out_of_stock_count}"
      f" / 🟢 Normal {back_in_stock_count})",
      "\n---",
  ]

  if detail_messages:
    final_msg = "\n\n".join(["\n".join(summary_header)] + detail_messages)
    final_msg += (
        "\n\n👉 [Naver Commerce Admin](https://sell.smartstore.naver.com/)"
    )
  else:
    final_msg = (
        "\n".join(summary_header)
        + "\n\n✨ All inventory & price levels optimal."
    )

  send_telegram_msg(final_msg)
  log_container.write("🎉 Fast Parallel Sync Complete!")
  return updated_count


# ==========================================
# 3. Streamlit UI 구성
# ==========================================

st.markdown(
    """
    <div class="uic-header">
        <div>
            <div class="uic-title">⚡ UniFi Supply Monitor</div>
            <div class="uic-subtitle">MSRP-Based Price Engine & Adorama/Amazon/B&H Triple Guard</div>
        </div>
        <div class="uic-badge">SYSTEM ACTIVE</div>
    </div>
""",
    unsafe_allow_html=True,
)

current_rate = get_current_exchange_rate()
scrapedo_usage = get_scrapedo_usage()

col_m1, col_m2, col_m3 = st.columns([1, 1, 3])
with col_m1:
  st.metric(label="USD / KRW Exchange Rate", value=f"₩ {current_rate:,}")
with col_m2:
  if scrapedo_usage:
    remaining = scrapedo_usage.get("RemainingMonthlyRequest", 0)
    max_credits = scrapedo_usage.get("MaxMonthlyRequest", 0)
    pct_left = f"{remaining / max_credits:.0%} 남음" if max_credits else None
    st.metric(
        label="Scrape.do 잔여 크레딧",
        value=f"{remaining:,}",
        delta=pct_left,
        delta_color="off",
        help=f"월 한도 {max_credits:,} 크레딧 기준",
    )
  else:
    st.metric(label="Scrape.do 잔여 크레딧", value="조회 실패")

st.divider()

tab1, tab2 = st.tabs(["📦 Inventory & Price Grid", "➕ Register New Product"])

with tab1:
  col_t1, col_t2 = st.columns([3, 1])
  with col_t1:
    st.markdown("### Managed Products")
  with col_t2:
    # 참고(Scrape.do 기준, 실측 반영): Amazon은 PDP 전용 엔드포인트로 요청당
    # 1크레딧 고정. B&H는 일반 프록시가 항상 막혀서 바로 super=true(10크레딧)로
    # 요청. Adorama는 일반 프록시(1크레딧)로 먼저 시도하고 막히는 경우에만
    # super=true(10크레딧)로 재시도하므로 상품 1개당 보통 12크레딧, 봇 차단이
    # 걸리면 최대 약 22크레딧까지 소모될 수 있습니다.
    if st.button(
        "⚡ Sync Retailers Now", type="primary", use_container_width=True,
        help="상품 1개당 Adorama+Amazon+B&H 합쳐 보통 약 12크레딧, 봇 차단이"
        " 걸리면 최대 약 22크레딧까지 소모될 수 있습니다.",
    ):
      with st.status("Executing Multi-thread Sync...", expanded=True) as status:
        count = run_tbd_tracker(status)
        status.update(
            label=f"Sync Finished ({count} items updated)",
            state="complete",
            expanded=False,
        )
      st.success("AirTable and Telegram alerts updated.")
      st.rerun()

  records = table.all()
  if records:
    columns = [
        "SKU / Model", "Naver ID",
        # 가격 크롤링 내역: UniFi Store(MSRP) → B&H → Adorama → Amazon → Best Price 순
        "UniFi Store ($)", "B&H ($)", "Adorama ($)", "Amazon ($)", "Best Price ($)",
        "Status",
        "판매가격", "최종가격", "수익",
    ]
    divider_nth = columns.index("판매가격") + 1  # CSS nth-child는 1부터 시작
    final_price_nth = columns.index("최종가격") + 1
    best_price_nth = columns.index("Best Price ($)") + 1

    # UniFi Store(MSRP) 대비 Best Price 비교 색상
    COLOR_GOOD = "#2f6df6"  # 파랑 — MSRP보다 저렴 (좋음)
    COLOR_SAME = "#69c970"  # 초록 — MSRP와 동일
    COLOR_BAD = "#e37574"  # 빨강 — 가격정보 없음 또는 MSRP보다 비쌈

    def _rgba(hex_color, alpha):
      hex_color = hex_color.lstrip("#")
      r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
      return f"rgba({r}, {g}, {b}, {alpha})"

    # 가격 셀 클릭 시 해당 쇼핑몰 상품 페이지로 이동시키기 위한 URL 빌더.
    # fetch_*_info()에서 크롤링할 때 쓰는 URL 규칙과 동일하게 맞춥니다.
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

    rows_html = []
    for r in records:
      f = r["fields"]
      is_active = bool(f.get("In_Stock"))
      msrp = f.get("MSRP_USD", 0.0) or 0.0
      best_usd = f.get("Best_USD", 0.0) or 0.0
      bh_usd = f.get("BH_USD", 0.0) or 0.0
      adorama_usd = f.get("Adorama_USD", 0.0) or 0.0
      amazon_usd = f.get("Amazon_USD", 0.0) or 0.0

      bh_url = _bh_url(f.get("BH_ID"))
      adorama_url = _adorama_url(f.get("ADORAMA_ID"))
      amazon_url = _amazon_url(f.get("ASIN"))

      # Best Price는 세 곳 중 최저가라, 실제로 그 값을 낸 쇼핑몰의 링크로
      # 연결합니다. 반올림 오차 대비 0.01달러 오차는 같은 값으로 취급.
      best_price_url = None
      for price, url in (
          (bh_usd, bh_url), (adorama_usd, adorama_url), (amazon_usd, amazon_url)
      ):
        if url and price > 0 and abs(price - best_usd) < 0.01:
          best_price_url = url
          break

      if best_usd <= 0:
        best_color = COLOR_BAD
      elif round(best_usd, 2) < round(msrp, 2):
        best_color = COLOR_GOOD
      elif round(best_usd, 2) == round(msrp, 2):
        best_color = COLOR_SAME
      else:
        best_color = COLOR_BAD

      cells = {
          "SKU / Model": f.get("SKU", "-"),
          "Naver ID": f.get("Naver_Product_No", "-"),
          "UniFi Store ($)": f"${msrp:,.2f}",
          "B&H ($)": f"${bh_usd:,.2f}",
          "Adorama ($)": f"${adorama_usd:,.2f}",
          "Amazon ($)": f"${amazon_usd:,.2f}",
          "Best Price ($)": f"${best_usd:,.2f}",
          "Status": "🟢 Active" if is_active else "🔴 Out of Stock",
          "판매가격": f"₩ {f.get('판매금액', 0):,}",
          "최종가격": f"₩ {f.get('최종가격', 0):,}",
          "수익": f"₩ {f.get('수익', 0):,}",
      }

      # 금액 컬럼 → 해당 쇼핑몰 상품 페이지 링크. URL이 없으면(ID 미등록 등)
      # 그냥 텍스트로만 표시합니다.
      cell_links = {
          "B&H ($)": bh_url,
          "Adorama ($)": adorama_url,
          "Amazon ($)": amazon_url,
          "Best Price ($)": best_price_url,
      }

      tds = []
      for col in columns:
        value = html_escape(str(cells[col]))
        link_url = cell_links.get(col)
        if link_url:
          value = (
              f'<a href="{html_escape(link_url)}" target="_blank"'
              f' rel="noopener noreferrer">{value}</a>'
          )
        if col == "Best Price ($)":
          # MSRP 대비 좋음/동일/나쁨(또는 데이터 없음)에 따라 텍스트+배경색 적용.
          # 배경은 텍스트색의 15% 알파로 은은하게.
          style = (
              f"color:{best_color}; background-color:{_rgba(best_color, 0.15)};"
              " font-weight:600;"
          )
          tds.append(f'<td style="{style}">{value}</td>')
        else:
          tds.append(f"<td>{value}</td>")
      rows_html.append("<tr>" + "".join(tds) + "</tr>")

    thead_html = (
        "<tr>" + "".join(f"<th>{html_escape(c)}</th>" for c in columns) + "</tr>"
    )
    table_html = (
        f'<table class="uic-price-table"><thead>{thead_html}</thead>'
        f'<tbody>{"".join(rows_html)}</tbody></table>'
    )

    # 주의: st.markdown()에 넘기는 HTML 문자열 줄 앞에 공백(파이썬 코드 들여쓰기)이
    # 남아있으면 Markdown이 "들여쓴 코드블록"으로 인식해서 HTML을 렌더링하지 않고
    # 그대로 텍스트로 출력해버립니다. 반드시 textwrap.dedent()로 공통 들여쓰기를
    # 제거한 뒤, table_html(자체 들여쓰기가 다른 문자열)은 별도로 이어붙입니다.
    css_block = textwrap.dedent(f"""
        <style>
        .uic-price-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        .uic-price-table th, .uic-price-table td {{
            padding: 10px 14px;
            text-align: center;
            white-space: nowrap;
            border-bottom: 1px solid #e2e8f0;
        }}
        .uic-price-table thead th {{
            background-color: #f8fafc;
            font-weight: 700;
            color: #0f172a;
        }}
        .uic-price-table tbody tr:hover {{
            background-color: #f8fafc;
        }}
        .uic-price-table td a {{
            color: inherit;
            text-decoration: none;
        }}
        .uic-price-table td a:hover {{
            text-decoration: underline;
        }}
        .uic-price-table th:nth-child({divider_nth}),
        .uic-price-table td:nth-child({divider_nth}) {{
            border-left: 2.5px solid #e2e8f0;
        }}
        .uic-price-table th:nth-child({final_price_nth}),
        .uic-price-table td:nth-child({final_price_nth}) {{
            background-color: #eff6ff;
        }}
        /* Best Price 컬럼은 행마다 색이 달라서 헤더만 살짝 표시 */
        .uic-price-table th:nth-child({best_price_nth}) {{
            background-color: #f1f5f9;
        }}
        </style>
    """)

    st.markdown(
        css_block + f'<div style="overflow-x:auto;">{table_html}</div>',
        unsafe_allow_html=True,
    )
  else:
    st.info("No tracked products found in AirTable.")

with tab2:
  st.markdown("### Add Product to Monitor")
  st.caption(
      "Enter model identifiers and MSRP (including RAM surcharge) for"
      " automated tracking."
  )

  with st.form("add_product_form", clear_on_submit=True):
    f_col1, f_col2 = st.columns(2)
    with f_col1:
      new_sku = st.text_input(
          "Product Name / SKU *", placeholder="e.g. Ubiquiti Cloud Gateway Ultra"
      )
      new_msrp = st.number_input(
          "MSRP USD (Surcharge Included) *",
          min_value=0.0,
          value=199.0,
          step=1.0,
      )
      new_naver_id = st.text_input(
          "Naver SmartStore No.", placeholder="e.g. 10293848"
      )

    with f_col2:
      new_adorama = st.text_input(
          "Adorama SKU (Optional)", placeholder="e.g. ubcgultr"
      )
      new_asin = st.text_input(
          "Amazon ASIN (Optional)", placeholder="e.g. B0CWLKD9RP"
      )
      new_bh_id = st.text_input(
          "B&H ID (Optional)", placeholder="e.g. 1815010-REG"
      )

    submitted = st.form_submit_button("⚡ Add to Inventory System")

    if submitted:
      if not new_sku or new_msrp <= 0:
        st.error("SKU and valid MSRP are required!")
      else:
        new_record_data = {
            "SKU": new_sku.strip(),
            "MSRP_USD": float(new_msrp),
            "Exchange_Rate": current_rate,
        }
        if new_adorama:
          new_record_data["ADORAMA_ID"] = new_adorama.strip()
        if new_asin:
          new_record_data["ASIN"] = new_asin.strip().upper()
        if new_bh_id:
          new_record_data["BH_ID"] = new_bh_id.strip().upper()
        if new_naver_id:
          new_record_data["Naver_Product_No"] = new_naver_id.strip()

        try:
          table.create(new_record_data)
          st.success(f"⚡ [{new_sku}] successfully added to monitoring matrix!")
        except Exception as e:
          st.error(f"AirTable Registration Error: {e}")
