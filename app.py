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


def fetch_bh_info(bh_id):
  if not bh_id:
    return None

  clean_id = str(bh_id).strip()
  if not clean_id.endswith("-REG") and clean_id.isdigit():
    clean_id = f"{clean_id}-REG"

  target_url = f"https://www.bhphotovideo.com/c/product/{clean_id}.html"

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
    bh_usd = 0.0
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
          bh_usd = float(price)
          availability = str(offers.get("availability", "")).lower()
          if "outofstock" in availability or "discontinued" in availability:
            in_stock = False
          break
      except Exception:
        pass

    if bh_usd == 0.0:
      price_selectors = [
          '[data-selenium="pricingPrice"]',
          '[data-selenium="price"]',
          'span[class*="price"]',
          ".price_12-4-0",
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

    return {"price": bh_usd, "in_stock": in_stock}
  except Exception:
    return None


def fetch_adorama_info(adorama_id):
  if not adorama_id:
    return None

  clean_id = str(adorama_id).strip().lower()
  target_urls = [
      f"https://www.adorama.com/p/{clean_id}",
      f"https://www.adorama.com/{clean_id}.html",
      f"https://www.adorama.com/l/?searchinfo={clean_id}",
  ]

  for target_url in target_urls:
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
        continue

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

      if adorama_usd > 0:
        return {"price": adorama_usd, "in_stock": in_stock}

    except Exception:
      continue

  return {"price": 0.0, "in_stock": False}


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
      "⚡ [UI.com Engine] JSON-LD Multi-retailer sync running..."
  )
  current_rate = get_current_exchange_rate()
  log_container.write(f"💱 Applied Exchange Rate: ₩{current_rate}")

  records = table.all()
  total_count = len(records)
  log_container.write(f"📦 Active Inventory Records: {total_count}")

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

    log_container.write(f"🔍 Deep Parsing [{sku}]...")

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

    try:
      table.update(record_id, update_data)
    except Exception as e:
      log_container.write(f"⚠️ AirTable Sync Warning ({sku}): {e}")

    updated_count += 1

    if prev_stock != curr_stock:
      if not curr_stock:
        out_of_stock_count += 1
        detail_messages.append(
            f"🔴 **[OUT OF STOCK]** *{sku}*\n• SmartStore ID({naver_id})"
            " Action Required"
        )
      else:
        back_in_stock_count += 1
        updated_record = table.get(record_id)
        new_calc_price = updated_record["fields"].get("Calculated_Price", 0)
        detail_messages.append(
            f"🟢 **[BACK IN STOCK]** *{sku}*\n• Best Source: **{best_source}**"
            f" (${best_price})\n• Target Price: **`{new_calc_price:,}원`**"
        )

    log_container.write(
        f"✅ [{sku}] Complete | B&H:${bh_price} / Ado:${adorama_price} /"
        f" Amz:${amazon_price} ➔ Best:${best_price}"
    )

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
  log_container.write("🎉 UI.com Deep Sync Complete!")
  return updated_count


# ==========================================
# 3. Streamlit UI 구성
# ==========================================

st.markdown(
    """
    <div class="uic-header">
        <div>
            <div class="uic-title">⚡ UniFi Supply Monitor</div>
            <div class="uic-subtitle">Real-time Retailer Arbitrage & MSRP Price Defense Engine</div>
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
      with st.status("Deep Extracting JSON-LD Data...", expanded=True) as status:
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
          "MSRP ($)": f"${f.get('MSRP_USD', 0.0):,.2f}",
          "B&H ($)": f"${f.get('BH_USD', 0.0):,.2f}",
          "Adorama ($)": f"${f.get('Adorama_USD', 0.0):,.2f}",
          "Amazon ($)": f"${f.get('Amazon_USD', 0.0):,.2f}",
          "Best USD ($)": f"${f.get('Best_USD', 0.0):,.2f}",
          "Status": "🟢 Active" if f.get("In_Stock") else "🔴 Out of Stock",
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
      new_bh = st.text_input(
          "B&H Code (Optional)", placeholder="e.g. 1815010-REG"
      )
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
          st.success(f"⚡ [{new_sku}] successfully added to monitoring matrix!")
        except Exception as e:
          st.error(f"AirTable Registration Error: {e}")
