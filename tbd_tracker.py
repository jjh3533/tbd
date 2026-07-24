import math
import os
import re
from bs4 import BeautifulSoup
from pyairtable import Api
import requests
import yfinance as yf

# ==========================================
# 1. 환경 설정 및 인증 정보
# ==========================================
AIRTABLE_API_TOKEN = os.getenv(
    "AIRTABLE_API_TOKEN",
    "patGCAx3PVLC76hji.998b00597d0a3751e2151d0f1d1e6ef3f2c9790b0ff9686929d4b353cb24c418",
)
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "apphI9EUz746dP0Ye")
AIRTABLE_TABLE_NAME = "Products"

SCRAPERAPI_KEY = os.getenv(
    "SCRAPERAPI_KEY", "643a1d003d0287a250d8cff2f6016159"
)

TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN", "8997002649:AAFku9xJ3fKAEq8yaqE8vQAlu8R34vqIwjw"
)
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7729393976")

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


# --- 1) B&H 크롤링 ---
def fetch_bh_info(bh_id):
  if not bh_id:
    return None
  target_url = f"https://www.bhphotovideo.com/c/product/{bh_id}.html"
  try:
    res = requests.get(
        "http://api.scraperapi.com",
        params={
            "api_key": SCRAPERAPI_KEY,
            "url": target_url,
            "country_code": "us",
            "keep_headers": "true",
        },
        timeout=30,
    )
    if res.status_code != 200:
      return None
    soup = BeautifulSoup(res.text, "html.parser")

    price_elem = soup.select_one('[data-selenium="pricingPrice"]')
    stock_elem = soup.select_one('[data-selenium="stockStatus"]')

    in_stock = True
    if stock_elem and "out of stock" in stock_elem.get_text().lower():
      in_stock = False

    price = 0.0
    if price_elem:
      clean_p = re.sub(r"[^\d.]", "", price_elem.get_text())
      if clean_p:
        price = float(clean_p)

    return {"price": price, "in_stock": in_stock}
  except Exception:
    return None


# --- 2) Adorama 크롤링 ---
def fetch_adorama_info(adorama_id):
  if not adorama_id:
    return None
  target_url = f"https://www.adorama.com/{adorama_id}.html"
  try:
    res = requests.get(
        "http://api.scraperapi.com",
        params={
            "api_key": SCRAPERAPI_KEY,
            "url": target_url,
            "country_code": "us",
            "keep_headers": "true",
        },
        timeout=30,
    )
    if res.status_code != 200:
      return None
    soup = BeautifulSoup(res.text, "html.parser")

    price_elem = soup.select_one(".your-price") or soup.select_one(
        '[itemprop="price"]'
    )
    stock_elem = soup.select_one(".stock-status") or soup.select_one(
        ".availability"
    )

    in_stock = True
    if stock_elem and "out of stock" in stock_elem.get_text().lower():
      in_stock = False

    price = 0.0
    if price_elem:
      clean_p = re.sub(r"[^\d.]", "", price_elem.get_text())
      if clean_p:
        price = float(clean_p)

    return {"price": price, "in_stock": in_stock}
  except Exception:
    return None


# --- 3) Amazon 크롤링 ---
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
        timeout=30,
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


def run_tracker():
  print("🚀 멀티 쇼핑몰(B&H ➔ Adorama ➔ Amazon) 동기화 시작...")
  current_rate = get_current_exchange_rate()
  records = table.all()

  total_count = len(records)
  out_of_stock_count = 0
  back_in_stock_count = 0
  detail_messages = []

  for r in records:
    record_id = r["id"]
    fields = r["fields"]
    sku = fields.get("SKU", "무명 상품")

    bh_id = fields.get("BH_ID")
    adorama_id = fields.get("ADORAMA_ID")
    asin = fields.get("ASIN")

    msrp_usd = fields.get("MSRP_USD", 0.0)
    prev_stock = fields.get("In_Stock", False)
    prev_rate = fields.get("Exchange_Rate")
    naver_id = fields.get("Naver_Product_No", "-")

    # 순서대로 크롤링 실행
    bh_data = fetch_bh_info(bh_id)
    adorama_data = fetch_adorama_info(adorama_id)
    amazon_data = fetch_amazon_info(asin)

    bh_price = bh_data["price"] if bh_data else 0.0
    adorama_price = adorama_data["price"] if adorama_data else 0.0
    amazon_price = amazon_data["price"] if amazon_data else 0.0

    # 유효한 정가 이하 가격 수집
    valid_candidates = []
    if (
        bh_data
        and bh_data["in_stock"]
        and 0 < bh_price <= (msrp_usd if msrp_usd > 0 else 99999)
    ):
      valid_candidates.append(("B&H", bh_price))
    if (
        adorama_data
        and adorama_data["in_stock"]
        and 0 < adorama_price <= (msrp_usd if msrp_usd > 0 else 99999)
    ):
      valid_candidates.append(("Adorama", adorama_price))
    if (
        amazon_data
        and amazon_data["in_stock"]
        and 0 < amazon_price <= (msrp_usd if msrp_usd > 0 else 99999)
    ):
      valid_candidates.append(("Amazon", amazon_price))

    # 최저가 산출 및 재고 상태 결정
    if valid_candidates:
      valid_candidates.sort(key=lambda x: x[1])
      best_source, best_price = valid_candidates[0]
      curr_stock = True
    else:
      best_source, best_price = "None", msrp_usd
      curr_stock = False

    # 에어테이블 업데이트 준비
    update_data = {
        "BH_USD": bh_price,
        "Adorama_USD": adorama_price,
        "Amazon_USD": amazon_price,
        "Best_USD": best_price,
        "In_Stock": curr_stock,
    }
    if prev_rate != current_rate:
      update_data["Exchange_Rate"] = current_rate

    table.update(record_id, update_data)

    # 알림 메시지 생성
    if prev_stock != curr_stock:
      if not curr_stock:
        out_of_stock_count += 1
        detail_messages.append(
            f"🔴 **[품절 발생 - 정가 재고 없음]** *{sku}*\n•"
            f" 스마트스토어({naver_id}) **품절 처리** 필요"
        )
      else:
        back_in_stock_count += 1
        updated_record = table.get(record_id)
        new_calc_price = updated_record["fields"].get("Calculated_Price", 0)
        detail_messages.append(
            f"🟢 **[재입고 감지]** *{sku}*\n• 최저가 출처: **{best_source}**"
            f" (${best_price})\n• 추천 판매가: **`{new_calc_price:,}원`**"
        )

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
  print("🎉 동기화 리포트 발송 완료!")


if __name__ == "__main__":
  run_tracker()
