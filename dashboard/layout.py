"""사이드바 + 상단 셸. app.py의 render_sidebar()에 대응하되, NiceGUI엔
Streamlit 같은 영속 레이아웃이 없어서 매 페이지가 frame()을 호출해 셸을
새로 그린다.
"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager

from nicegui import app, ui

import sync_engine
from sync_engine import CATEGORIES, RETAILER_NAMES
from dashboard import theme
from dashboard.components import NiceGuiLogAdapter

QUICK_LINKS = {
    "NocoDB": None,  # frame()에서 config.NOCODB_URL로 채움 (import 순환 방지)
    "Scrape.do": "https://scrape.do",
    "GitHub": "https://github.com",
}


def _theme_name() -> str:
  return app.storage.user.get("theme", "light")


def _category_href(name: str) -> str:
  from dashboard.pages.category import category_slug
  return f"/category/{category_slug(name)}"


async def _run_sync(log: ui.log, retailers, only_needs_check=False, label=None):
  """run_tbd_tracker는 (스레드풀로 상품들을 병렬 처리하긴 해도) 그 자체가
  블로킹 함수라, NiceGUI의 단일 이벤트루프 안에서 그냥 호출하면 동기화가
  끝날 때까지 서버 전체가 멈춘다. run_in_executor로 별도 스레드에 던져서
  이벤트루프는 계속 다른 요청을 처리할 수 있게 한다.

  run_sync_guarded를 통해 실행하므로, 이미 다른 동기화(수동/스케줄 무관)가
  진행 중이면 이번 호출은 바로 건너뛰어지고 로그에 안내만 남는다 - 여러 Sync
  버튼을 동시에 눌러서 겹쳐 도는 사고를 방지하기 위함."""
  log.clear()
  adapter = NiceGuiLogAdapter(log)
  loop = asyncio.get_event_loop()
  count = await loop.run_in_executor(
      None, sync_engine.run_sync_guarded, adapter, retailers, only_needs_check, label
  )
  try:
    ui.notify(f"⚡ 동기화 완료 ({count}건 갱신)", type="positive")
  except RuntimeError:
    # 사용자가 이미 페이지를 떠난 경우 무시 (로그엔 이미 완료 메시지가 있음)
    pass


@contextmanager
def frame(active_path: str):
  """사이드바+상단 셸을 그리고, 본문을 채울 컨테이너를 with 블록으로 넘겨준다.

  사용법:
      with layout.frame(active_path="/"):
          ui.label("본문")
  """
  from config import NOCODB_URL
  QUICK_LINKS["NocoDB"] = NOCODB_URL

  ui.add_head_html(theme.build_head_html())
  if _theme_name() == "dark":
    ui.query("body").classes(add="tbd-dark")

  with ui.row().classes("tbd-shell w-full gap-0 no-wrap"):
    with ui.column().classes("tbd-sidebar gap-1"):
      logo_uri = theme.logo_data_uri(_theme_name())
      if logo_uri:
        ui.html(f'<div class="tbd-logo-wrap"><img src="{logo_uri}" alt="TBD Dashboard"/></div>')
      else:
        ui.html('<div class="tbd-logo-wrap">⚡ TBD Dashboard</div>')

      sync_log = ui.log().classes("tbd-sync-log w-full").style("display:none")

      # NiceGUI 버튼은 color prop 없이도 기본 bg-primary 클래스가 붙고,
      # 이게 일반 커스텀 클래스보다 강하게 이겨버려서(이전에 겪은 문제와 동일
      # 원인) Tailwind의 강제 important 유틸리티(!bg-[...])로 덮어써야 함.
      _black_btn = f"!bg-[{theme.BLACK_BTN_BG}] !text-[{theme.BLACK_BTN_TEXT}]"

      # 진행 중 표시(스피너+라벨) + 중지 버튼. 여러 Sync 버튼을 동시에 눌러서
      # 겹쳐 도는 사고를 겪은 뒤 도입 - sync_status_row는 평소엔 숨겨져 있다가
      # 아래 타이머가 sync_engine.is_sync_running()을 감시해서 보여줌/숨김.
      with ui.row().classes("w-full items-center gap-2 mb-2").style("display:none") as sync_status_row:
        ui.spinner(size="sm")
        sync_status_label = ui.label("동기화 중...").classes("text-xs flex-1")
        ui.button(
            "⏹️ 중지", on_click=lambda: sync_engine.request_sync_cancel(),
        ).props("unelevated rounded size=sm color=negative")

      _sync_buttons = []

      def _sync_button(text, on_click, extra_classes=""):
        btn = ui.button(text, on_click=on_click).props("unelevated rounded").classes(
            f"{extra_classes} {_black_btn}"
        )
        _sync_buttons.append(btn)
        return btn

      def _start_sync(retailers, only_needs_check=False, label=None):
        sync_log.style("display:block")
        for btn in _sync_buttons:
          btn.disable()
        asyncio.create_task(_run_sync(sync_log, retailers, only_needs_check, label))

      _sync_button(
          "⚡ Sync All Retailers",
          lambda: _start_sync(RETAILER_NAMES),
          "w-full",
      )
      _sync_button(
          "🔍 Sync 확인 필요만",
          lambda: _start_sync(RETAILER_NAMES, only_needs_check=True),
          "w-full mt-2",
      )

      with ui.row().classes("w-full gap-1 no-wrap mt-2 mb-2"):
        for retailer in RETAILER_NAMES:
          _sync_button(
              retailer,
              lambda r=retailer: _start_sync((r,)),
              "flex-1",
          ).props("size=sm")

      def _poll_sync_status():
        running = sync_engine.is_sync_running()
        sync_status_row.style(f"display:{'flex' if running else 'none'}")
        if running:
          sync_status_label.set_text(f"{sync_engine.get_sync_label()} 동기화 중...")
          for btn in _sync_buttons:
            btn.disable()
        else:
          for btn in _sync_buttons:
            btn.enable()

      ui.timer(1.0, _poll_sync_status)

      ui.html('<div class="tbd-nav-label">메뉴</div>')
      nav_items = [("📊 메인 대시보드", "/")] + [
          (f"　{c}", _category_href(c)) for c in CATEGORIES
      ] + [
          ("➕ 상품 등록", "/register"),
          ("📦 재고/이력 관리", "/inventory"),
          ("⚠️ 확인 필요", "/needs-check"),
      ]
      for label, href in nav_items:
        active_cls = "tbd-nav-link active" if href == active_path else "tbd-nav-link"
        ui.html(f'<a class="{active_cls}" href="{href}">{label}</a>')

      ui.html('<div class="tbd-nav-label">테마</div>')

      def _toggle_theme():
        app.storage.user["theme"] = "dark" if _theme_name() == "light" else "light"
        ui.navigate.reload()

      ui.button(
          "☀️ Light / 🌙 Dark", on_click=_toggle_theme,
      ).props("outline rounded size=sm").classes("w-full")

      ui.html('<div class="tbd-nav-label">바로가기</div>')
      links_html = '<div class="tbd-quicklinks">' + "".join(
          f'<a class="tbd-quicklink" href="{url}" target="_blank">{name}</a>'
          for name, url in QUICK_LINKS.items()
      ) + "</div>"
      ui.html(links_html)

    with ui.column().classes("tbd-main gap-0"):
      yield
