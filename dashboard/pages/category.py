"""카테고리별 페이지 (/category/{slug}) - app.py의 카테고리 페이지 대응."""
from __future__ import annotations

import re

from nicegui import ui

from sync_engine import (
    CATEGORIES,
    build_products_table_html,
    exclude_clone_rows,
    get_latest_price_deltas,
    safe_fetch_records,
    sort_records_by_name,
    status_counts,
)
from dashboard import components, layout


def category_slug(name: str) -> str:
  return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


_SLUG_TO_CATEGORY = {category_slug(c): c for c in CATEGORIES}


@ui.page("/category/{slug}")
def category_page(slug: str) -> None:
  category = _SLUG_TO_CATEGORY.get(slug)

  with layout.frame(active_path=f"/category/{slug}"):
    if category is None:
      components.topbar("Not Found")
      ui.label(f"알 수 없는 카테고리입니다: {slug}").classes("text-tbd-text-secondary")
      return

    components.topbar(category)

    records = exclude_clone_rows(safe_fetch_records(on_error=lambda msg: ui.notify(msg, type="negative")))
    cat_records = [r for r in records if r["fields"].get("Category") == category]
    cat_records = sort_records_by_name(cat_records)
    active, out_stock, needs_check = status_counts(cat_records)

    with ui.row().classes("w-full gap-5 mb-10"):
      with ui.column().classes("flex-1 min-w-0"):
        components.stat_card("상품 수", len(cat_records))
      with ui.column().classes("flex-1 min-w-0"):
        components.stat_card("판매 가능", active, "success")
      with ui.column().classes("flex-1 min-w-0"):
        components.stat_card("품절", out_stock, "danger")
      with ui.column().classes("flex-1 min-w-0"):
        components.stat_card("확인 필요", needs_check, "warning")

    price_deltas = get_latest_price_deltas()
    table_html = build_products_table_html(
        cat_records, "light", show_category=False, price_deltas=price_deltas
    )
    if table_html is None:
      ui.label("등록된 상품이 없습니다.").classes("text-tbd-text-secondary")
    else:
      ui.html(table_html, sanitize=False)
