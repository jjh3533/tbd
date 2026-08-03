"""사이드바 + 상단 셸."""
from __future__ import annotations

from contextlib import contextmanager

from nicegui import ui

from sync_engine import CATEGORIES
from dashboard import theme


def _category_href(name: str) -> str:
  from dashboard.pages.category import category_slug
  return f"/category/{category_slug(name)}"


@contextmanager
def frame(active_path: str):
  """사이드바+상단 셸을 그리고, 본문을 채울 컨테이너를 with 블록으로 넘겨준다."""
  ui.add_head_html(theme.build_head_html())

  with ui.row().classes("tbd-shell w-full gap-0 no-wrap"):
    with ui.column().classes("tbd-sidebar gap-1"):
      logo_uri = theme.logo_data_uri()
      if logo_uri:
        ui.html(f'<div class="tbd-logo-wrap"><img src="{logo_uri}" alt="TBD Dashboard"/></div>', sanitize=False)
      else:
        ui.html('<div class="tbd-logo-wrap">⚡ TBD Dashboard</div>', sanitize=False)

      products_expanded = (
          active_path == "/"
          or active_path.startswith("/category/")
          or active_path.startswith("/brand/")
      )
      ui.html('<div class="tbd-nav-label">PRODUCTS</div>', sanitize=False)
      for label, href in [
          ("➕ 신규등록", "/register"),
          ("🖼️ 상세페이지 제작", "/detail-page-builder"),
          ("📋 상품 리스트", "/"),
          ("⚡ 가격 업데이트", "/sync"),
          ("📦 품절/변동", "/inventory"),
          ("🏪 스마트스토어", "/smartstore"),
      ]:
        active_cls = "tbd-nav-link active" if href == active_path else "tbd-nav-link"
        ui.html(f'<a class="{active_cls}" href="{href}">{label}</a>', sanitize=False)
        if href == "/" and products_expanded:
          for brand_label, brand_href in [("UniFi", "/brand/unifi"), ("GL.iNet", "/brand/glinet")]:
            sub_cls = "tbd-nav-link tbd-nav-sub active" if brand_href == active_path else "tbd-nav-link tbd-nav-sub"
            ui.html(f'<a class="{sub_cls}" href="{brand_href}">{brand_label}</a>', sanitize=False)

      ui.html('<div class="tbd-nav-label">SALES</div>', sanitize=False)
      for label, href in [
          ("🛒 주문", "/orders"),
          ("📝 발주", "/purchase"),
          ("🚚 배송", "/shipping"),
      ]:
        active_cls = "tbd-nav-link active" if href == active_path else "tbd-nav-link"
        ui.html(f'<a class="{active_cls}" href="{href}">{label}</a>', sanitize=False)

      ui.html('<div class="tbd-nav-label">COMMON</div>', sanitize=False)
      for label, href in [
          ("⚙️ 공통 설정", "/settings"),
      ]:
        active_cls = "tbd-nav-link active" if href == active_path else "tbd-nav-link"
        ui.html(f'<a class="{active_cls}" href="{href}">{label}</a>', sanitize=False)

      ui.html('<div class="tbd-nav-label">LINKS</div>', sanitize=False)
      for label, href in [
          ("🛍️ TBD Seoul", "https://smartstore.naver.com/tbdseoul"),
          ("🏬 스마트스토어 센터", "https://smartstore.naver.com"),
          ("🔌 커머스API센터", "https://apicenter.commerce.naver.com"),
      ]:
        ui.html(f'<a class="tbd-nav-link" href="{href}" target="_blank" rel="noopener noreferrer">{label}</a>', sanitize=False)

      ui.html('<a class="tbd-nav-link" href="/logout">🚪 로그아웃</a>', sanitize=False)

    with ui.column().classes("tbd-main gap-0"):
      yield
