from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import re
from bs4 import BeautifulSoup
from pyairtable import Api
import requests
import yfinance as yf

from config import (
    AIRTABLE_API_TOKEN,
    AIRTABLE_BASE_ID,
    AIRTABLE_TABLE_NAME,
    SCRAPERAPI_KEY,
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


# --- 1) Adorama 파서 ---
def fetch_adorama_info(adorama_id):
  if not adorama_id:
    return None

  clean_id = str(adorama_id).strip().lower()
  target_url = f"https://www.adorama.com/{clean_id}.html"

  try:
    res = requests.get(
        "http://api.scraperapi.com",
        params={
            "api_key": SCRAPERAPI_KEY,
            "url": target_url,
            "country_code": "us",
            "keep_headers": "true",
        },
        timeout=15,
    )
    if res.status_code != 200:
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
def fetch_amazon_info(asin):
  if not asin:
    return None
  target_url = f"https://www.amazon.com/dp/{asin}"
  try:
    res = requests.get(
        "http://api.scraperapi.com",
        params={
            "api_key": SCRAPERAPI_KEY,
            "url": target_url,
            "country_code": "us",
            "keep_headers": "true",
        },
        timeout=15,
    )
    if res.status_code != 200:
      return None
    soup = BeautifulSoup(res.text, "html.parser")

    amazon_usd = 0.0
    price_selectors = [
        "#corePriceDisplay_desktop_feature_div .a-offscreen",
        "#corePrice_feature_div .a-offscreen",
        "#apex_desktop .a-offscreen",
        ".a-price .a-offscreen",
    ]
    for selector in price_selectors:
      elems = soup.select(selector)
      for elem in elems:
        clean_p = re.sub(r"[^\d.]", "", elem.get_text().strip())
        if clean_p:
          try:
            val = float(clean_p)
            if 5.0 <= val <= 10000.0:
              amazon_usd = val
              break
          except ValueError:
            pass
      if amazon_usd > 0:
        break

    in_stock = True
    avail_elem = soup.select_one("#availability")
    if avail_elem:
      avail_text = avail_elem.get_text().lower()
      if "currently unavailable" in avail_text or "out of stock" in avail_text:
        in_stock = False

    return {"price": amazon_usd, "in_stock": in_stock}
  except Exception:
    return None


# 단일 상품 수집 및 판정 로직
def process_single_record(r, current_rate):
  record_id = r["id"]
  fields = r["fields"]
  sku = fields.get("SKU", "무명 상품")

  adorama_id = fields.get("ADORAMA_ID")
  asin = fields.get("ASIN")

  msrp_usd = fields.get("MSRP_USD", 0.0)
  prev_stock = fields.get("In_Stock", False)
  naver_id = fields.get("Naver_Product_No", "-")

  adorama_data = fetch_adorama_info(adorama_id)
  amazon_data = fetch_amazon_info(asin)

  adorama_price = adorama_data["price"] if adorama_data else 0.0
  amazon_price = amazon_data["price"] if amazon_data else 0.0

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

  # MSRP 이하 재고 유무 판정
  curr_stock = True if valid_retailers else False

  update_data = {
      "Adorama_USD": adorama_price,
      "Amazon_USD": amazon_price,
      "In_Stock": curr_stock,
      "Exchange_Rate": current_rate,
  }

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
      new_calc_price = updated_record["fields"].get("Calculated_Price", 0)
      available_sources = ", ".join(valid_retailers)
      status_change = (
          "IN_STOCK",
          f"🟢 **[재입고 감지]** *{sku}*\n• 정가 범위 구매처: **{available_sources}**\n•"
          f" 추천 판매가 (MSRP 기준): **`{new_calc_price:,}원`**",
      )

  return status_change


def run_tracker():
  print("⚡ Adorama / Amazon 초고속 동기화 시작...")
  current_rate = get_current_exchange_rate()
  records = table.all()
  total_count = len(records)

  out_of_stock_count = 0
  back_in_stock_count = 0
  detail_messages = []

  with ThreadPoolExecutor(max_workers=5) as executor:
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
