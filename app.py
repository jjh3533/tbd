import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
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
    initial_sidebar_state="expanded",
)

AIRTABLE_API_TOKEN = "patGCAx3PVLC76hji.998b00597d0a3751e2151d0f1d1e6ef3f2c9790b0ff9686929d4b353cb24c418"
AIRTABLE_BASE_ID = "apphI9EUz746dP0Ye"
AIRTABLE_TABLE_NAME = "Products"

SCRAPERAPI_KEY = "643a1d003d0287a250d8cff2f6016159"

TELEGRAM_TOKEN = "8997002649:AAFku9xJ3fKAEq8yaqE8vQAlu8R34vqIwjw"
TELEGRAM_CHAT_ID = "7729393976"

api = Api(AIRTABLE_API_TOKEN)
table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

# 바로가기 링크 (메인 도메인)
QUICK_LINKS = {
    "Airtable": "https://airtable.com",
    "Scrape.do": "https://scrape.do",
    "GitHub": "https://github.com",
}

# UniFi Store 카테고리 (What's New 제외, Airtable Category 필드와 동일)
CATEGORIES = [
    "Cloud Gateways",
    "Switching",
    "WiFi",
    "Physical Security",
    "Door Access",
    "Integrations",
    "Advanced Hosting",
    "Accessories",
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
        "shadow": "0 1px 2px rgba(0, 0, 0, 0.4)",
    },
}

ASSETS_DIR = Path(__file__).parent / "assets"


@st.cache_data(show_spinner=False)
def _b64(filename: str) -> str:
    path = ASSETS_DIR / filename
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


FONT_REGULAR = _b64("ui-sans-v9-regular.woff2")
FONT_MEDIUM = _b64("ui-sans-v9-medium.woff2")
FONT_BOLD = _b64("ui-sans-v9-bold.woff2")
FONT_BLACK = _b64("ui-sans-v9-black.woff2")
LOGO_DARK = _b64("unifi_supply_logo.svg")  # 어두운 로고 (라이트 배경용)
LOGO_LIGHT = _b64("unifi_supply_logo_white.svg")  # 밝은 로고 (다크 배경용)


