"""재고/이력 관리 (/inventory) - 15일 이상 품절 상품 + 최근 가격/재고 변동 이력.

Price_History 테이블(sync_engine.get_long_oos_products/get_price_history)을
근거로 만든 새 페이지. home.py/category.py와 동일한 패턴(layout.frame +
components.topbar)을 따르고, 표는 build_products_table_html이 쓰는 것과 같은
uic-table/uic-pill CSS 클래스(dashboard/theme.py)를 재사용해 톤을 맞춘다.
"""
from __future__ import annotations

from html import escape as html_escape

from nicegui import ui

from sync_engine import (
    _naver_url,
    get_long_oos_products,
    get_price_history,
    safe_fetch_records,
)
from dashboard import components, layout

MIN_OOS_DAYS = 15


def _naver_link_html(naver_id) -> str:
  url = _naver_url(naver_id)
  label = html_escape(str(naver_id)) if naver_id else "-"
  if not url:
    return label
  return f'<a href="{url}" target="_blank">{label}</a>'


def _long_oos_table_html(long_oos: list[dict]) -> str | None:
  if not long_oos:
    return None
  rows = []
  for entry in long_oos:
    rows.append(
        "<tr>"
        f'<td class="uic-sku">{html_escape(entry["sku"])}</td>'
        f'<td><span class="uic-pill cat">{html_escape(entry["category"])}</span></td>'
        f'<td><span class="uic-pill bad">{entry["days_oos"]}일</span></td>'
        f'<td>{_naver_link_html(entry["naver_id"])}</td>'
        "</tr>"
    )
  return f"""
  <div class="uic-table-wrap">
    <div class="uic-table-scroll">
      <table class="uic-table">
        <thead><tr><th>SKU / Model</th><th>Category</th><th>품절 일수</th><th>Naver ID</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </div>
  """


def _unknown_since_table_html(unknown_since: list[dict]) -> str | None:
  if not unknown_since:
    return None
  rows = []
  for entry in unknown_since:
    rows.append(
        "<tr>"
        f'<td class="uic-sku">{html_escape(entry["sku"])}</td>'
        f'<td><span class="uic-pill cat">{html_escape(entry["category"])}</span></td>'
        f'<td><span class="uic-pill check">기록 이전부터 품절</span></td>'
        f'<td>{_naver_link_html(entry["naver_id"])}</td>'
        "</tr>"
    )
  return f"""
  <div class="uic-table-wrap">
    <div class="uic-table-scroll">
      <table class="uic-table">
        <thead><tr><th>SKU / Model</th><th>Category</th><th>상태</th><th>Naver ID</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </div>
  """


def _history_table_html(history: list[dict]) -> str | None:
  if not history:
    return None
  rows = []
  for h in history:
    rows.append(
        "<tr>"
        f'<td>{html_escape(h["changed_at_kst"])}</td>'
        f'<td class="uic-sku">{html_escape(h["sku"])}</td>'
        f'<td><span class="uic-pill cat">{html_escape(h["field_name"])}</span></td>'
        f'<td>{html_escape(str(h["old_value"]))} → {html_escape(str(h["new_value"]))}</td>'
        "</tr>"
    )
  return f"""
  <div class="uic-table-wrap">
    <div class="uic-table-scroll">
      <table class="uic-table">
        <thead><tr><th>시간 (KST)</th><th>상품명</th><th>필드</th><th>변동</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </div>
  """


@ui.page("/inventory")
def inventory_page() -> None:
  with layout.frame(active_path="/inventory"):
    components.topbar("재고 / 이력 관리")

    records = safe_fetch_records(on_error=lambda msg: ui.notify(msg, type="negative"))
    long_oos, unknown_since = get_long_oos_products(records, min_days=MIN_OOS_DAYS)
    history = get_price_history(limit=50)

    ui.label(f"{MIN_OOS_DAYS}일 이상 품절 상품").classes("text-lg font-bold mb-1")
    ui.label(
        "Price_History에 기록된 재고 전이 이력을 근거로 계산됩니다."
    ).classes("text-sm text-tbd-text-secondary mb-4")

    long_oos_html = _long_oos_table_html(long_oos)
    if long_oos_html is None:
      ui.label(f"{MIN_OOS_DAYS}일 이상 품절인 상품이 없습니다.").classes(
          "text-tbd-text-secondary mb-8"
      )
    else:
      ui.html(long_oos_html).classes("mb-8")

    if unknown_since:
      ui.label("기록 이전부터 품절").classes("text-lg font-bold mb-1")
      ui.label(
          "이 기능 도입 이전부터 품절이었던 상품 - 정확한 품절 시작일을 알 수 없습니다."
      ).classes("text-sm text-tbd-text-secondary mb-4")
      ui.html(_unknown_since_table_html(unknown_since)).classes("mb-8")

    ui.label("최근 가격 / 재고 변동").classes("text-lg font-bold mb-1")
    ui.label("최근 50건, 시간순 정렬.").classes("text-sm text-tbd-text-secondary mb-4")

    history_html = _history_table_html(history)
    if history_html is None:
      ui.label("아직 기록된 변동 이력이 없습니다.").classes("text-tbd-text-secondary")
    else:
      ui.html(history_html)
