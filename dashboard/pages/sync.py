"""가격 업데이트 (/sync) - Sync 버튼을 카드에 내장한 레이아웃(2026-08-04 개편).

1번째 줄: 상품 수(전체 Sync)/판매 가능/품절/확인 필요(확인 필요만 Sync) 카운팅 카드.
2번째 줄: 리테일러별(Adorama/Amazon/B&H) 개별 Sync 카드 + Scrape.do 크레딧 카드(가로형).
예전에 따로 있던 "⚡ Sync All Retailers"/"🔍 Sync 확인 필요만"/리테일러별 버튼 행은
전부 카드 안으로 흡수되어 제거됨."""
from __future__ import annotations

import asyncio

from nicegui import ui

import sync_engine
from sync_engine import RETAILER_NAMES, get_scrapedo_usage, safe_fetch_records, exclude_clone_rows, status_counts
from dashboard import components, layout
from dashboard.components import NiceGuiLogAdapter


async def _run_sync(log: ui.log, retailers, only_needs_check=False, label=None):
  log.clear()
  adapter = NiceGuiLogAdapter(log)
  loop = asyncio.get_event_loop()
  count = await loop.run_in_executor(
      None, sync_engine.run_sync_guarded, adapter, retailers, only_needs_check, label
  )
  try:
    ui.notify(f"⚡ 동기화 완료 ({count}건 갱신)", type="positive")
  except RuntimeError:
    pass


@ui.page("/sync")
def sync_page() -> None:
  with layout.frame(active_path="/sync"):
    components.topbar("가격 업데이트")

    records = exclude_clone_rows(
        safe_fetch_records(on_error=lambda msg: ui.notify(msg, type="negative"))
    )
    active, out_stock, needs_check = status_counts(records)
    scrapedo_usage = get_scrapedo_usage()

    with ui.row().classes("w-full items-center gap-2 mb-4").style("display:none") as sync_status_row:
      ui.spinner(size="sm")
      sync_status_label = ui.label("동기화 중...").classes("text-xs flex-1")
      ui.button(
          "⏹️ 중지", on_click=lambda: sync_engine.request_sync_cancel(),
      ).props("unelevated rounded size=sm color=negative")

    _sync_buttons = []

    def _start_sync(retailers, only_needs_check=False, label=None):
      for btn in _sync_buttons:
        btn.disable()
      asyncio.create_task(_run_sync(sync_log, retailers, only_needs_check, label))

    with ui.row().classes("w-full gap-5 mb-5 items-stretch"):
      with ui.column().classes("flex-1 min-w-0"):
        _sync_buttons.append(components.stat_card(
            "상품 수", len(records),
            button_label="SYNC", on_click=lambda: _start_sync(RETAILER_NAMES),
        ))
      with ui.column().classes("flex-1 min-w-0"):
        components.stat_card("판매 가능", active, "success")
      with ui.column().classes("flex-1 min-w-0"):
        components.stat_card("품절", out_stock, "danger")
      with ui.column().classes("flex-1 min-w-0"):
        _sync_buttons.append(components.stat_card(
            "확인 필요", needs_check, "warning",
            button_label="SYNC", on_click=lambda: _start_sync(RETAILER_NAMES, only_needs_check=True),
        ))

    with ui.row().classes("w-full gap-5 mb-5 items-stretch"):
      for retailer in RETAILER_NAMES:
        with ui.column().classes("flex-1 min-w-0"):
          _sync_buttons.append(components.stat_card(
              retailer, "", button_label="SYNC",
              on_click=lambda r=retailer: _start_sync((r,)),
          ))
      with ui.column().classes("flex-1 min-w-0"):
        components.scrapedo_donut_card(scrapedo_usage, orientation="horizontal")

    sync_log = ui.log().classes("tbd-log tbd-log--fill w-full")

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