def inject_css(theme_name: str) -> None:
  t = THEMES[theme_name]
  logo_data = LOGO_LIGHT if theme_name == "dark" else LOGO_DARK

  st.session_state["_logo_data_uri"] = (
      f"data:image/svg+xml;base64,{logo_data}" if logo_data else ""
  )

  st.markdown(
      f"""
      <style>
      @font-face {{
          font-family: 'UI Sans';
          src: url(data:font/woff2;base64,{FONT_REGULAR}) format('woff2');
          font-weight: 400;
          font-display: swap;
      }}
      @font-face {{
          font-family: 'UI Sans';
          src: url(data:font/woff2;base64,{FONT_MEDIUM}) format('woff2');
          font-weight: 500;
          font-display: swap;
      }}
      @font-face {{
          font-family: 'UI Sans';
          src: url(data:font/woff2;base64,{FONT_BOLD}) format('woff2');
          font-weight: 700;
          font-display: swap;
      }}
      @font-face {{
          font-family: 'UI Sans';
          src: url(data:font/woff2;base64,{FONT_BLACK}) format('woff2');
          font-weight: 900;
          font-display: swap;
      }}

      html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea {{
          font-family: 'UI Sans', Inter, -apple-system, BlinkMacSystemFont,
              "Segoe UI", Lato, Arial, sans-serif !important;
      }}

      .stApp {{
          background-color: {t['bg']};
          color: {t['text']};
      }}

      [data-testid="stSidebar"] {{
          background-color: {t['bg']};
          border-right: 1px solid {t['border']};
      }}
      [data-testid="stSidebar"] > div:first-child {{
          padding-top: 1.25rem;
      }}
      [data-testid="stHeader"] {{
          background-color: transparent;
      }}
      [data-testid="stAppViewBlockContainer"] {{
          padding-top: 1.5rem;
      }}

      h1, h2, h3, h4, h5, p, span, div, label {{
          color: {t['text']};
      }}

      /* ---------- 사이드바 로고 ---------- */
      .uic-logo-wrap {{
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 4px 4px 18px 4px;
          margin-bottom: 6px;
          border-bottom: 1px solid {t['border']};
      }}
      .uic-logo-wrap img {{ height: 26px; }}
      .uic-logo-text {{
          font-size: 15px;
          font-weight: 700;
          letter-spacing: -0.2px;
          line-height: 1.1;
      }}
      .uic-logo-sub {{
          font-size: 11px;
          color: {t['text_secondary']};
          font-weight: 500;
      }}

      /* ---------- 사이드바 섹션 라벨 ---------- */
      .uic-nav-label {{
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.6px;
          color: {t['text_secondary']};
          margin: 14px 4px 6px 4px;
      }}

      /* radio를 Site Manager 스타일의 네비 리스트로 재구성 */
      [data-testid="stSidebar"] div[role="radiogroup"] {{
          gap: 1px;
      }}
      [data-testid="stSidebar"] div[role="radiogroup"] label {{
          padding: 7px 10px;
          border-radius: 8px;
          width: 100%;
          font-size: 13.5px;
          font-weight: 500;
      }}
      [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
          background-color: {t['surface_tint']};
      }}
      [data-testid="stSidebar"] div[role="radiogroup"] input:checked + div {{
          color: {t['accent']} !important;
          font-weight: 700 !important;
      }}
      [data-testid="stSidebar"] div[role="radiogroup"] label div:first-child {{
          display: none;
      }}

      /* ---------- 상단 헤더 바 ---------- */
      .uic-topbar {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          background-color: {t['bg_secondary']};
          border: 1px solid {t['border']};
          border-radius: 12px;
          padding: 18px 24px;
          margin-bottom: 20px;
      }}
      .uic-topbar-title {{
          font-size: 21px;
          font-weight: 700;
          letter-spacing: -0.3px;
          margin: 0;
      }}
      .uic-topbar-sub {{
          font-size: 12.5px;
          color: {t['text_secondary']};
          margin-top: 2px;
          font-weight: 500;
      }}
      .uic-badge {{
          background-color: {t['accent_soft_bg']};
          color: {t['accent']};
          font-size: 11px;
          font-weight: 700;
          padding: 4px 10px;
          border-radius: 20px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
      }}

      /* ---------- 메트릭 카드 ---------- */
      .uic-card {{
          background-color: {t['surface']};
          border: 1px solid {t['border']};
          border-radius: 12px;
          padding: 16px 18px;
          box-shadow: {t['shadow']};
          height: 100%;
      }}
      .uic-card-label {{
          font-size: 11.5px;
          font-weight: 600;
          color: {t['text_secondary']};
          text-transform: uppercase;
          letter-spacing: 0.4px;
          margin-bottom: 6px;
      }}
      .uic-card-value {{
          font-size: 26px;
          font-weight: 900;
          letter-spacing: -0.5px;
      }}
      .uic-card-value.accent {{ color: {t['accent']}; }}
      .uic-card-value.success {{ color: {t['success']}; }}
      .uic-card-value.danger {{ color: {t['danger']}; }}

      /* ---------- 카테고리 카드(대시보드 클릭 진입) ---------- */
      .uic-cat-card {{
          background-color: {t['surface']};
          border: 1px solid {t['border']};
          border-radius: 12px;
          padding: 14px 16px;
          margin-bottom: 10px;
      }}
      .uic-cat-card-title {{
          font-size: 14px;
          font-weight: 700;
      }}
      .uic-cat-card-count {{
          font-size: 12px;
          color: {t['text_secondary']};
          font-weight: 500;
      }}

      div[data-testid="stButton"] > button {{
          background-color: {t['accent']} !important;
          color: #ffffff !important;
          border: none !important;
          border-radius: 8px !important;
          font-weight: 700 !important;
          font-size: 13px !important;
          padding: 8px 16px !important;
          transition: all 0.15s ease-in-out !important;
      }}
      div[data-testid="stButton"] > button:hover {{
          filter: brightness(1.08);
      }}
      div[data-testid="stButton"] > button[kind="secondary"] {{
          background-color: {t['surface']} !important;
          color: {t['text']} !important;
          border: 1px solid {t['border']} !important;
      }}

      /* ---------- 커스텀 테이블 (Site Manager 리스트 뷰 스타일) ---------- */
      .uic-table-wrap {{
          background-color: {t['surface']};
          border: 1px solid {t['border']};
          border-radius: 12px;
          overflow: hidden;
          margin-top: 4px;
      }}
      table.uic-table {{
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
      }}
      table.uic-table thead th {{
          text-align: left;
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.4px;
          color: {t['text_secondary']};
          background-color: {t['bg_secondary']};
          padding: 10px 16px;
          border-bottom: 1px solid {t['border']};
          white-space: nowrap;
      }}
      table.uic-table tbody td {{
          padding: 11px 16px;
          border-bottom: 1px solid {t['border']};
          white-space: nowrap;
      }}
      table.uic-table tbody tr:last-child td {{ border-bottom: none; }}
      table.uic-table tbody tr:hover {{ background-color: {t['surface_tint']}; }}
      table.uic-table td.uic-num {{ text-align: right; font-variant-numeric: tabular-nums; }}
      table.uic-table td.uic-sku {{ font-weight: 700; }}

      .uic-pill {{
          display: inline-block;
          padding: 3px 10px;
          border-radius: 20px;
          font-size: 11.5px;
          font-weight: 700;
      }}
      .uic-pill.ok {{ background-color: {t['success_soft_bg']}; color: {t['success']}; }}
      .uic-pill.bad {{ background-color: {t['danger_soft_bg']}; color: {t['danger']}; }}
      .uic-pill.cat {{ background-color: {t['accent_soft_bg']}; color: {t['accent']}; }}

      /* ---------- 사이드바 바로가기 아이콘 ---------- */
      .uic-quicklinks {{
          display: flex;
          gap: 8px;
          margin-top: 6px;
      }}
      .uic-quicklink {{
          flex: 1;
          text-align: center;
          padding: 8px 4px;
          border-radius: 8px;
          border: 1px solid {t['border']};
          font-size: 11px;
          font-weight: 700;
          color: {t['text_secondary']};
          text-decoration: none;
      }}
      .uic-quicklink:hover {{
          border-color: {t['accent']};
          color: {t['accent']};
      }}

      [data-testid="stMetricValue"] {{
          font-size: 22px !important;
          font-weight: 900 !important;
          color: {t['accent']} !important;
      }}
      hr {{ border-color: {t['border']} !important; }}
      </style>
      """,
      unsafe_allow_html=True,
  )


