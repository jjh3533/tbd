import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape as html_escape
import json
import re
import threading
import time
from pathlib import Path

from bs4 import BeautifulSoup
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
    initial_sidebar_state="expanded",
)

# 시크릿은 하드코딩하지 않고 config.py(환경변수 / Streamlit Secrets)에서 가져옵니다.
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


def logo_data_uri(theme_name: str) -> str:
  logo_data = LOGO_LIGHT if theme_name == "dark" else LOGO_DARK
  return f"data:image/svg+xml;base64,{logo_data}" if logo_data else ""


def inject_css(theme_name: str) -> None:
  t = THEMES[theme_name]

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

      /* Streamlit 자체 스타일시트가 [data-testid="stMarkdownContainer"] 등
         구체적인 엘리먼트에 직접 font-family: "Source Sans"를 걸어두기 때문에,
         html/body에만 지정하면 상속 우선순위에서 밀려 적용되지 않음.
         실제로 텍스트가 렌더링되는 컨테이너들을 전부 명시적으로 targeted. */
      html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea,
      [data-testid="stMarkdownContainer"],
      [data-testid="stMarkdownContainer"] *,
      [data-testid="stMetricValue"], [data-testid="stMetricLabel"],
      [data-testid="stMetricDelta"], [data-testid="stCaptionContainer"],
      [data-testid="stCaptionContainer"] *,
      [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
      [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
      [data-testid="stSelectbox"], [data-testid="stSelectbox"] *,
      [data-testid="stSidebar"] *,
      table.uic-table, table.uic-table * {{
          font-family: 'UI Sans', Inter, -apple-system, BlinkMacSystemFont,
              "Segoe UI", Lato, Arial, sans-serif !important;
      }}
      /* 위 규칙이 사이드바 접기 화살표 등 Material 아이콘 엘리먼트까지
         덮어써서, 리게처(ligature)로 그려져야 할 아이콘이
         "keyboard_double_arrow_left" 같은 글자 그대로 보이는 문제가 있었음.
         아이콘 폰트를 명시적으로 되돌림 (같은 특정도라 순서상 이 규칙이 이김). */
      [data-testid="stIconMaterial"] {{
          font-family: "Material Symbols Rounded", "Material Icons" !important;
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
          justify-content: flex-start;
          padding: 10px 4px 20px 4px;
          margin-bottom: 6px;
          border-bottom: 1px solid {t['border']};
      }}
      .uic-logo-wrap img {{ height: 44px; width: auto; display: block; }}
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
      [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
          color: {t['accent']} !important;
          font-weight: 700 !important;
      }}
      [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) * {{
          color: {t['accent']} !important;
          font-weight: 700 !important;
      }}
      /* 라디오 원형 아이콘만 숨김. 실제 배포된 페이지의 DOM을 직접 열어
         구조를 확인해보니 label > div > div > div(첫번째, 16x16,
         border-radius:50%)가 원형 아이콘이고, 그 형제인 두번째 div
         (stMarkdownContainer)가 텍스트였음. 정확히 그 위치만 숨김. */
      [data-testid="stSidebar"] div[role="radiogroup"] label > div > div > div:first-child {{
          display: none;
      }}

      /* ---------- 상단 헤더 바 ---------- */
      .uic-topbar {{
          position: relative;
          padding: 8px 90px 20px 4px;
          margin-bottom: 20px;
      }}
      .uic-topbar-title {{
          font-size: 84px;
          font-weight: 900;
          letter-spacing: -2px;
          line-height: 1.05;
          margin: 0;
          text-align: left;
      }}
      .uic-badge {{
          position: absolute;
          top: 4px;
          right: 4px;
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

      /* ---------- 커스텀 테이블 (Site Manager 리스트 뷰 스타일) ---------- */
      /* 라운드 코너를 담당하는 바깥 wrap(overflow:hidden만 사용)과, 가로
         스크롤을 담당하는 안쪽 scroll div를 분리했음. 이전에는 한 엘리먼트에
         overflow-x:auto + overflow-y:hidden을 같이 걸어뒀는데, 이 조합에서
         일부 브라우저가 border-radius 클리핑을 마지막 행 쪽에서 제대로 안 하는
         이슈가 있어서 표 하단이 둥근 모서리 밖으로 살짝 튀어나와 보였음. */
      .uic-table-wrap {{
          background-color: {t['surface']};
          border: 1px solid {t['border']};
          border-radius: 12px;
          overflow: hidden;
          margin-top: 4px;
      }}
      .uic-table-scroll {{
          overflow-x: auto;
      }}
      table.uic-table {{
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
      }}
      table.uic-table thead th {{
          text-align: center;
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.4px;
          color: {t['text_secondary']};
          background-color: {t['bg_secondary']};
          padding: 10px 14px;
          border-bottom: 1px solid {t['border']};
          white-space: nowrap;
      }}
      table.uic-table tbody td {{
          padding: 10px 14px;
          border-bottom: 1px solid {t['border']};
          white-space: nowrap;
          text-align: center;
          vertical-align: middle;
          line-height: 1.4;
          box-sizing: border-box;
      }}
      table.uic-table tbody tr:last-child td {{ border-bottom: none; }}
      table.uic-table tbody tr:hover {{ background-color: {t['surface_tint']}; }}
      table.uic-table td.uic-sku {{ font-weight: 700; text-align: left; }}
      table.uic-table td a {{ color: inherit; text-decoration: none; }}
      table.uic-table td a:hover {{ text-decoration: underline; }}
      table.uic-table th.uic-divider, table.uic-table td.uic-divider {{
          border-left: 2px solid {t['border']};
      }}
      table.uic-table th.uic-final-price, table.uic-table td.uic-final-price {{
          background-color: {t['accent_soft_bg']};
      }}

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
      .uic-quicklink,
      [data-testid="stSidebar"] a.uic-quicklink {{
          flex: 1;
          text-align: center;
          padding: 8px 4px;
          border-radius: 8px;
          border: 1px solid {t['border']};
          background-color: {t['surface_tint']};
          font-size: 11px;
          font-weight: 600;
          color: {t['text_secondary']} !important;
          text-decoration: none !important;
      }}
      .uic-quicklink:hover,
      [data-testid="stSidebar"] a.uic-quicklink:hover {{
          border-color: {t['accent']};
          color: {t['accent']} !important;
      }}

      /* ---------- 사이드바 하단 동기화 로그 (최대 5줄) ---------- */
      .uic-sync-log {{
          margin-top: 4px;
          padding: 10px 10px;
          border-radius: 8px;
          background-color: {t['surface_tint']};
          border: 1px solid {t['border']};
      }}
      .uic-sync-log-line {{
          font-size: 10.5px;
          color: {t['text_secondary']};
          line-height: 1.5;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
      }}
      .uic-sync-log-more {{
          font-weight: 700;
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
# 2. 백엔드 핵심 함수 (기존 스크래핑/알림 로직 그대로 유지)
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
  """Scrape.do 계정의 남은 크레딧 현황을 조회합니다 (분당 호출 제한이 있어 60초 캐싱)."""
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


# Amazon PDP 플러그인 엔드포인트는 토큰당 동시 요청 1개 제한이 있어 세마포어로 직렬화.
_AMAZON_SEMAPHORE = threading.Semaphore(1)


def _scrapedo_get(target_url, timeout=60, max_retries=1, retry_delay=2.0,
                   try_super_on_failure=True, force_super=False):
  """Scrape.do 요청 공용 래퍼 (재시도 + 비용 절감 escalation 포함)."""
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
  """B&H Specs의 'Packaging Info > Package Weight' 행에서 배송 패키지 무게를 kg로 추출."""
  label_pattern = re.compile(r"package\s*weight", re.IGNORECASE)
  weight_pattern = re.compile(r"([\d.]+)\s*(kg|lbs|lb|oz|g)\b", re.IGNORECASE)

  for row in soup.find_all("tr"):
    cells = row.find_all(["td", "th"])
    if len(cells) < 2:
      continue
    if label_pattern.search(cells[0].get_text(strip=True)):
      match = weight_pattern.search(cells[1].get_text(strip=True))
      if match:
        value, unit = float(match.group(1)), match.group(2).lower()
        return round(value * _WEIGHT_UNIT_TO_KG.get(unit, 1.0), 3)

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

  clean_id = str(bh_id).strip().upper()
  target_url = f"https://www.bhphotovideo.com/c/product/{clean_id}/"

  try:
    res = _scrapedo_get(target_url, force_super=True)
    if res is None:
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
  """워커 스레드에서 실행되므로 st.* 호출 없이 로그 문자열만 만들어 반환합니다."""
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

  bh_weight_kg = bh_data.get("weight_kg") if bh_data else None
  if bh_weight_kg is not None:
    update_data["Weight_KG"] = bh_weight_kg

  try:
    table.update(record_id, update_data)
  except Exception:
    pass

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

  with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [
        executor.submit(process_single_record, r, current_rate)
        for r in records
    ]
    for future in as_completed(futures):
      log_line, res = future.result()
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


def safe_fetch_records():
  """Airtable 호출이 실패해도(토큰 만료/권한 부족/네트워크 오류) 대시보드 전체가
  죽지 않고, 원인을 바로 알 수 있게 에러 메시지를 보여준 뒤 빈 목록으로 계속 진행."""
  try:
    return table.all()
  except requests.exceptions.HTTPError as e:
    status = e.response.status_code if e.response is not None else "?"
    if status == 401:
      hint = "AIRTABLE_API_TOKEN이 만료/무효합니다. Streamlit Secrets에 새 Personal Access Token을 등록하세요."
    elif status == 403:
      hint = (
          "토큰에 이 Base('UniFi Supply')에 대한 접근 권한 또는"
          " data.records:read/write, schema.bases:read 스코프가 없습니다."
      )
    elif status == 404:
      hint = "Base ID 또는 Table 이름(Products)이 올바른지 확인하세요."
    elif status == 429:
      hint = "Airtable API 요청 한도를 초과했습니다. 잠시 후 다시 시도하세요."
    else:
      hint = "Airtable API 호출 중 오류가 발생했습니다."
    st.error(f"⚠️ Airtable 연결 실패 (HTTP {status}): {hint}")
    return []
  except Exception as e:
    st.error(f"⚠️ Airtable 연결 실패: {e}")
    return []


# ==========================================
# 3. UI 보조 함수
# ==========================================
class _CappedSidebarLog:
  """사이드바 하단 로그 슬롯에 최대 N줄만 표시하는 run_tbd_tracker()용 래퍼.

  run_tbd_tracker()는 여러 줄을 log_container.write(msg)로 계속 호출하는데,
  좁은 사이드바에 전부 다 찍으면 상품 수가 늘어날수록 계속 길어지므로
  처음 N개만 보여주고 나머지는 개수만 요약합니다.
  """

  def __init__(self, slot, limit=5):
    self.slot = slot
    self.limit = limit
    self.lines = []
    self.total = 0

  def write(self, msg):
    self.total += 1
    if len(self.lines) < self.limit:
      self.lines.append(str(msg))
    rows = "".join(
        f'<div class="uic-sync-log-line">{html_escape(l)}</div>'
        for l in self.lines
    )
    if self.total > self.limit:
      rows += (
          f'<div class="uic-sync-log-line uic-sync-log-more">'
          f'…외 {self.total - self.limit}건 처리 중</div>'
      )
    self.slot.markdown(
        f'<div class="uic-sync-log">{rows}</div>', unsafe_allow_html=True
    )


_COLOR_KEY_GOOD = "accent"    # MSRP보다 저렴
_COLOR_KEY_SAME = "success"   # MSRP와 동일
_COLOR_KEY_BAD = "danger"     # 가격정보 없음 / MSRP보다 비쌈


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


def render_products_table(records, theme_name, show_category=True):
  """Adorama / Amazon / B&H 가격, Best Price(클릭 시 최저가 판매처로 이동),
  판매가격/최종가격/수익까지 보여주는 Site Manager 스타일 테이블."""
  if not records:
    st.info("등록된 상품이 없습니다.")
    return

  t = THEMES[theme_name]

  columns = ["SKU / Model"]
  if show_category:
    columns.append("Category")
  columns += [
      "Naver ID", "UniFi Store ($)", "B&H ($)", "Adorama ($)", "Amazon ($)",
      "Best Price ($)", "Status", "판매가격", "최종가격", "수익",
  ]
  final_price_col = "최종가격"

  rows_html = []
  for r in records:
    f = r["fields"]
    sku = f.get("SKU", "-")
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

    if best_usd <= 0:
      color_key = _COLOR_KEY_BAD
    elif round(best_usd, 2) < round(msrp, 2):
      color_key = _COLOR_KEY_GOOD
    elif round(best_usd, 2) == round(msrp, 2):
      color_key = _COLOR_KEY_SAME
    else:
      color_key = _COLOR_KEY_BAD
    best_color = t[color_key]

    status_html = (
        '<span class="uic-pill ok">Active</span>'
        if is_active
        else '<span class="uic-pill bad">Out of Stock</span>'
    )
    cat_html = f'<span class="uic-pill cat">{html_escape(category)}</span>'

    cell_values = {
        "SKU / Model": html_escape(sku),
        "Category": cat_html,
        "Naver ID": html_escape(str(f.get("Naver_Product_No", "-"))),
        "UniFi Store ($)": fmt_usd(msrp),
        "B&H ($)": fmt_usd(bh_usd),
        "Adorama ($)": fmt_usd(adorama_usd),
        "Amazon ($)": fmt_usd(amazon_usd),
        "Best Price ($)": fmt_usd(best_usd),
        "Status": status_html,
        "판매가격": fmt_krw(f.get("판매금액", 0)),
        "최종가격": fmt_krw(f.get("최종가격", 0)),
        "수익": fmt_krw(f.get("수익", 0)),
    }
    cell_links = {
        "B&H ($)": bh_url,
        "Adorama ($)": adorama_url,
        "Amazon ($)": amazon_url,
        "Best Price ($)": best_price_url,
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
      if col == "Best Price ($)":
        style = (
            f' style="color:{best_color};'
            f' background-color:{_rgba_from_hex(best_color, 0.14)};'
            ' font-weight:700;"'
        )

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

  table_html = f"""
  <div class="uic-table-wrap">
    <div class="uic-table-scroll">
      <table class="uic-table">
        <thead><tr>{''.join(thead_cells)}</tr></thead>
        <tbody>{''.join(rows_html)}</tbody>
      </table>
    </div>
  </div>
  """
  st.markdown(table_html, unsafe_allow_html=True)


def render_sidebar():
  # 테마를 세션스테이트에서 직접 읽어와 로고를 고름. (이전에는 inject_css()가
  # 세션스테이트에 로고를 저장해두고 render_sidebar()가 그걸 읽었는데,
  # render_sidebar()가 inject_css()보다 먼저 호출되다 보니 매 세션 첫 로드 때는
  # 항상 "한 런(run) 뒤처진" 빈 값을 읽어서 로고 대신 텍스트만 보이는 버그가 있었음.)
  logo_uri = logo_data_uri(st.session_state.get("theme", "light"))
  st.sidebar.markdown(
      f"""
      <div class="uic-logo-wrap">
          {'<img src="' + logo_uri + '" alt="UniFi Supply" />' if logo_uri else '⚡ UniFi Supply'}
      </div>
      """,
      unsafe_allow_html=True,
  )

  sync_clicked = st.sidebar.button(
      "⚡ Sync Retailers Now", type="primary", use_container_width=True,
      help="상품 1개당 Adorama+Amazon+B&H 합쳐 보통 약 12크레딧, 봇 차단이"
      " 걸리면 최대 약 22크레딧까지 소모될 수 있습니다.",
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

  # 동기화 실행 로그: 메뉴바 제일 하단에 최대 5줄만 표시.
  # (버튼은 로고 바로 아래 있지만, 이 슬롯은 사이드바에서 제일 마지막에
  # 생성되므로 화면상 항상 맨 아래에 위치함 — 위젯 선언 순서 = 렌더링 순서)
  log_slot = st.sidebar.empty()
  if sync_clicked:
    capped_log = _CappedSidebarLog(log_slot, limit=5)
    with st.spinner("Adorama / Amazon / B&H 동기화 중..."):
      count = run_tbd_tracker(capped_log)
    log_slot.success(f"⚡ 동기화 완료 ({count}건 갱신)")
    st.rerun()

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

# 타이틀은 영문으로 표기 (카테고리명은 이미 영문이라 그대로 사용).
page_title = (
    "Register Product"
    if is_register_page
    else ("Main Dashboard" if is_dashboard else active_category)
)

st.markdown(
    f"""
    <div class="uic-topbar">
        <div class="uic-topbar-title">{page_title}</div>
        <div class="uic-badge">System Active</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not is_register_page:
  scrapedo_usage = get_scrapedo_usage()

  # Sync 버튼은 사이드바(로고 바로 아래)로 이동했습니다.
  m1, m2 = st.columns([1, 1])
  with m1:
    st.metric(label="USD / KRW", value=f"₩ {current_rate:,}")
  with m2:
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

  records = safe_fetch_records()
  theme_now = st.session_state.get("theme", "light")

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
    st.markdown("##### 카테고리별 현황")
    st.caption("카테고리별 상품 수예요. 세부 가격은 왼쪽 메뉴에서 카테고리를 선택하면 볼 수 있어요.")

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

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown("##### 전체 상품")
    render_products_table(records, theme_now, show_category=True)

  else:
    cat_records = [r for r in records if r["fields"].get("Category") == active_category]
    cat_in_stock = sum(1 for r in cat_records if r["fields"].get("In_Stock"))

    c1, c2, c3 = st.columns(3)
    render_metric_card(c1, "상품 수", f"{len(cat_records)}")
    render_metric_card(c2, "판매 가능", f"{cat_in_stock}", "success")
    render_metric_card(c3, "품절", f"{len(cat_records) - cat_in_stock}", "danger")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    render_products_table(cat_records, theme_now, show_category=False)

else:
  st.markdown("##### 신규 상품 등록")
  st.caption(
      "모델명과 MSRP(램 서차지 포함)를 입력하면 Adorama / Amazon / B&H 자동"
      " 모니터링이 시작됩니다."
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
      new_category = st.selectbox("Category", CATEGORIES)

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
            "Category": new_category,
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
