"""디자인 토큰 + 전역 스타일시트.

1차 버전은 사실 기존 Streamlit 레이아웃에 파스텔 색만 입힌 수준이라
"기존과 큰 차이가 없다"는 피드백을 받음. 문제의 핵심: 페이지 배경(bg)과
카드 배경(surface)이 똑같은 흰색이라 카드가 전혀 "떠 보이지" 않았음 -
참고 디자인(ProductPal/Sterling Legal/Zendenta) 3개 전부 공통적으로
연한 회색 배경 위에 흰 카드를 그림자로 띄우는 레이어 구조를 쓴다.

이번엔 그 레이어 구조를 실제로 만든다:
  - 페이지 배경 ≠ 카드 배경 (연한 웜그레이 위에 흰 카드가 그림자로 분리)
  - radius를 전체적으로 크게 (카드 20px, 필/뱃지는 완전 라운드)
  - 그림자를 얇은 테두리 대신 실제 elevation처럼 (2단 블러)
  - 여백을 훨씬 넉넉하게 (섹션 간 간격, 카드 내부 패딩 전부 확대)
  - 사이드바는 페이지와 같은 회색 배경에 로고/네비만 놓고, 활성 항목만
    알약(pill) 모양으로 살짝 띄움 - 딱딱한 테두리 구분선 대신 여백으로 분리
"""
from __future__ import annotations

import base64
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"


def _b64(filename: str) -> str:
  path = ASSETS_DIR / filename
  if not path.exists():
    return ""
  return base64.b64encode(path.read_bytes()).decode()


FONT_REGULAR = _b64("ui-sans-v9-regular.woff2")
FONT_MEDIUM = _b64("ui-sans-v9-medium.woff2")
FONT_BOLD = _b64("ui-sans-v9-bold.woff2")
FONT_BLACK = _b64("ui-sans-v9-black.woff2")
LOGO_DARK = _b64("tbd_dashboard.svg")
LOGO_LIGHT = _b64("tbd_dashboard_white.svg")


def logo_data_uri(theme_name: str) -> str:
  logo_data = LOGO_LIGHT if theme_name == "dark" else LOGO_DARK
  return f"data:image/svg+xml;base64,{logo_data}" if logo_data else ""


# ==========================================
# 라이트/다크 각각의 CSS 변수 값
# ==========================================
_VARS = {
    "light": {
        # 페이지 배경(연한 웜그레이)과 카드 배경(순백)을 분리 - 이게 핵심.
        "page-bg": "#F4F4F6",
        "surface": "#FFFFFF",
        "surface-tint": "rgba(33, 35, 39, 0.04)",
        "surface-tint-strong": "rgba(33, 35, 39, 0.07)",
        "border": "rgba(33, 35, 39, 0.08)",
        "text": "#1A1B1E",
        "text-secondary": "#82868C",
        "accent": "#006FFF",
        "accent-soft-bg": "#E8F1FF",
        "success": "#189652",
        "success-soft-bg": "#E3F8EB",
        "danger": "#E5484D",
        "danger-soft-bg": "#FDEBEC",
        "warning": "#B25E09",
        "warning-soft-bg": "#FCF1E3",
        "shadow": "0 1px 1px rgba(20, 21, 26, 0.03), 0 8px 20px -6px rgba(20, 21, 26, 0.08)",
        "shadow-sm": "0 1px 2px rgba(20, 21, 26, 0.04)",
        # 활성 메뉴 항목: 카드와 같은 언어로 - 회색 사이드바 위에 흰 배경만
        # 살짝 얹어서 표시 (검정 필이 아니라 옅은 부상 효과).
        "nav-active-bg": "#FFFFFF",
        "nav-active-text": "#1A1B1E",
    },
    "dark": {
        "page-bg": "#0B0C0E",
        "surface": "#1B1D21",
        "surface-tint": "rgba(249, 250, 250, 0.045)",
        "surface-tint-strong": "rgba(249, 250, 250, 0.08)",
        "border": "rgba(249, 250, 250, 0.08)",
        "text": "#F5F6F7",
        "text-secondary": "#8E9298",
        "accent": "#4C9AFF",
        "accent-soft-bg": "#122A4D",
        "success": "#36D876",
        "success-soft-bg": "#0F2E1E",
        "danger": "#FF6259",
        "danger-soft-bg": "#3A1414",
        "warning": "#F0A83C",
        "warning-soft-bg": "#3A2B0F",
        "shadow": "0 1px 1px rgba(0, 0, 0, 0.2), 0 8px 20px -6px rgba(0, 0, 0, 0.5)",
        "shadow-sm": "0 1px 2px rgba(0, 0, 0, 0.3)",
        # 다크모드에서는 순백 대신 카드와 동일한(surface) 밝은 회색으로 -
        # 순백 필은 다크 배경에서 너무 튀어서 surface 톤으로 "부상" 느낌만 유지.
        "nav-active-bg": "#2A2D32",
        "nav-active-text": "#F5F6F7",
    },
}

