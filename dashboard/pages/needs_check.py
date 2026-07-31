"""확인 필요 상품 모아보기 (/needs-check) - category.py와 동일한 패턴, Category
대신 Needs_Check=True로 필터링."""
from __future__ import annotations

from nicegui import ui

from sync_engine import (
    build_products_table_html,
    exclude_clone_rows,
    get_latest_price_deltas,
    safe_fetch_records,
    sort_records_by_category_then_name,
)
from dashboard import components, layout
from dashboard.layout import _theme_name


@ui.page("/needs-check")
def needs_check_page() -> None:
  with layout.frame(active_path="/needs-check"):
    components.topbar("확인 필요 상품")

    records = exclude_clone_rows(safe_fetch_records(on_error=lambda msg: ui.notify(msg, type="negative")))
    check_records = [r for r in records if r["fields"].get("Needs_Check")]
    check_records = sort_records_by_category_then_name(check_records)

    with ui.column().classes("gap-1 mb-10"):
      components.stat_card("확인 필요", len(check_records), "warning")

    ui.label(
        "사이트 접속/파싱 실패로 재고 상태를 확정 못 한 상품들입니다. "
        "가격/재고 셀에 마우스를 올리면 어떤 리테일러가 실패했는지 보여줍니다."
    ).classes("text-sm text-tbd-text-secondary mb-4")

    price_deltas = get_latest_price_deltas()
    table_html = build_products_table_html(
        check_records, _theme_name(), show_category=True, price_deltas=price_deltas
    )
    if table_html is None:
      ui.label("확인이 필요한 상품이 없습니다.").classes("text-tbd-text-secondary")
    else:
      ui.html(table_html)
