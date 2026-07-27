import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape as html_escape
import json
import re
import threading
import time
from pathlib import Path

from bs4 import BeautifulSoup
from nocodb_client import NocoDBTable
import requests
import streamlit as st
import yfinance as yf

from config import (
    NOCODB_URL,
    NOCODB_API_TOKEN,
    NOCODB_TABLE_ID,
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
table = NocoDBTable(NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID)

# 바로가기 링크 (메인 도메인)
QUICK_LINKS = {
    "NocoDB": NOCODB_URL,
    "Scrape.do": "https://scrape.do",
    "GitHub": "https://github.com",
}

# UniFi Store 카테고리 (What's New 제외, NocoDB Category 필드와 동일)
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
        "warning": "#B25E09",
        "warning_soft_bg": "#FBF0E1",
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
        "warning": "#F0A83C",
        "warning_soft_bg": "#3A2B0F",
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
# TBD Dashboard 워드마크: 배경이 없는 단색 텍스트라 다크 모드에서도 보이도록
# 흰색 버전을 별도로 만들어둠 (unifi_supply_logo 때와 동일한 방식).
LOGO_DARK = _b64("tbd_dashboard.svg")   # 어두운 색 로고 (라이트 배경용)
LOGO_LIGHT = _b64("tbd_dashboard_white.svg")  # 밝은 색 로고 (다크 배경용)


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
      .uic-logo-wrap img {{ height: 45px; width: auto; display: block; }}
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
          font-size: 56px;
          font-weight: 900;
          letter-spacing: -1.3px;
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
      .uic-card-value.warning {{ color: {t['warning']}; }}

      /* ---------- 카테고리 카드(대시보드 클릭 진입) ---------- */
      .uic-cat-card {{
          background-color: {t['surface']};
          border: 1px solid {t['border']};
          border-radius: 12px;
          padding: 14px 16px;
          margin-bottom: 10px;
          transition: border-color 0.15s ease-in-out;
      }}
      .uic-cat-card-title {{
          font-size: 14px;
          font-weight: 700;
          margin-bottom: 6px;
      }}
      .uic-cat-card-count {{
          font-size: 12px;
          color: {t['text_secondary']};
          font-weight: 600;
      }}
      .uic-cat-card-num {{
          font-size: 28px;
          font-weight: 900;
          color: {t['text']};
          letter-spacing: -0.8px;
          margin-right: 5px;
      }}

      /* 카드 전체를 클릭 가능하게: 보이는 카드(div) 위에 투명한 버튼을
         position:absolute로 겹쳐서, 카드 어디를 눌러도 이동하도록 함. */
      div[class*="st-key-catcard_"] {{
          position: relative;
      }}
      div[class*="st-key-catcard_"]:hover .uic-cat-card {{
          border-color: {t['accent']};
      }}
      div[class*="st-key-catcard_"] div[data-testid="stButton"] {{
          position: absolute;
          inset: 0;
          margin: 0;
      }}
      div[class*="st-key-catcard_"] div[data-testid="stButton"] > button {{
          width: 100%;
          height: 100%;
          background: transparent !important;
          border: none !important;
          box-shadow: none !important;
          opacity: 0;
          cursor: pointer;
          padding: 0 !important;
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

      /* ---------- 리테일러별 개별 Sync 버튼 (전체 Sync보다 톤 다운) ---------- */
      div[class*="st-key-retailer_sync_row"] {{
          margin-top: 6px;
          margin-bottom: 10px;
      }}
      div[class*="st-key-retailer_sync_row"] div[data-testid="stButton"] button {{
          background-color: transparent !important;
          color: {t['text_secondary']} !important;
          border: 1px solid {t['border']} !important;
          border-radius: 8px !important;
          font-weight: 600 !important;
          font-size: 11px !important;
          letter-spacing: -0.2px;
          white-space: nowrap !important;
          overflow: hidden;
          text-overflow: ellipsis;
          padding: 7px 2px !important;
          min-width: 0;
      }}
      div[class*="st-key-retailer_sync_row"] div[data-testid="stButton"] button:hover {{
          border-color: {t['accent']} !important;
          color: {t['accent']} !important;
          filter: none;
      }}

      /* ---------- 확인 필요 상품만 재동기화하는 버튼 (경고색으로 구분) ---------- */
      div[class*="st-key-check_needed_sync_row"] {{
          margin-top: 6px;
          margin-bottom: 10px;
      }}
      div[class*="st-key-check_needed_sync_row"] div[data-testid="stButton"] button {{
          background-color: {t['warning']} !important;
          color: #ffffff !important;
          border: none !important;
          border-radius: 8px !important;
          font-weight: 700 !important;
          font-size: 13px !important;
          padding: 8px 16px !important;
          transition: all 0.15s ease-in-out !important;
      }}
      div[class*="st-key-check_needed_sync_row"] div[data-testid="stButton"] button:hover {{
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
      /* 실제 배포 페이지에서 직접 측정해보니 모든 행 높이는 이미 43px로
         동일했음 — "튀어나온" 것처럼 보인 진짜 원인은 표가 가로 스크롤이
         필요할 만큼 넓어서, 브라우저가 예약해두는 가로 스크롤바 높이(~17px)가
         라운드 처리된 wrap 안쪽 맨 아래에 빈 공간처럼 끼어 있었던 것.
         스크롤바를 얇게 커스텀해서 그 여백을 없앰. */
      .uic-table-scroll {{
          overflow-x: auto;
          scrollbar-width: thin;
          scrollbar-color: {t['border']} transparent;
      }}
      .uic-table-scroll::-webkit-scrollbar {{
          height: 6px;
      }}
      .uic-table-scroll::-webkit-scrollbar-track {{
          background: transparent;
      }}
      .uic-table-scroll::-webkit-scrollbar-thumb {{
          background-color: {t['text_secondary']};
          border-radius: 4px;
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
      /* title(=Check_Note)이 붙어있는 뱃지는 Active/Out of Stock이어도
         호버하면 메모가 보이니, 도움말 커서로 힌트를 줌. */
      .uic-pill[title] {{ cursor: help; }}
      .uic-pill.ok {{ background-color: {t['success_soft_bg']}; color: {t['success']}; }}
      .uic-pill.bad {{ background-color: {t['danger_soft_bg']}; color: {t['danger']}; }}
      .uic-pill.check {{ background-color: {t['warning_soft_bg']}; color: {t['warning']}; }}
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

# Scrape.do 대시보드(dashboard.scrape.do)에서 확인한 실제 계정 동시 요청 한도는
# Hobby 플랜 기준 10. Amazon이 항상 1개를 쓰므로 Adorama/B&H 합산 한도를
# 5로 잡아 (5 + 1 = 6) 계정 한도(10)에 여유를 넉넉히 남깁니다. 예전에 9까지
# 밀어붙였다가 Adorama가 대량 502(약 57초 지연 후 실패)를 뱉은 적이 있어서,
# 이번엔 계정 한도에 딱 맞추기보다 여유를 두는 쪽을 택했습니다.
_SCRAPEDO_SEMAPHORE = threading.Semaphore(5)


def _scrapedo_get(target_url, timeout=60, max_retries=1, retry_delay=2.0,
                   try_super_on_failure=True, force_super=False,
                   fast_free_tier=False):
  """Scrape.do 요청 공용 래퍼 (재시도 + 비용 절감 escalation 포함).

  fast_free_tier=True: 무료 티어(super=false)에서 타임아웃/재시도 횟수를
  줄여서 "어차피 막힐 요청"에 오래 매달리지 않고 super 티어로 더 빨리
  넘어가게 합니다. super를 상시로 켜는 것과 달리, 무료 티어에서 성공하는
  건(=차단 안 걸리는 상품) 여전히 정상가로 처리되니 크레딧은 그대로 아낍니다.
  Adorama처럼 무료 티어가 자주/오래 막혀서 502로 시간을 잡아먹는 곳에 사용.
  """
  if force_super:
    tiers = [(True, timeout, max_retries, 15000)]
  else:
    if fast_free_tier:
      free_tier = (False, min(timeout, 10), 0, 5000)
    else:
      free_tier = (False, timeout, max_retries, 15000)
    super_tier = (True, timeout, max_retries, 15000)
    tiers = [free_tier, super_tier] if try_super_on_failure else [free_tier]

  for use_super, tier_timeout, tier_retries, retry_timeout_ms in tiers:
    for attempt in range(tier_retries + 1):
      try:
        with _SCRAPEDO_SEMAPHORE:
          res = requests.get(
              "https://api.scrape.do/",
              params={
                  "token": SCRAPEDO_TOKEN,
                  "url": target_url,
                  "geoCode": "us",
                  "super": "true" if use_super else "false",
                  # 무료 티어는 "빨리 확인하고 다음 티어로 넘어가는" 게
                  # 목적이라 scrape.do 자체 내부 재시도 주기도 짧게 잡음.
                  "retryTimeout": retry_timeout_ms,
              },
              timeout=tier_timeout,
          )
        if res.status_code == 200:
          return res
      except Exception:
        pass
      if attempt < tier_retries:
        time.sleep(retry_delay)
  return None


# 사이트가 요청을 거부/차단했을 때 나타나는 흔한 문구. 200 응답이어도 실제
# 내용이 아니라 이런 인터스티셜/캡차 페이지일 수 있어서, 이걸 감지하면
# "품절"이 아니라 "확인 필요"로 분류합니다.
_BLOCK_KEYWORDS = [
    "pardon our interruption",
    "access denied",
    "are you a robot",
    "unusual traffic",
    "px-captcha",
    "distil_r_captcha",
    "request unsuccessful",
    "reference #",
    "verify you are a human",
    "attention required",
    "checking your browser",
]

_OOS_KEYWORDS = [
    "out of stock",
    "discontinued",
    "sold out",
    "coming soon",
    "notify when available",
    "special order",
    "backordered",
    "pre-order",
    "preorder",
    "no longer available",
]


def fetch_adorama_info(adorama_id):
  if not adorama_id:
    return None

  clean_id = str(adorama_id).strip().lower()
  target_url = f"https://www.adorama.com/{clean_id}.html"

  try:
    # Adorama는 무료 티어가 자주/오래 막혀서(502, ~57초) super로 넘어가는
    # 시간이 병목이었음. super를 상시로 켜는 대신, 무료 티어에서 빨리
    # 포기하고(20초/1회) super로 넘어가도록 fast_free_tier만 켬.
    res = _scrapedo_get(target_url, fast_free_tier=True)
    if res is None:
      # 재시도까지 다 실패 - 진짜 품절인지 사이트가 막았는지 알 수 없으니
      # 0으로 확정 짓지 않고 "확인 필요"로만 표시합니다.
      return {"price": 0.0, "in_stock": False, "status": "check_needed",
              "detail": "request_failed"}

    soup = BeautifulSoup(res.text, "html.parser")
    adorama_usd = 0.0
    in_stock = True
    confirmed_oos = False

    page_text_lower = soup.get_text(" ", strip=True).lower()
    blocked = any(kw in page_text_lower for kw in _BLOCK_KEYWORDS)

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
            confirmed_oos = True
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

    if any(kw in page_text_lower for kw in _OOS_KEYWORDS):
      in_stock = False
      confirmed_oos = True

    if blocked:
      status, detail = "check_needed", "blocked"
    elif confirmed_oos:
      status, detail = "oos", ""
    elif adorama_usd > 0:
      status, detail = "ok", ""
    else:
      # 가격도 못 찾고, 차단 문구도 품절 문구도 없음 - 페이지 구조가 바뀌었을
      # 수 있으니 이것도 확정하지 않고 확인 필요로 남겨둡니다.
      status, detail = "check_needed", "no_price_found"

    return {"price": adorama_usd, "in_stock": in_stock, "status": status,
            "detail": detail}
  except Exception:
    return {"price": 0.0, "in_stock": False, "status": "check_needed",
            "detail": "exception"}


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
          # 플러그인이 정상적으로 페이지를 읽어서 "success"를 준 경우라 가격이
          # 0이어도(=페이지에 가격이 없음) 이건 확정된 정보로 취급합니다.
          status = "ok" if amazon_usd > 0 else "oos"
          return {"price": amazon_usd, "in_stock": amazon_usd > 0,
                  "status": status, "detail": ""}
        # 플러그인 자체가 이 ASIN을 못 읽었다는 뜻 - 품절 확정이 아니라
        # 재조회가 필요한 상태.
        return {"price": 0.0, "in_stock": False, "status": "check_needed",
                "detail": "plugin_failed"}
    except Exception:
      pass
    if attempt < max_retries:
      time.sleep(retry_delay)
  return {"price": 0.0, "in_stock": False, "status": "check_needed",
          "detail": "request_failed"}


_WEIGHT_UNIT_TO_KG = {
    "kg": 1.0,
    "g": 0.001,
    "lb": 0.453592,
    "lbs": 0.453592,
    "oz": 0.0283495,
}


_PACKAGE_CORRECTION_KG = 0.3  # General > Weight(제품 자체 무게)에 더해 패키지 무게를 추정

# "Weight" 단독 라벨(General 섹션의 제품 자체 무게)과 "Package Weight" 라벨을
# 구분해서 찾음. 둘 다 같은 helper(_extract_bh_weight_kg)로 파싱.
_GENERAL_WEIGHT_LABEL_RE = re.compile(r"^\s*weight\s*$", re.IGNORECASE)
_PACKAGE_WEIGHT_LABEL_RE = re.compile(r"package\s*weight", re.IGNORECASE)
_WEIGHT_VALUE_RE = re.compile(r"([\d.]+)\s*(kg|lbs|lb|oz|g)\b", re.IGNORECASE)


def _extract_bh_weight_kg(soup, label_pattern):
  """B&H Specs 표에서 라벨(label_pattern)에 해당하는 무게 값을 kg로 추출."""
  for row in soup.find_all("tr"):
    cells = row.find_all(["td", "th"])
    if len(cells) < 2:
      continue
    if label_pattern.search(cells[0].get_text(strip=True)):
      match = _WEIGHT_VALUE_RE.search(cells[1].get_text(strip=True))
      if match:
        value, unit = float(match.group(1)), match.group(2).lower()
        return round(value * _WEIGHT_UNIT_TO_KG.get(unit, 1.0), 3)

  for dt in soup.find_all("dt"):
    if label_pattern.search(dt.get_text(strip=True)):
      dd = dt.find_next_sibling("dd")
      if dd:
        match = _WEIGHT_VALUE_RE.search(dd.get_text(strip=True))
        if match:
          value, unit = float(match.group(1)), match.group(2).lower()
          return round(value * _WEIGHT_UNIT_TO_KG.get(unit, 1.0), 3)

  return None


def _parse_bh_package_weight_kg(soup):
  """B&H Specs에서 배송 패키지 무게를 kg로 추출.

  우선순위:
  1) 'Packaging Info > Package Weight' - 있으면 이게 실제 패키지 무게 그
     자체라 가장 정확함. 1순위로 사용(보정값 더하지 않음).
  2) 위에서 못 찾았을 때만 General 섹션의 'Weight'(제품 자체 무게, 박스
     미포함)를 대신 사용. 실제 배송 패키지는 이보다 무거우니 보정값
     (_PACKAGE_CORRECTION_KG=0.3kg)을 더해 추정치로 씀.
  """
  package_weight = _extract_bh_weight_kg(soup, _PACKAGE_WEIGHT_LABEL_RE)
  if package_weight is not None:
    return package_weight

  general_weight = _extract_bh_weight_kg(soup, _GENERAL_WEIGHT_LABEL_RE)
  if general_weight is not None:
    return round(general_weight + _PACKAGE_CORRECTION_KG, 3)

  return None


def fetch_bh_info(bh_id):
  if not bh_id:
    return None

  clean_id = str(bh_id).strip().upper()
  target_url = f"https://www.bhphotovideo.com/c/product/{clean_id}/"

  try:
    # B&H는 다른 곳보다 캡차/차단에 자주 걸리는 편이라 재시도를 한 번 더 줍니다.
    res = _scrapedo_get(target_url, force_super=True, max_retries=2)
    if res is None:
      return {"price": 0.0, "in_stock": False, "weight_kg": None,
              "status": "check_needed", "detail": "request_failed"}

    soup = BeautifulSoup(res.text, "html.parser")
    bh_usd = 0.0
    in_stock = True
    confirmed_oos = False

    page_text_lower = soup.get_text(" ", strip=True).lower()
    blocked = any(kw in page_text_lower for kw in _BLOCK_KEYWORDS)

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
            confirmed_oos = True
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

    if any(kw in page_text_lower for kw in _OOS_KEYWORDS):
      in_stock = False
      confirmed_oos = True

    weight_kg = _parse_bh_package_weight_kg(soup)

    if blocked:
      status, detail = "check_needed", "blocked"
    elif confirmed_oos:
      status, detail = "oos", ""
    elif bh_usd > 0:
      status, detail = "ok", ""
    else:
      status, detail = "check_needed", "no_price_found"

    return {"price": bh_usd, "in_stock": in_stock, "weight_kg": weight_kg,
            "status": status, "detail": detail}
  except Exception:
    return {"price": 0.0, "in_stock": False, "weight_kg": None,
            "status": "check_needed", "detail": "exception"}


RETAILER_NAMES = ("Adorama", "Amazon", "B&H")
_RETAILER_PRICE_FIELD = {"Adorama": "Adorama_USD", "Amazon": "Amazon_USD", "B&H": "BH_USD"}
# 사이트별로 "그 사이트 자체에 재고가 있는지"를 따로 저장하는 체크박스 필드.
# 예전엔 가격(>0)으로 재고 여부를 추측했는데, 품절이어도 마지막 확인된 가격이
# 남아있는 경우가 있어서(사이트가 세일가를 보여준 채 품절 표시) 개별
# 리테일러만 Sync할 때 다른 두 곳 상태를 잘못 추측하는 원인이었음. 이제
# fetch_*_info()가 실제로 판단한 in_stock을 이 필드에 그대로 저장해두고,
# 재조회 안 하는 라운드에는 가격 대신 이 필드를 그대로 읽어옵니다.
_RETAILER_STOCK_FIELD = {
    "Adorama": "Adorama_In_Stock", "Amazon": "Amazon_In_Stock", "B&H": "BH_In_Stock",
}


def _stale_retailer_data(name, product_id, fields):
  """이번 라운드에 다시 조회하지 않는 리테일러의 데이터를, NocoDB에 마지막으로
  저장된 값(가격 + 사이트별 재고 체크박스)으로 흉내냅니다. 개별 리테일러만
  Sync할 때도 전체 재고/확인필요 판단(In_Stock, Needs_Check)은 계속 3곳 기준
  으로 일관되게 나오게 하기 위함 - 단, 이 리테일러의 필드들은 이번에 새로
  쓰지 않습니다(밑에서 처리)."""
  if not product_id:
    return None
  price = fields.get(_RETAILER_PRICE_FIELD[name], 0.0) or 0.0
  stock = bool(fields.get(_RETAILER_STOCK_FIELD[name], False))
  check_note = fields.get("Check_Note") or ""
  if f"{name} 확인 필요" in check_note:
    return {"price": price, "in_stock": stock, "status": "check_needed",
            "detail": "stale"}
  return {"price": price, "in_stock": stock, "status": "ok" if stock else "oos",
          "detail": ""}


def process_single_record(r, current_rate, retailers=RETAILER_NAMES):
  """워커 스레드에서 실행되므로 st.* 호출 없이 로그 문자열만 만들어 반환합니다.

  retailers: 이번 라운드에 실제로 재조회할 리테일러 이름 집합/튜플
  ("Adorama", "Amazon", "B&H" 중 일부 또는 전체). 나머지는 NocoDB에 저장된
  마지막 값을 그대로 사용합니다(개별 Sync 버튼용)."""
  record_id = r["id"]
  fields = r["fields"]
  sku = fields.get("SKU", "무명 상품")

  adorama_id = fields.get("ADORAMA_ID")
  asin = fields.get("ASIN")
  bh_id = fields.get("BH_ID")

  msrp_usd = fields.get("MSRP_USD", 0.0)
  prev_stock = fields.get("In_Stock", False)
  prev_needs_check = fields.get("Needs_Check", False)
  naver_id = fields.get("Naver_Product_No", "-")
  max_threshold = msrp_usd if msrp_usd > 0 else 99999.0

  # 이번에 실제로 재조회할 곳만 스레드로 동시에 요청. 실제 네트워크 동시
  # 요청 개수는 _AMAZON_SEMAPHORE(1)와 _SCRAPEDO_SEMAPHORE(5)가 계정 한도
  # (Hobby 플랜 10) 안에서 제한하므로, 안전합니다.
  fresh_results = {}
  with ThreadPoolExecutor(max_workers=max(len(retailers), 1)) as retailer_executor:
    futures = {}
    if "Adorama" in retailers:
      futures["Adorama"] = retailer_executor.submit(fetch_adorama_info, adorama_id)
    if "Amazon" in retailers:
      futures["Amazon"] = retailer_executor.submit(fetch_amazon_info, asin)
    if "B&H" in retailers:
      futures["B&H"] = retailer_executor.submit(fetch_bh_info, bh_id)
    for name, future in futures.items():
      fresh_results[name] = future.result()

  adorama_data = (
      fresh_results["Adorama"] if "Adorama" in retailers
      else _stale_retailer_data("Adorama", adorama_id, fields)
  )
  amazon_data = (
      fresh_results["Amazon"] if "Amazon" in retailers
      else _stale_retailer_data("Amazon", asin, fields)
  )
  bh_data = (
      fresh_results["B&H"] if "B&H" in retailers
      else _stale_retailer_data("B&H", bh_id, fields)
  )

  adorama_price = adorama_data["price"] if adorama_data else 0.0
  amazon_price = amazon_data["price"] if amazon_data else 0.0
  bh_price = bh_data["price"] if bh_data else 0.0

  valid_retailers = []
  if (
      adorama_data
      and adorama_data.get("status") == "ok"
      and 0 < adorama_price <= max_threshold
  ):
    valid_retailers.append("Adorama")
  if (
      amazon_data
      and amazon_data.get("status") == "ok"
      and 0 < amazon_price <= max_threshold
  ):
    valid_retailers.append("Amazon")
  if (
      bh_data
      and bh_data.get("status") == "ok"
      and 0 < bh_price <= max_threshold
  ):
    valid_retailers.append("B&H")

  # ID가 설정된 곳(=data가 None이 아님) 중 이번에 "확인 필요"로 끝난 곳들.
  # 하나라도 있으면 이번 결과만으로 재고 상태를 확정할 수 없다는 뜻입니다.
  check_needed_sources = [
      name for name, data in (
          ("Adorama", adorama_data), ("Amazon", amazon_data), ("B&H", bh_data)
      )
      if data and data.get("status") == "check_needed"
  ]
  any_check_needed = bool(check_needed_sources)

  if valid_retailers:
    curr_stock = True
  elif not any_check_needed:
    # 시도한 곳들이 전부 확정적인 답(정상가 또는 품절/사이트 자체 신고)을
    # 줬는데 유효한 판매처가 없다면, 진짜 품절/MSRP 초과로 확정합니다.
    curr_stock = False
  else:
    # 일부는 사이트가 막았거나 파싱에 실패해서 확답을 못 받은 상태 - 이전
    # 재고 상태를 그대로 유지하고 "품절"이 아니라 "확인 필요"로만 표시합니다.
    curr_stock = prev_stock

  # B&H 패키지 무게 - 배송비(Shipping_KRW) 계산의 입력값이라, 못 찾았을 때
  # 방치하면(공란/음수 임시값 등) 배송비 계산식이 이상한 값을 뱉습니다.
  # 유효한(양수) 무게가 이미 있으면 건드리지 않고, 없을 때만 1.0kg 기본값을
  # 채워 넣습니다. 크롤링 실패 자체는 매 라운드 Check_Note에 남겨서 눈에
  # 보이게 합니다(값을 덮어쓰든 안 쓰든, "이건 추정치일 수 있다"는 신호).
  bh_weight_kg = (
      bh_data.get("weight_kg") if (bh_data and "B&H" in retailers) else None
  )
  prev_check_note = fields.get("Check_Note") or ""
  weight_note_was_active = "Weight_KG 크롤링 실패" in prev_check_note
  weight_fallback_applied = False
  if bh_weight_kg is not None:
    # 이번에 실제로 찾음 - 예전 실패 메모는 자연히 사라짐(check_note_parts에서 제외)
    weight_update = {"Weight_KG": bh_weight_kg}
  else:
    weight_update = {}
    if "B&H" in retailers and bh_data is not None:
      # 이번 라운드에 B&H를 다시 시도했지만 여전히 못 찾음
      weight_fallback_applied = True
      existing_weight = fields.get("Weight_KG")
      if not existing_weight or existing_weight <= 0:
        weight_update["Weight_KG"] = 1.0
    elif weight_note_was_active:
      # 이번 라운드엔 B&H를 건드리지 않았지만, 예전에 크롤링 실패로 기본값을
      # 쓰고 있었다는 사실 자체는 여전히 유효하니 메모를 계속 유지
      weight_fallback_applied = True

  check_note_parts = [f"{name} 확인 필요" for name in check_needed_sources]
  if weight_fallback_applied:
    check_note_parts.append("Weight_KG 크롤링 실패 - 기본값 1.0kg 사용 중")

  update_data = {
      "In_Stock": curr_stock,
      "Needs_Check": any_check_needed,
      "Check_Note": ", ".join(check_note_parts),
      "Exchange_Rate": current_rate,
      **weight_update,
  }
  # 사이트가 막혀서 확정 못 한 가격은 이전 값을 0으로 덮어쓰지 않고 그대로
  # 둡니다 (마지막으로 확인된 값이 남아있는 게, 잘못된 $0보다 낫습니다).
  # 이번 라운드에 실제로 재조회하지 않은 리테일러의 가격 필드는 건드리지
  # 않습니다(개별 Sync 버튼 - 다른 두 곳 값은 그대로 유지).
  # 가격과 함께, 그 사이트 자체의 재고 여부(_RETAILER_STOCK_FIELD)도 이번에
  # 실제로 재조회한 리테일러만 갱신합니다. 이게 있어야 다음번에 이 리테일러를
  # 건너뛸 때(_stale_retailer_data) 가격>0 추측이 아니라 진짜 마지막 재고
  # 상태를 정확히 읽어올 수 있습니다.
  if "Adorama" in retailers and (
      adorama_data is None or adorama_data.get("status") != "check_needed"
  ):
    update_data["Adorama_USD"] = adorama_price
    update_data["Adorama_In_Stock"] = bool(adorama_data and adorama_data.get("in_stock"))
  if "Amazon" in retailers and (
      amazon_data is None or amazon_data.get("status") != "check_needed"
  ):
    update_data["Amazon_USD"] = amazon_price
    update_data["Amazon_In_Stock"] = bool(amazon_data and amazon_data.get("in_stock"))
  if "B&H" in retailers and (
      bh_data is None or bh_data.get("status") != "check_needed"
  ):
    update_data["BH_USD"] = bh_price
    update_data["BH_In_Stock"] = bool(bh_data and bh_data.get("in_stock"))

  try:
    table.update(record_id, update_data)
  except Exception:
    pass

  def _fmt(label, name, data, price):
    if data and data.get("status") == "check_needed":
      return f"{label}:⚠({data.get('detail') or 'check'})"
    suffix = "" if name in retailers else "(cached)"
    return f"{label}:${price}{suffix}"

  log_line = (
      f"✅ [{sku}] Complete | {_fmt('Ado', 'Adorama', adorama_data, adorama_price)} /"
      f" {_fmt('Amz', 'Amazon', amazon_data, amazon_price)} /"
      f" {_fmt('BH', 'B&H', bh_data, bh_price)}"
  )

  status_change = None
  if any_check_needed and not prev_needs_check:
    status_change = (
        "CHECK",
        f"⚠️ **[확인 필요]** *{sku}*\n• {', '.join(check_needed_sources)} 접속/파싱"
        f" 실패 - 사이트를 직접 확인해주세요",
    )
  elif prev_stock != curr_stock:
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


def run_tbd_tracker(log_container, retailers=RETAILER_NAMES, only_needs_check=False):
  """retailers: 이번 라운드에 재조회할 리테일러 이름 집합/튜플. 기본값은 3곳
  전체(전체 Sync 버튼). 개별 Sync 버튼은 {"Adorama"} 처럼 1곳만 넘겨줍니다.
  only_needs_check=True면 Needs_Check=True인 상품만 골라 재조회합니다
  ("확인 필요만 Sync" 버튼)."""
  retailers_label = (
      " / ".join(retailers) if len(retailers) < len(RETAILER_NAMES)
      else "Adorama / Amazon / B&H Triple-Channel"
  )
  log_container.write(f"⚡ [UI.com Engine] {retailers_label} Syncing...")
  current_rate = get_current_exchange_rate()
  log_container.write(f"💱 Applied Exchange Rate: ₩{current_rate}")

  records = table.all()
  if only_needs_check:
    records = [r for r in records if r["fields"].get("Needs_Check")]
    log_container.write(f"🔍 확인 필요 상품만 재조회 대상: {len(records)}건")
    if not records:
      log_container.write("✨ 확인 필요한 상품이 없습니다.")
      return 0

  total_count = len(records)
  log_container.write(f"📦 Active Inventory Records: {total_count}")

  out_of_stock_count = 0
  back_in_stock_count = 0
  check_needed_count = 0
  detail_messages = []
  updated_count = len(records)

  # 바깥쪽 풀은 그저 "동시에 대기줄에 들어갈 수 있는 상품 개수"이고, 실제
  # 네트워크 동시 요청 한도는 위 세마포어들이 지킵니다. 10개면 상품 10개가
  # 동시에 세마포어 대기줄에 들어가 충분히 파이프라인을 채웁니다.
  with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(process_single_record, r, current_rate, retailers)
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
        elif st_type == "CHECK":
          check_needed_count += 1
        detail_messages.append(msg)

  changed_total = out_of_stock_count + back_in_stock_count

  summary_header = [
      "📊 **[UI.com Supply Monitor] Sync Report**",
      f"• **Synced Retailers**: {' / '.join(retailers)}",
      f"• **Monitored Items**: {total_count} units",
      f"• **Status Shift**: {changed_total} (🔴 Out of Stock {out_of_stock_count}"
      f" / 🟢 Normal {back_in_stock_count})",
      f"• **Needs Manual Check**: {check_needed_count} (사이트 접속/파싱 실패 - 품절"
      " 확정 아님)",
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
  """NocoDB 호출이 실패해도(토큰 만료/권한 부족/네트워크 오류) 대시보드 전체가
  죽지 않고, 원인을 바로 알 수 있게 에러 메시지를 보여준 뒤 빈 목록으로 계속 진행."""
  try:
    return table.all()
  except requests.exceptions.HTTPError as e:
    status = e.response.status_code if e.response is not None else "?"
    if status == 401:
      hint = "NOCODB_API_TOKEN이 만료/무효합니다. NocoDB Account Settings > Tokens에서 새 토큰을 발급하세요."
    elif status == 403:
      hint = "토큰에 이 Base('UniFi Supply')/Products 테이블에 대한 접근 권한이 없습니다."
    elif status == 404:
      hint = "NOCODB_URL 또는 NOCODB_TABLE_ID가 올바른지 확인하세요."
    elif status == 429:
      hint = "NocoDB API 요청 한도를 초과했습니다. 잠시 후 다시 시도하세요."
    else:
      hint = "NocoDB API 호출 중 오류가 발생했습니다."
    st.error(f"⚠️ NocoDB 연결 실패 (HTTP {status}): {hint}")
    return []
  except Exception as e:
    st.error(f"⚠️ NocoDB 연결 실패: {e}")
    return []


# ==========================================
# 3. UI 보조 함수
# ==========================================
class _CappedSidebarLog:
  """사이드바 하단 로그 슬롯에 최근 N줄만 실시간으로 보여주는
  run_tbd_tracker()용 래퍼.

  run_tbd_tracker()는 여러 줄을 log_container.write(msg)로 계속 호출합니다.
  이전 버전은 "처음 N줄"만 고정해서 보여줬는데, 그러면 동기화가 진행돼도
  화면이 그대로 멈춰 보여서 실제로 뭐가 갱신되고 있는지 알 수 없었습니다.
  대신 매번 최근 N줄만 보여주는 롤링(rolling) 윈도우로 바꿔서, 새 줄이
  들어올 때마다 오래된 줄은 밀려나고 화면이 계속 최신 상태로 갱신되게
  합니다. (이전 실행 결과는 새 실행 시작과 동시에 지워집니다.)
  """

  def __init__(self, slot, limit=8):
    self.slot = slot
    self.limit = limit
    self.lines = []
    self.total = 0

  def write(self, msg):
    self.total += 1
    self.lines.append(str(msg))
    if len(self.lines) > self.limit:
      self.lines = self.lines[-self.limit:]
    rows = "".join(
        f'<div class="uic-sync-log-line">{html_escape(l)}</div>'
        for l in self.lines
    )
    self.slot.markdown(
        f'<div class="uic-sync-log">{rows}</div>', unsafe_allow_html=True
    )


_COLOR_KEY_GOOD = "accent"    # MSRP보다 저렴
_COLOR_KEY_SAME = "success"   # MSRP와 동일
_COLOR_KEY_BAD = "danger"     # 가격정보 없음 / MSRP보다 비쌈

_PRICE_COL_TO_RETAILER = {"B&H ($)": "B&H", "Adorama ($)": "Adorama", "Amazon ($)": "Amazon"}


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


# UniFi Store(store.ui.com) 제품 URL은 카테고리 없이 슬러그만으로 접근 가능함
# (예: https://store.ui.com/us/en/products/u6-pro). 이 슬러그는 techspecs.ui.com
# 크롤링 프로젝트 때 만들어둔 product_slug_map.json의 techspecs_slug와 동일한
# 값이라(실측 확인함) 그 파일을 그대로 재사용합니다.
# NocoDB로 이전하면서 레코드 id 체계가 완전히 바뀌었으므로(Airtable recXXXX ->
# NocoDB 정수 Id), 더 이상 record id로 매칭할 수 없습니다. 대신 두 데이터
# 모두에 안정적으로 존재하는 product_slug_map.json의 "name" <-> NocoDB의
# "SKU" 필드(실제로는 제품명을 담고 있음, 예: "UniFi U6 Mesh")로 매칭합니다.
_PRODUCT_SLUG_MAP_FILE = Path(__file__).parent / "product_slug_map.json"


@st.cache_data(show_spinner=False)
def _load_unifi_store_slug_map():
  if not _PRODUCT_SLUG_MAP_FILE.exists():
    return {}
  try:
    records = json.loads(_PRODUCT_SLUG_MAP_FILE.read_text(encoding="utf-8"))
    return {
        r["name"]: r["techspecs_slug"]
        for r in records if r.get("name") and r.get("techspecs_slug")
    }
  except Exception:
    return {}


def _unifi_store_url(product_name):
  slug = _load_unifi_store_slug_map().get(product_name)
  if not slug:
    return None
  return f"https://store.ui.com/us/en/products/{slug}"


def _naver_url(naver_id):
  if not naver_id or str(naver_id).strip() in ("", "-"):
    return None
  return f"https://smartstore.naver.com/tbdseoul/products/{str(naver_id).strip()}"


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


def sort_records_by_category_then_name(records):
  """메인 대시보드 '전체 상품' 표 정렬: 1) 왼쪽 메뉴의 카테고리 순서,
  2) 같은 카테고리 안에서는 이름(SKU) 오름차순."""
  def _key(r):
    fields = r["fields"]
    category = fields.get("Category")
    category_rank = (
        CATEGORIES.index(category) if category in CATEGORIES else len(CATEGORIES)
    )
    name = str(fields.get("SKU") or "").lower()
    return (category_rank, name)

  return sorted(records, key=_key)


def sort_records_by_name(records):
  """카테고리별 페이지 표 정렬: 상품 이름(SKU) 오름차순."""
  return sorted(records, key=lambda r: str(r["fields"].get("SKU") or "").lower())


def status_counts(records):
  """판매 가능 / 품절 / 확인 필요 3분류 카운트. render_products_table의 Status
  뱃지 우선순위(확인 필요 > 판매가능/품절)와 동일한 기준으로 집계해, 카드 숫자와
  표에 실제로 보이는 뱃지 개수가 항상 일치하게 합니다."""
  active = out_of_stock = needs_check = 0
  for r in records:
    f = r["fields"]
    if f.get("Needs_Check"):
      needs_check += 1
    elif f.get("In_Stock"):
      active += 1
    else:
      out_of_stock += 1
  return active, out_of_stock, needs_check


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

    needs_check = bool(f.get("Needs_Check"))
    check_note = f.get("Check_Note") or ""
    # Status 뱃지는 마우스를 올리면 항상 Check_Note를 보여줍니다(재고
    # 확인이 안 됐을 때뿐 아니라, Active/Out of Stock 상태에서도 예를 들어
    # "무게 크롤링 실패로 배송비 추정치 사용 중" 같은 메모가 있으면 보이게).
    tooltip_note = check_note or (
        "사이트 접속/파싱 실패 - 직접 확인해주세요" if needs_check else ""
    )
    tooltip_attr = f' title="{html_escape(tooltip_note)}"' if tooltip_note else ""
    # Check_Note에서 "Adorama 확인 필요"처럼 이번에 확인이 안 된 개별
    # 리테일러를 뽑아냄. 그 리테일러의 가격 셀은 회색으로 표시해서, 이게
    # 이번에 새로 확인된 값이 아니라 마지막으로 확인됐던 값(stale)이라는
    # 걸 한눈에 알 수 있게 합니다.
    blocked_retailers = {
        name for name in RETAILER_NAMES if f"{name} 확인 필요" in check_note
    }
    if needs_check:
      status_html = f'<span class="uic-pill check"{tooltip_attr}>⚠ Check Needed</span>'
    elif is_active:
      status_html = f'<span class="uic-pill ok"{tooltip_attr}>Active</span>'
    else:
      status_html = f'<span class="uic-pill bad"{tooltip_attr}>Out of Stock</span>'
    cat_html = f'<span class="uic-pill cat">{html_escape(category)}</span>'

    unifi_store_url = _unifi_store_url(sku)
    naver_url = _naver_url(f.get("Naver_Product_No"))

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
        "Naver ID": naver_url,
        "UniFi Store ($)": unifi_store_url,
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
      elif col in _PRICE_COL_TO_RETAILER and _PRICE_COL_TO_RETAILER[col] in blocked_retailers:
        style = (
            f' style="color:{_rgba_from_hex(t["text_secondary"], 0.45)};" '
            f'title="확인 필요 - 마지막으로 확인된 값"'
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
  logo_uri = logo_data_uri(st.session_state.get("theme", "light"))
  st.sidebar.markdown(
      f"""
      <div class="uic-logo-wrap">
          {'<img src="' + logo_uri + '" alt="TBD Dashboard" />' if logo_uri else '⚡ TBD Dashboard'}
      </div>
      """,
      unsafe_allow_html=True,
  )

  sync_all_clicked = st.sidebar.button(
      "⚡ Sync All Retailers", type="primary", use_container_width=True,
      help="상품 1개당 Adorama+Amazon+B&H 합쳐 보통 약 12크레딧, 봇 차단이"
      " 걸리면 최대 약 22크레딧까지 소모될 수 있습니다.",
  )

  # 확인 필요(Needs_Check=True) 상품만 골라 재조회하는 버튼. 다른 Sync
  # 버튼과 헷갈리지 않도록 경고색(warning)으로 구분합니다.
  with st.sidebar.container(key="check_needed_sync_row"):
    sync_check_needed_clicked = st.button(
        "🔍 Sync 확인 필요만", use_container_width=True,
        key="sync_check_needed_btn",
        help="Needs_Check=True로 표시된 상품만 Adorama+Amazon+B&H 재조회",
    )

  # 리테일러별 개별 Sync 버튼. 한 곳만 다시 확인하고 싶을 때(예: Adorama가
  # 502로 자주 실패해서 그곳만 재시도) 다른 두 곳까지 전부 돌리지 않아도 됨.
  # 안 고른 두 곳은 NocoDB에 저장된 마지막 값을 그대로 사용해 In_Stock 등
  # 전체 판단은 계속 3곳 기준으로 일관되게 유지됩니다.
  with st.sidebar.container(key="retailer_sync_row"):
    rcol1, rcol2, rcol3 = st.columns(3, gap="small")
    with rcol1:
      sync_adorama_clicked = st.button(
          "Adorama", use_container_width=True, key="sync_adorama_btn",
          help="Adorama만 재조회 (Amazon/B&H는 마지막 값 유지)",
      )
    with rcol2:
      sync_amazon_clicked = st.button(
          "Amazon", use_container_width=True, key="sync_amazon_btn",
          help="Amazon만 재조회 (Adorama/B&H는 마지막 값 유지)",
      )
    with rcol3:
      sync_bh_clicked = st.button(
          "B&H", use_container_width=True, key="sync_bh_btn",
          help="B&H만 재조회 (Adorama/Amazon은 마지막 값 유지)",
      )

  retailers_to_sync = None
  only_needs_check = False
  if sync_all_clicked:
    retailers_to_sync = RETAILER_NAMES
  elif sync_check_needed_clicked:
    retailers_to_sync = RETAILER_NAMES
    only_needs_check = True
  elif sync_adorama_clicked:
    retailers_to_sync = ("Adorama",)
  elif sync_amazon_clicked:
    retailers_to_sync = ("Amazon",)
  elif sync_bh_clicked:
    retailers_to_sync = ("B&H",)

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
  if retailers_to_sync:
    capped_log = _CappedSidebarLog(log_slot, limit=8)
    if only_needs_check:
      sync_label = "확인 필요"
    else:
      sync_label = (
          " / ".join(retailers_to_sync)
          if len(retailers_to_sync) < len(RETAILER_NAMES) else "Adorama / Amazon / B&H"
      )
    with st.spinner(f"{sync_label} 동기화 중..."):
      count = run_tbd_tracker(
          capped_log, retailers_to_sync, only_needs_check=only_needs_check
      )
    log_slot.success(f"⚡ {sync_label} 동기화 완료 ({count}건 갱신)")
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
    active_count, out_stock, check_needed = status_counts(records)
    cat_counts = {c: 0 for c in CATEGORIES}
    for r in records:
      c = r["fields"].get("Category")
      if c in cat_counts:
        cat_counts[c] += 1

    c1, c2, c3, c4, c5 = st.columns(5)
    render_metric_card(c1, "전체 상품", f"{total}")
    render_metric_card(c2, "판매 가능 (Active)", f"{active_count}", "success")
    render_metric_card(c3, "품절 (Out of Stock)", f"{out_stock}", "danger")
    render_metric_card(c4, "확인 필요 (Check Needed)", f"{check_needed}", "warning")
    render_metric_card(c5, "카테고리", f"{len([c for c in cat_counts.values() if c > 0])}", "accent")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("##### 카테고리별 현황")
    st.caption("카드를 클릭하면 해당 카테고리의 상품/가격만 모아볼 수 있어요.")

    cat_cols = st.columns(4)
    for idx, cat in enumerate(CATEGORIES):
      with cat_cols[idx % 4]:
        with st.container(key=f"catcard_{cat}"):
          st.markdown(
              f"""
              <div class="uic-cat-card">
                  <div class="uic-cat-card-title">{cat}</div>
                  <div class="uic-cat-card-count">
                      <span class="uic-cat-card-num">{cat_counts[cat]}</span>Products
                  </div>
              </div>
              """,
              unsafe_allow_html=True,
          )
          if st.button(f"{cat} 카테고리 보기", key=f"catbtn_{cat}"):
            st.session_state.nav_choice = f"　{cat}"
            st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.markdown("##### 전체 상품")
    sorted_records = sort_records_by_category_then_name(records)
    render_products_table(sorted_records, theme_now, show_category=True)

  else:
    cat_records = [r for r in records if r["fields"].get("Category") == active_category]
    cat_records = sort_records_by_name(cat_records)
    cat_active, cat_out_stock, cat_check_needed = status_counts(cat_records)

    c1, c2, c3, c4 = st.columns(4)
    render_metric_card(c1, "상품 수", f"{len(cat_records)}")
    render_metric_card(c2, "판매 가능", f"{cat_active}", "success")
    render_metric_card(c3, "품절", f"{cat_out_stock}", "danger")
    render_metric_card(c4, "확인 필요", f"{cat_check_needed}", "warning")

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