# ==========================================
# 2. 백엔드 핵심 함수 (기존 로직 유지)
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
# 3. UI 보조 함수
# ==========================================
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


def render_metric_card(col, label, value, tone=""):
  with col:
    st.markdown(
        f"""
        <div class="uic-card">
            <div class="uic-card-label">{label}</div>
            <div class="uic-card-value {tone}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_products_table(records, show_category=True):
  if not records:
    st.info("등록된 상품이 없습니다.")
    return

  header_cols = ["SKU / Model"]
  if show_category:
    header_cols.append("Category")
  header_cols += ["MSRP", "Adorama", "Amazon", "Status", "판매가(KRW)", "Naver ID"]

  rows_html = []
  for r in records:
    f = r["fields"]
    sku = f.get("SKU", "-")
    category = f.get("Category") or "미분류"
    in_stock = f.get("In_Stock", False)
    status_html = (
        '<span class="uic-pill ok">Active</span>'
        if in_stock
        else '<span class="uic-pill bad">Out of Stock</span>'
    )
    cat_html = f'<span class="uic-pill cat">{category}</span>'

    cells = [f'<td class="uic-sku">{sku}</td>']
    if show_category:
      cells.append(f"<td>{cat_html}</td>")
    cells += [
        f'<td class="uic-num">{fmt_usd(f.get("MSRP_USD", 0))}</td>',
        f'<td class="uic-num">{fmt_usd(f.get("Adorama_USD", 0))}</td>',
        f'<td class="uic-num">{fmt_usd(f.get("Amazon_USD", 0))}</td>',
        f"<td>{status_html}</td>",
        f'<td class="uic-num">{fmt_krw(f.get("Calculated_Price", 0))}</td>',
        f'<td>{f.get("Naver_Product_No", "-")}</td>',
    ]
    rows_html.append("<tr>" + "".join(cells) + "</tr>")

  table_html = f"""
  <div class="uic-table-wrap">
    <table class="uic-table">
      <thead><tr>{''.join(f"<th>{c}</th>" for c in header_cols)}</tr></thead>
      <tbody>{''.join(rows_html)}</tbody>
    </table>
  </div>
  """
  st.markdown(table_html, unsafe_allow_html=True)


def render_sidebar():
  logo_uri = st.session_state.get("_logo_data_uri", "")
  st.sidebar.markdown(
      f"""
      <div class="uic-logo-wrap">
          {'<img src="' + logo_uri + '" />' if logo_uri else '⚡'}
          <div>
              <div class="uic-logo-text">UniFi Supply</div>
              <div class="uic-logo-sub">Price Monitor</div>
          </div>
      </div>
      """,
      unsafe_allow_html=True,
  )

  st.sidebar.markdown('<div class="uic-nav-label">메뉴</div>', unsafe_allow_html=True)

  nav_options = ["📊 메인 대시보드"] + [f"　{c}" for c in CATEGORIES] + ["➕ 상품 등록"]

  if "nav_choice" not in st.session_state:
    st.session_state.nav_choice = nav_options[0]

  # key를 "nav_choice"로 직접 지정해야, 대시보드의 카테고리 카드 버튼이
  # st.session_state.nav_choice를 바꿔서 이 라디오의 선택값을 그대로 갱신할 수 있음
  # (key와 별개 변수를 쓰면 rerun 후에도 라디오가 이전 선택을 그대로 유지하는 버그가 생김)
  choice = st.sidebar.radio(
      "메뉴",
      nav_options,
      label_visibility="collapsed",
      key="nav_choice",
  )

  st.sidebar.markdown('<div class="uic-nav-label">테마</div>', unsafe_allow_html=True)
  theme_choice = st.sidebar.radio(
      "테마",
      ["Light", "Dark"],
      index=0 if st.session_state.get("theme", "light") == "light" else 1,
      horizontal=True,
      label_visibility="collapsed",
      key="theme_radio",
  )
  st.session_state.theme = theme_choice.lower()

  st.sidebar.markdown('<div class="uic-nav-label">바로가기</div>', unsafe_allow_html=True)
  links_html = '<div class="uic-quicklinks">' + "".join(
      f'<a class="uic-quicklink" href="{url}" target="_blank">{name}</a>'
      for name, url in QUICK_LINKS.items()
  ) + "</div>"
  st.sidebar.markdown(links_html, unsafe_allow_html=True)

  return choice


# ==========================================
# 4. 메인 렌더링
# ==========================================
nav_choice = render_sidebar()
inject_css(st.session_state.get("theme", "light"))

current_rate = get_current_exchange_rate()

is_register_page = nav_choice == "➕ 상품 등록"
is_dashboard = nav_choice == "📊 메인 대시보드"
active_category = None if (is_register_page or is_dashboard) else nav_choice.strip()

page_title = (
    "상품 등록"
    if is_register_page
    else ("메인 대시보드" if is_dashboard else active_category)
)
page_sub = (
    "Adorama / Amazon 신규 모니터링 상품 추가"
    if is_register_page
    else "MSRP 기준 가격 엔진 · Adorama / Amazon 듀얼 가드"
)

top_col1, top_col2 = st.columns([4, 1])
with top_col1:
  st.markdown(
      f"""
      <div class="uic-topbar">
          <div>
              <div class="uic-topbar-title">⚡ {page_title}</div>
              <div class="uic-topbar-sub">{page_sub}</div>
          </div>
          <div class="uic-badge">System Active</div>
      </div>
      """,
      unsafe_allow_html=True,
  )

if not is_register_page:
  m1, m2, m3 = st.columns([1.3, 1, 2])
  with m1:
    st.metric(label="USD / KRW", value=f"₩ {current_rate:,}")
  with m3:
    if st.button("⚡ Sync Retailers Now", type="primary", use_container_width=True):
      with st.status("Executing Multi-thread Sync...", expanded=True) as status:
        count = run_tbd_tracker(status)
        status.update(
            label=f"Sync Finished ({count} items updated)",
            state="complete",
            expanded=False,
        )
      st.success("AirTable and Telegram alerts updated.")
      st.rerun()

  st.divider()

  records = table.all()

  if is_dashboard:
    total = len(records)
    in_stock = sum(1 for r in records if r["fields"].get("In_Stock"))
    out_stock = total - in_stock
    cat_counts = {c: 0 for c in CATEGORIES}
    for r in records:
      c = r["fields"].get("Category")
      if c in cat_counts:
        cat_counts[c] += 1

    c1, c2, c3, c4 = st.columns(4)
    render_metric_card(c1, "전체 상품", f"{total}")
    render_metric_card(c2, "판매 가능 (Active)", f"{in_stock}", "success")
    render_metric_card(c3, "품절 (Out of Stock)", f"{out_stock}", "danger")
    render_metric_card(c4, "카테고리", f"{len([c for c in cat_counts.values() if c > 0])}", "accent")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("##### 카테고리별 보기")
    st.caption("카테고리를 클릭하면 해당 카테고리의 상품/가격만 모아볼 수 있어요.")

    cat_cols = st.columns(4)
    for idx, cat in enumerate(CATEGORIES):
      with cat_cols[idx % 4]:
        st.markdown(
            f"""
            <div class="uic-cat-card">
                <div class="uic-cat-card-title">{cat}</div>
                <div class="uic-cat-card-count">{cat_counts[cat]}개 상품</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("보기", key=f"catbtn_{cat}", use_container_width=True):
          st.session_state.nav_choice = f"　{cat}"
          st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown("##### 전체 상품")
    render_products_table(records, show_category=True)

  else:
    cat_records = [r for r in records if r["fields"].get("Category") == active_category]
    cat_in_stock = sum(1 for r in cat_records if r["fields"].get("In_Stock"))

    c1, c2, c3 = st.columns(3)
    render_metric_card(c1, "상품 수", f"{len(cat_records)}")
    render_metric_card(c2, "판매 가능", f"{cat_in_stock}", "success")
    render_metric_card(c3, "품절", f"{len(cat_records) - cat_in_stock}", "danger")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    render_products_table(cat_records, show_category=False)

else:
  st.markdown("##### 신규 상품 등록")
  st.caption("모델명과 MSRP(램 서차지 포함)를 입력하면 자동 모니터링이 시작됩니다.")

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
      new_category = st.selectbox("Category", CATEGORIES)

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
            "Category": new_category,
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
