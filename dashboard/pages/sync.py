"""Sync 제어 페이지 (/sync)."""
from __future__ import annotations

import asyncio

from nicegui import ui

import sync_engine
from sync_engine import RETAILER_NAMES
from dashboard import components, layout, theme
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
    components.topbar("Sync")

    _black_btn = f"!bg-[{theme.BLACK_BTN_BG}] !text-[{theme.BLACK_BTN_TEXT}]"

    with ui.row().classes("w-full items-center gap-2 mb-4").style("display:none") as sync_status_row:
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
      for btn in _sync_buttons:
        btn.disable()
      asyncio.create_task(_run_sync(sync_log, retailers, only_needs_check, label))

    _sync_button("⚡ Sync All Retailers", lambda: _start_sync(RETAILER_NAMES), "w-full")
    _sync_button("🔍 Sync 확인 필요만", lambda: _start_sync(RETAILER_NAMES, only_needs_check=True), "w-full mt-2")

    with ui.row().classes("w-full gap-1 no-wrap mt-2 mb-4"):
      for retailer in RETAILER_NAMES:
        _sync_button(
            retailer,
            lambda r=retailer: _start_sync((r,)),
            "flex-1",
        ).props("size=sm")

    sync_log = ui.log().classes("tbd-sync-log w-full")

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
