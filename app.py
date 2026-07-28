import base64
from html import escape as html_escape
from pathlib import Path

import streamlit as st

from sync_engine import (
    CATEGORIES,
    RETAILER_NAMES,
    THEMES,
    build_products_table_html,
    get_current_exchange_rate,
    get_scrapedo_usage,
    run_tbd_tracker,
    safe_fetch_records,
    sort_records_by_category_then_name,
    sort_records_by_name,
    status_counts,
    table,
)
from config import NOCODB_URL

# ==========================================
# 1. 페이지 및 환경 설정
# ==========================================
st.set_page_config(
    page_title="UniFi Supply Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 바로가기 링크 (메인 도메인)
QUICK_LINKS = {
    "NocoDB": NOCODB_URL,
    "Scrape.do": "https://scrape.do",
    "GitHub": "https://github.com",
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
  판매가격/최종가격/수익까지 보여주는 Site Manager 스타일 테이블.

  실제 HTML 생성은 sync_engine.build_products_table_html()이 담당 (NiceGUI
  대시보드와 공유) - 여기선 Streamlit 렌더링(st.info/st.markdown)만 담당."""
  table_html = build_products_table_html(records, theme_name, show_category=show_category)
  if table_html is None:
    st.info("등록된 상품이 없습니다.")
    return
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

  records = safe_fetch_records(on_error=st.error)
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
