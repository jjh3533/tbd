from concurrent.futures import ThreadPoolExecutor, as_completed
import json
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
    page_title="UniFi Supply Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
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


def process_single_record(r, current_rate, log_container):
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

  log_container.write(
      f"✅ [{sku}] Complete | Ado:${adorama_price} / Amz:${amazon_price}"
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
      new_calc_price = updated_record["fields"].get("Calculated_Price", 0)
      available_sources = ", ".join(valid_retailers)
      status_change = (
          "IN_STOCK",
          f"🟢 **[BACK IN STOCK]** *{sku}*\n• Valid Retailers:"
          f" **{available_sources}**\n• Target Price (MSRP Based):"
          f" **`{new_calc_price:,}원`**",
      )

  return status_change


def run_tbd_tracker(log_container):
  log_container.write(
      "⚡ [UI.com Engine] Adorama & Amazon Dual-Channel Syncing..."
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

  with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(process_single_record, r, current_rate, log_container)
        for r in records
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
            <div class="uic-subtitle">MSRP-Based Price Engine & Adorama/Amazon Dual Guard</div>
        </div>
        <div class="uic-badge">SYSTEM ACTIVE</div>
    </div>
""",
    unsafe_allow_html=True,
)

current_rate = get_current_exchange_rate()

col_m1, col_m2 = st.columns([1, 4])
with col_m1:
  st.metric(label="USD / KRW Exchange Rate", value=f"₩ {current_rate:,}")

st.divider()

tab1, tab2 = st.tabs(["📦 Inventory & Price Grid", "➕ Register New Product"])

with tab1:
  col_t1, col_t2 = st.columns([3, 1])
  with col_t1:
    st.markdown("### Managed Products")
  with col_t2:
    if st.button(
        "⚡ Sync Retailers Now", type="primary", use_container_width=True
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
    data_list = []
    for r in records:
      f = r["fields"]
      data_list.append({
          "SKU / Model": f.get("SKU", "-"),
          "MSRP Base ($)": f"${f.get('MSRP_USD', 0.0):,.2f}",
          "Adorama ($)": f"${f.get('Adorama_USD', 0.0):,.2f}",
          "Amazon ($)": f"${f.get('Amazon_USD', 0.0):,.2f}",
          "Status": (
              "🟢 Active (MSRP Valid)"
              if f.get("In_Stock")
              else "🔴 Out of Stock (Above MSRP)"
          ),
          "Calculated KRW": f"₩ {f.get('Calculated_Price', 0):,}",
          "Naver ID": f.get("Naver_Product_No", "-"),
      })

    df = pd.DataFrame(data_list)
    st.dataframe(df, use_container_width=True, hide_index=True)
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
        if new_naver_id:
          new_record_data["Naver_Product_No"] = new_naver_id.strip()

        try:
          table.create(new_record_data)
          st.success(f"⚡ [{new_sku}] successfully added to monitoring matrix!")
        except Exception as e:
          st.error(f"AirTable Registration Error: {e}")
