import math
import re
from bs4 import BeautifulSoup
import pandas as pd
from pyairtable import Api
import requests
import streamlit as st
import yfinance as yf

# ==========================================
# 1. 페이지 및 환경 설정
# ==========================================
st.set_page_config(
    page_title="TBD SEOUL 대시보드", page_icon="🚀", layout="wide"
)

AIRTABLE_API_TOKEN = "patGCAx3PVLC76hji.998b00597d0a3751e2151d0f1d1e6ef3f2c9790b0ff9686929d4b353cb24c418"
AIRTABLE_BASE_ID = "apphI9EUz746dP0Ye"
AIRTABLE_TABLE_NAME = "Products"

SCRAPERAPI_KEY = "643a1d003d0287a250d8cff2f6016159"

TELEGRAM_TOKEN = "8997002649:AAFku9xJ3fKAEq8yaqE8vQAlu8R34vqIwjw"
TELEGRAM_CHAT_ID = "7729393976"

api = Api(AIRTABLE_API_TOKEN)
table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)


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


def run_tbd_tracker(log_container):
  log_container.write(
      "🚀 멀티 쇼핑몰(B&H ➔ Adorama ➔ Amazon) 크롤링 시작..."
  )
  current_rate = get_current_exchange_rate()
  log_container.write(f"💱 적용 환율: {current_rate}원")

  records = table.all()
  total_count = len(records)
  log_container.write(f"📦 에어테이블 레코드 {total_count}개 조회 완료")

  out_of_stock_count = 0
  back_in_stock_count = 0
  detail_messages = []
  updated_count = 0

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

    log_container.write(f"🔍 [{sku}] B&H ➔ Adorama ➔ Amazon 순서로 크롤링 중...")

    bh_data = fetch_bh_info(bh_id)
    adorama_data = fetch_adorama_info(adorama_id)
    amazon_data = fetch_amazon_info(asin)

    bh_price = bh_data["price"] if bh_data else 0.0
    adorama_price = adorama_data["price"] if adorama_data else 0.0
    amazon_price = amazon_data["price"] if amazon_data else 0.0

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

    if valid_candidates:
      valid_candidates.sort(key=lambda x: x[1])
      best_source, best_price = valid_candidates[0]
      curr_stock = True
    else:
      best_source, best_price = "None", msrp_usd
      curr_stock = False

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
    updated_count += 1

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

    log_container.write(
        f"✅ 완료: {sku} (최저가: ${best_price} / 출처: {best_source})"
    )

  changed_total = out_of_stock_count + back_in_stock_count

  summary_header = [
      "📊 **[TBD SEOUL] 웹 수동 동기화 리포트**",
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
  log_container.write("🎉 동기화 리포트 발송 완료!")
  return updated_count


# ==========================================
# 3. Streamlit UI 구성
# ==========================================
st.title("🚀 TBD SEOUL 커머스 관리 대시보드")
st.caption(
    "B&H ➔ Adorama ➔ Amazon 실시간 가격 비교 및 최저가 자동 산출 시스템"
)

current_rate = get_current_exchange_rate()
st.metric(label="현재 적용 환율 (KRW/USD)", value=f"{current_rate} 원")

st.divider()

tab1, tab2 = st.tabs(
    ["📦 Registered Products & Sync", "➕ Add New Item (신규 등록)"]
)

with tab1:
  col1, col2 = st.columns([3, 1])
  with col1:
    st.subheader("등록된 상품 현황")
  with col2:
    if st.button(
        "🔄 지금 데이터 동기화 실행", type="primary", use_container_width=True
    ):
      with st.status("동기화 진행 중...", expanded=True) as status:
        count = run_tbd_tracker(status)
        status.update(
            label=f"동기화 완료! ({count}개 변경됨)",
            state="complete",
            expanded=False,
        )
      st.success("에어테이블 및 텔레그램 알림 처리가 완료되었습니다.")
      st.rerun()

  records = table.all()
  if records:
    data_list = []
    for r in records:
      f = r["fields"]
      data_list.append({
          "SKU": f.get("SKU", "-"),
          "MSRP ($)": f.get("MSRP_USD", 0.0),
          "B&H ($)": f.get("BH_USD", 0.0),
          "Adorama ($)": f.get("Adorama_USD", 0.0),
          "Amazon ($)": f.get("Amazon_USD", 0.0),
          "Best ($)": f.get("Best_USD", 0.0),
          "In Stock": "🟢 정상판매" if f.get("In_Stock") else "🔴 품절(웃돈/재고없음)",
          "Calculated Price (KRW)": f.get("Calculated_Price", 0),
          "Naver Product No": f.get("Naver_Product_No", "-"),
      })

    df = pd.DataFrame(data_list)
    st.dataframe(df, use_container_width=True, hide_index=True)
  else:
    st.info("현재 등록된 상품이 없습니다.")

with tab2:
  st.subheader("신규 트래킹 상품 추가")
  st.write(
      "상품 정보 및 각 쇼핑몰 ID, Surcharge가 포함된 공홈 정가(MSRP)를"
      " 입력하세요."
  )

  with st.form("add_product_form", clear_on_submit=True):
    new_sku = st.text_input(
        "상품명 / SKU", placeholder="예: Ubiquiti UniFi Express 7"
    )
    new_msrp = st.number_input(
        "Surcharge 포함 공홈 정가 (MSRP USD $)",
        min_value=0.0,
        value=199.0,
        step=1.0,
    )
    new_bh = st.text_input("B&H Product Code (선택)", placeholder="예: UBU7PRO")
    new_adorama = st.text_input(
        "Adorama SKU (선택)", placeholder="예: UBQU7PRO"
    )
    new_asin = st.text_input(
        "Amazon ASIN (선택)", placeholder="예: B0CWLKD9RP"
    )
    new_naver_id = st.text_input(
        "네이버 스마트스토어 상품번호 (선택)", placeholder="예: 10293848"
    )

    submitted = st.form_submit_button("➕ 에어테이블에 신규 상품 등록")

    if submitted:
      if not new_sku or new_msrp <= 0:
        st.error("SKU와 MSRP 정가는 필수 입력 항목입니다!")
      else:
        new_record_data = {
            "SKU": new_sku.strip(),
            "MSRP_USD": float(new_msrp),
            "Exchange_Rate": current_rate,
        }
        if new_bh:
          new_record_data["BH_ID"] = new_bh.strip()
        if new_adorama:
          new_record_data["ADORAMA_ID"] = new_adorama.strip()
        if new_asin:
          new_record_data["ASIN"] = new_asin.strip().upper()
        if new_naver_id:
          new_record_data["Naver_Product_No"] = new_naver_id.strip()

        try:
          table.create(new_record_data)
          st.success(f"🎉 [{new_sku}] 상품이 추가되었습니다!")
        except Exception as e:
          st.error(f"에어테이블 추가 중 오류 발생: {e}")
