from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import re
import threading
import time
from bs4 import BeautifulSoup
from pyairtable import Api
import requests
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
# 1. 환경 설정 및 인증 정보
# ==========================================
# 시크릿은 하드코딩하지 않고 config.py(환경변수 / GitHub Actions Secrets)에서 가져옵니다.
api = Api(AIRTABLE_API_TOKEN)
table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)


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
    print(f"텔레그램 발송 실패: {e}")


# Amazon PDP 플러그인 엔드포인트는 토큰당 동시 요청 1개 제한이 있어,
# ThreadPoolExecutor의 여러 워커가 동시에 Amazon을 호출하지 못하도록
# 세마포어로 직렬화합니다. (Adorama/B&H는 일반 프록시 엔드포인트라 해당 없음)
_AMAZON_SEMAPHORE = threading.Semaphore(1)


# --- 1) Adorama 파서 ---
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


# --- 2) Amazon 파서 ---
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


# --- 3) B&H 파서 ---
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


# 단일 상품 수집 및 판정 로직
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

  adorama_data = fetch_adorama_info(adorama_id)
  amazon_data = fetch_amazon_info(asin)
  bh_data = fetch_bh_info(bh_id)

  adorama_price = adorama_data["price"] if adorama_data else 0.0
  amazon_price = amazon_data["price"] if amazon_data else 0.0
  bh_price = bh_data["price"] if bh_data else 0.0

  valid_retailers = []
  max_threshold = msrp_usd if msrp_usd > 0 else 99999.0

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

  # MSRP 이하 재고 유무 판정
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

  status_change = None
  if prev_stock != curr_stock:
    if not curr_stock:
      status_change = (
          "OOS",
          f"🔴 **[품절 발생 - MSRP 이하 재고 없음]** *{sku}*\n• 스마트스토어({naver_id})"
          " **품절 처리** 필요",
      )
    else:
      updated_record = table.get(record_id)
      new_sell_price = updated_record["fields"].get("판매금액", 0)
      available_sources = ", ".join(valid_retailers)
      status_change = (
          "IN_STOCK",
          f"🟢 **[재입고 감지]** *{sku}*\n• 정가 범위 구매처: **{available_sources}**\n•"
          f" 추천 판매가 (MSRP 기준): **`{new_sell_price:,}원`**",
      )

  return status_change


def run_tracker():
  print("⚡ Adorama / Amazon / B&H 초고속 동기화 시작...")
  current_rate = get_current_exchange_rate()
  records = table.all()
  total_count = len(records)

  out_of_stock_count = 0
  back_in_stock_count = 0
  detail_messages = []

  # Scrape.do Hobby Plan은 계정 전체 동시 요청 10개까지 허용합니다. Amazon
  # PDP 요청은 별도로 _AMAZON_SEMAPHORE(동시 1개)로 직렬화되어 이 한도와
  # 무관하게 돌아가므로, 나머지 Adorama/B&H 일반 프록시 요청 기준으로 여유를
  # 좀 남겨 max_workers=8로 설정합니다. (Airtable 쓰기는 pyairtable이 429를
  # 자동 재시도하므로 워커 수를 늘려도 크게 문제되지 않습니다.)
  with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [
        executor.submit(process_single_record, r, current_rate) for r in records
    ]
    for future in as_completed(futures):
      res = future.result()
      if res:
        st_type, msg = res
        if st_type == "OOS":
          out_of_stock_count += 1
        elif st_type == "IN_STOCK":
          back_in_stock_count += 1
        detail_messages.append(msg)

  changed_total = out_of_stock_count + back_in_stock_count

  summary_header = [
      "📊 **[TBD SEOUL] 일일 크롤링 종합 리포트**",
      f"• **총 관리 상품**: {total_count}개",
      f"• **상태 변동 상품**: {changed_total}개 (🔴 품절 {out_of_stock_count} / 🟢"
      f" 정상판매 {back_in_stock_count})",
      "\n---",
  ]

  if detail_messages:
    final_msg = "\n\n".join(["\n".join(summary_header)] + detail_messages)
    final_msg += (
        "\n\n👉 [스마트스토어 수정"
        " 바로가기](https://sell.smartstore.naver.com/)"
    )
  else:
    final_msg = (
        "\n".join(summary_header)
        + "\n\n✨ 품절 전환 또는 재입고 변동 사항이 없습니다."
    )

  send_telegram_msg(final_msg)
  print("🎉 동기화 완료!")


if __name__ == "__main__":
  run_tracker()
