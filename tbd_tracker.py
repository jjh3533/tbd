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
  }
  try:
    requests.post(url, json=payload, timeout=5)
  except Exception as e:
    print(f"텔레그램 발송 실패: {e}")


def fetch_amazon_info_via_scraperapi(asin):
  target_url = f"https://www.amazon.com/dp/{asin}"
  payload = {
      "api_key": SCRAPERAPI_KEY,
      "url": target_url,
      "country_code": "us",
      "keep_headers": "true",
  }

  try:
    res = requests.get("http://api.scraperapi.com", params=payload, timeout=30)
    if res.status_code != 200:
      return None

    soup = BeautifulSoup(res.text, "html.parser")

    amazon_usd = 0.0
    price_selectors = [
        "#corePriceDisplay_desktop_feature_div .a-offscreen",
        "#corePrice_feature_div .a-offscreen",
        "#apex_desktop .a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        ".a-price .a-offscreen",
    ]

    for selector in price_selectors:
      elems = soup.select(selector)
      for elem in elems:
        price_text = elem.get_text().strip()
        clean_p = re.sub(r"[^\d.]", "", price_text)
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

    weight_kg = None
    page_text = soup.get_text()
    weight_pattern = r"(?:Item|Package|Product)?\s*Weight\s*[:\n\t]*\s*([\d\.]+)\s*(pounds|lbs|ounces|oz|kg|g)"
    weight_match = re.search(weight_pattern, page_text, re.IGNORECASE)

    if weight_match:
      val = abs(float(weight_match.group(1)))
      unit = weight_match.group(2).lower()

      raw_weight = 0.0
      if unit in ["pounds", "lbs"]:
        raw_weight = val * 0.453592
      elif unit in ["ounces", "oz"]:
        raw_weight = val * 0.0283495
      elif unit == "kg":
        raw_weight = val
      elif unit == "g":
        raw_weight = val / 1000.0

      calc_weight = raw_weight + 0.5
      weight_kg = math.ceil(calc_weight * 2.0) / 2.0

    if weight_kg is None or weight_kg <= 0:
      weight_kg = 1.0

    return {
        "amazon_usd": amazon_usd,
        "in_stock": in_stock,
        "weight_kg": weight_kg,
    }

  except Exception:
    return None


def run_tracker():
  print("🚀 스케줄 동기화 시작...")
  current_rate = get_current_exchange_rate()
  records = table.all()

  for r in records:
    record_id = r["id"]
    fields = r["fields"]
    sku = fields.get("SKU", "무명 상품")
    asin = fields.get("ASIN")

    if not asin:
      continue

    prev_usd = fields.get("Amazon_USD", 0.0)
    prev_stock = fields.get("In_Stock", False)
    prev_weight = fields.get("Weight_KG")
    prev_rate = fields.get("Exchange_Rate")
    naver_id = fields.get("Naver_Product_No", "-")

    amazon_data = fetch_amazon_info_via_scraperapi(asin)
    update_data = {}

    if prev_rate != current_rate:
      update_data["Exchange_Rate"] = current_rate

    if amazon_data:
      curr_usd = (
          amazon_data["amazon_usd"]
          if amazon_data["amazon_usd"] > 0
          else prev_usd
      )
      curr_stock = amazon_data["in_stock"]
      raw_w = (
          amazon_data["weight_kg"]
          if amazon_data["weight_kg"] is not None
          else (prev_weight or 1.0)
      )
      curr_weight = math.ceil(raw_w * 2.0) / 2.0

      if prev_usd != curr_usd:
        update_data["Amazon_USD"] = curr_usd
      if prev_stock != curr_stock:
        update_data["In_Stock"] = curr_stock
      if prev_weight != curr_weight:
        update_data["Weight_KG"] = curr_weight

      if update_data:
        table.update(record_id, update_data)
        updated_record = table.get(record_id)
        new_calc_price = updated_record["fields"].get("Calculated_Price", 0)
        shipping_krw = updated_record["fields"].get("Shipping_KRW", 0)

        msg_lines = []
        if prev_usd == 0.0 and curr_usd > 0:
          msg_lines.append(f"✨ **[신규 상품 자동 등록 완료]** *{sku}*")
          msg_lines.append(f"• 아마존 원가: `${curr_usd}`")
          msg_lines.append(
              f"• 적용 무게/내배송비: `{curr_weight}kg` ({shipping_krw:,}원)"
          )
          msg_lines.append(f"• 추천 판매가: **`{new_calc_price:,}원`**")

        elif prev_stock != curr_stock:
          status_str = (
              "🔴 **[품절 발생]**"
              if not curr_stock
              else "🟢 **[재입고 완료]**"
          )
          msg_lines.append(f"{status_str} *{sku}*")
          if not curr_stock:
            msg_lines.append(
                f"👉 스마트스토어({naver_id}) **품절 처리** 필요"
            )

        elif prev_usd != curr_usd and curr_stock:
          diff = curr_usd - prev_usd
          direction = "📈 상승" if diff > 0 else "📉 하락"
          msg_lines.append(
              f"🔔 **[가격 변동 감지 - {direction}]** *{sku}*"
          )
          msg_lines.append(
              f"• 아마존 원가: `${prev_usd}` ➡️ **`${curr_usd}`**"
          )
          msg_lines.append(
              f"• 적용 무게/내배송비: `{curr_weight}kg` ({shipping_krw:,}원)"
          )
          msg_lines.append(f"• 추천 판매가: **`{new_calc_price:,}원`**")
          msg_lines.append(
              f"👉 [스마트스토어 수정 바로가기](https://sell.smartstore.naver.com/)"
          )

        if msg_lines:
          send_telegram_msg("\n".join(msg_lines))
          print(f"✅ 업데이트 및 텔레그램 알림 발송: {sku}")
  print("🎉 동기화 성공적으로 종료!")


if __name__ == "__main__":
  run_tracker()