# Sync 버튼 전용 색 - 라이트/다크 상관없이 항상 검정 배경 + 흰 글씨로 고정
# (사이드바 테마와 무관하게 "액션 버튼"이라는 걸 항상 같은 색으로 구분).
BLACK_BTN_BG = "#1A1B1E"
BLACK_BTN_TEXT = "#FFFFFF"

RADIUS_SM = "10px"
RADIUS_MD = "16px"
RADIUS_LG = "22px"
RADIUS_PILL = "999px"


def _vars_block(scope: str, tokens: dict) -> str:
  lines = "\n".join(f"    --tbd-{k}: {v};" for k, v in tokens.items())
  return f"{scope} {{\n{lines}\n}}"


def build_head_html() -> str:
  """<head>에 한 번만 주입할 폰트 + CSS 변수 + 전역 스타일시트."""
  vars_css = (
      _vars_block(":root", _VARS["light"]) + "\n"
      + _vars_block("body.tbd-dark", _VARS["dark"])
  )
  return f"""
  <style>
    @font-face {{ font-family:'UI Sans'; src:url(data:font/woff2;base64,{FONT_REGULAR}) format('woff2'); font-weight:400; font-display:swap; }}
    @font-face {{ font-family:'UI Sans'; src:url(data:font/woff2;base64,{FONT_MEDIUM}) format('woff2'); font-weight:500; font-display:swap; }}
    @font-face {{ font-family:'UI Sans'; src:url(data:font/woff2;base64,{FONT_BOLD}) format('woff2'); font-weight:700; font-display:swap; }}
    @font-face {{ font-family:'UI Sans'; src:url(data:font/woff2;base64,{FONT_BLACK}) format('woff2'); font-weight:900; font-display:swap; }}

    {vars_css}

    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0;
      background-color: var(--tbd-page-bg);
      color: var(--tbd-text);
      font-family: 'UI Sans', 'Pretendard', -apple-system, BlinkMacSystemFont,
        'Segoe UI', Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    a {{ color: var(--tbd-accent); }}
    .q-page, .nicegui-content {{ background-color: var(--tbd-page-bg); padding: 0 !important; }}

    /* ---------- 레이아웃 ---------- */
    .tbd-shell {{ display: flex; min-height: 100vh; background-color: var(--tbd-page-bg); }}
    .tbd-sidebar {{
      width: 252px;
      flex-shrink: 0;
      background-color: var(--tbd-page-bg);
      padding: 28px 18px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}
    .tbd-main {{
      flex: 1;
      min-width: 0;
      padding: 40px 48px 96px;
    }}

    .tbd-logo-wrap {{
      display: flex;
      align-items: center;
      padding: 4px 6px 24px 6px;
      margin-bottom: 8px;
    }}
    .tbd-logo-wrap img {{ height: 38px; width: auto; display: block; }}

    .tbd-nav-label {{
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      color: var(--tbd-text-secondary);
      margin: 22px 10px 8px 10px;
      opacity: 0.8;
    }}

    /* ---------- 사이드바 네비 링크 ---------- */
    .tbd-nav-link {{
      display: block;
      padding: 9px 14px;
      margin: 1px 0;
      border-radius: {RADIUS_SM};
      font-size: 13.5px;
      font-weight: 500;
      color: var(--tbd-text) !important;
      text-decoration: none !important;
      transition: background-color 0.15s ease-in-out;
    }}
    .tbd-nav-link:hover {{ background-color: var(--tbd-surface-tint-strong); }}
    .tbd-nav-link.active {{
      background-color: var(--tbd-nav-active-bg);
      color: var(--tbd-nav-active-text) !important;
      font-weight: 700;
      box-shadow: var(--tbd-shadow-sm);
    }}

    /* ---------- 바로가기 ---------- */
    .tbd-quicklinks {{ display: flex; gap: 8px; margin-top: 8px; }}
    .tbd-quicklink {{
      flex: 1;
      text-align: center;
      padding: 9px 4px;
      border-radius: {RADIUS_SM};
      background-color: var(--tbd-surface);
      box-shadow: var(--tbd-shadow-sm);
      font-size: 11px;
      font-weight: 600;
      color: var(--tbd-text-secondary) !important;
      text-decoration: none !important;
    }}
    .tbd-quicklink:hover {{ color: var(--tbd-accent) !important; }}

    /* ---------- 상단바 ---------- */
    /* 이전엔 position:absolute로 배지를 띄웠는데, NiceGUI의 ui.html()
       래퍼가 콘텐츠 너비만큼만 차지해서 padding-right 여백 계산이 어긋나
       타이틀 글자 위에 배지가 그대로 겹쳐버렸음. flex + space-between으로
       바꿔서 컨테이너 실제 너비와 무관하게 항상 안 겹치게 함. */
    .tbd-topbar {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 24px;
      padding-bottom: 28px;
      margin-bottom: 32px;
      width: 100%;
    }}
    .tbd-topbar-title {{
      font-size: 34px;
      font-weight: 800;
      letter-spacing: -0.8px;
      line-height: 1.1;
      margin: 0;
    }}
    .tbd-badge {{
      flex-shrink: 0;
      margin-top: 6px;
      background-color: var(--tbd-accent-soft-bg);
      color: var(--tbd-accent);
      font-size: 11px;
      font-weight: 700;
      padding: 5px 12px;
      border-radius: {RADIUS_PILL};
      text-transform: uppercase;
      letter-spacing: 0.5px;
      white-space: nowrap;
    }}

    /* ---------- 통계 카드 ---------- */
    .tbd-card {{
      position: relative;
      background-color: var(--tbd-surface);
      border-radius: {RADIUS_MD};
      padding: 22px 24px;
      box-shadow: var(--tbd-shadow);
      width: 100%;
      height: 100%;
      overflow: hidden;
    }}
    /* 의미별 파스텔 배경 변형 - 카드 자체를 톤온톤으로 (그림자는 옅게 유지) */
    .tbd-card--success {{ background-color: var(--tbd-success-soft-bg); }}
    .tbd-card--danger  {{ background-color: var(--tbd-danger-soft-bg); }}
    .tbd-card--warning {{ background-color: var(--tbd-warning-soft-bg); }}
    .tbd-card--accent  {{ background-color: var(--tbd-accent-soft-bg); }}

    .tbd-card-icon {{
      position: absolute;
      top: 18px;
      right: 18px;
      width: 34px;
      height: 34px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      background-color: rgba(255,255,255,0.55);
    }}
    body.tbd-dark .tbd-card-icon {{ background-color: rgba(0,0,0,0.25); }}

    .tbd-card-label {{
      font-size: 12px;
      font-weight: 600;
      color: var(--tbd-text-secondary);
      letter-spacing: 0.1px;
      margin-bottom: 10px;
      padding-right: 40px; /* 우측 상단 아이콘 배지와 겹치지 않도록 */
      /* 라벨이 1줄/2줄로 나뉘는 카드가 섞이면 카드 높이가 들쭉날쭉해지므로
         2줄 기준으로 최소 높이를 고정해 항상 같은 높이로 보이게 함. */
      min-height: 32px;
    }}
    .tbd-card-value {{ font-size: 32px; font-weight: 800; letter-spacing: -0.7px; line-height: 1; color: var(--tbd-text); }}
    .tbd-card-value.success {{ color: var(--tbd-success); }}
    .tbd-card-value.danger  {{ color: var(--tbd-danger); }}
    .tbd-card-value.warning {{ color: var(--tbd-warning); }}
    .tbd-card-value.accent  {{ color: var(--tbd-accent); }}

    /* ---------- 카테고리 카드 ---------- */
    .tbd-cat-card {{
      background-color: var(--tbd-surface);
      border-radius: {RADIUS_MD};
      padding: 20px 20px;
      box-shadow: var(--tbd-shadow);
      cursor: pointer;
      transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
      text-decoration: none !important;
      display: block;
      color: var(--tbd-text) !important;
    }}
    .tbd-cat-card:hover {{ transform: translateY(-2px); box-shadow: 0 1px 1px rgba(20,21,26,0.04), 0 14px 28px -8px rgba(20,21,26,0.14); }}
    .tbd-cat-card-title {{ font-size: 13.5px; font-weight: 600; color: var(--tbd-text-secondary); margin-bottom: 10px; }}
    .tbd-cat-card-count {{ font-size: 12px; color: var(--tbd-text-secondary); font-weight: 600; }}
    .tbd-cat-card-num {{
      font-size: 28px; font-weight: 800; letter-spacing: -0.6px; margin-right: 6px;
      color: var(--tbd-text);
    }}

    /* ---------- 커스텀 테이블 (sync_engine.build_products_table_html 출력) ---------- */
    .uic-table-wrap {{
      background-color: var(--tbd-surface);
      border-radius: {RADIUS_MD};
      box-shadow: var(--tbd-shadow);
      overflow: hidden;
      margin-top: 4px;
    }}
    .uic-table-scroll {{
      overflow-x: auto;
      scrollbar-width: thin;
      scrollbar-color: var(--tbd-border) transparent;
    }}
    .uic-table-scroll::-webkit-scrollbar {{ height: 6px; }}
    .uic-table-scroll::-webkit-scrollbar-track {{ background: transparent; }}
    .uic-table-scroll::-webkit-scrollbar-thumb {{ background-color: var(--tbd-text-secondary); border-radius: 4px; }}
    table.uic-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    table.uic-table thead th {{
      text-align: center; font-size: 10.5px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.5px; color: var(--tbd-text-secondary); background-color: transparent;
      padding: 16px 16px 12px; border-bottom: 1px solid var(--tbd-border); white-space: nowrap;
    }}
    table.uic-table tbody td {{
      padding: 14px 16px; border-bottom: 1px solid var(--tbd-border); white-space: nowrap;
      text-align: center; vertical-align: middle; line-height: 1.4; box-sizing: border-box;
      color: var(--tbd-text);
    }}
    table.uic-table tbody tr:last-child td {{ border-bottom: none; }}
    table.uic-table tbody tr:hover {{ background-color: var(--tbd-surface-tint); }}
    table.uic-table td.uic-sku {{ font-weight: 700; text-align: left; }}
    table.uic-table td a {{ color: inherit; text-decoration: none; }}
    table.uic-table td a:hover {{ text-decoration: underline; }}
    table.uic-table th.uic-divider, table.uic-table td.uic-divider {{ border-left: 1px solid var(--tbd-border); }}
    table.uic-table th.uic-final-price, table.uic-table td.uic-final-price {{ background-color: var(--tbd-accent-soft-bg); }}

    .uic-pill {{ display: inline-block; padding: 4px 12px; border-radius: {RADIUS_PILL}; font-size: 11.5px; font-weight: 700; }}
    .uic-pill[title] {{ cursor: help; }}
    .uic-pill.ok {{ background-color: var(--tbd-success-soft-bg); color: var(--tbd-success); }}
    .uic-pill.bad {{ background-color: var(--tbd-danger-soft-bg); color: var(--tbd-danger); }}
    .uic-pill.check {{ background-color: var(--tbd-warning-soft-bg); color: var(--tbd-warning); }}
    .uic-pill.cat {{ background-color: var(--tbd-accent-soft-bg); color: var(--tbd-accent); }}

    /* ---------- 아바타/이니셜 칩 (담당자 표시용, 향후 주문관리 등에서 사용) ---------- */
    .tbd-avatar {{
      display: inline-flex; align-items: center; justify-content: center;
      width: 26px; height: 26px; border-radius: 50%;
      background-color: var(--tbd-accent-soft-bg); color: var(--tbd-accent);
      font-size: 11px; font-weight: 700;
    }}

    /* ---------- 진행률 바 (향후 재고/입고 등에서 사용) ---------- */
    .tbd-progress {{
      height: 6px; border-radius: 3px; background-color: var(--tbd-surface-tint-strong);
      overflow: hidden;
    }}
    .tbd-progress-bar {{ height: 100%; background-color: var(--tbd-accent); border-radius: 3px; }}

    /* ---------- 동기화 로그 ---------- */
    .tbd-sync-log {{
      margin-top: 6px; border-radius: {RADIUS_SM}; background-color: var(--tbd-surface);
      box-shadow: var(--tbd-shadow-sm); font-size: 10.5px; color: var(--tbd-text-secondary);
    }}

    hr {{ border-color: var(--tbd-border) !important; }}
  </style>
  """
