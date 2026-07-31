"""메인 대시보드 (/) - app.py의 is_dashboard 분기 대응."""
from __future__ import annotations

from nicegui import ui

from sync_engine import (
    CATEGORIES,
    build_products_table_html,
    exclude_clone_rows,
    get_current_exchange_rate,
    get_latest_price_deltas,
    get_scrapedo_usage,
    safe_fetch_records,
    sort_records_by_category_then_name,
    status_counts,
)
from dashboard import components, layout
from dashboard.layout import _theme_name


@ui.page("/")
def home_page() -> None:
  with layout.frame(active_path="/"):
    components.topbar("Main Dashboard")

    current_rate = get_current_exchange_rate()
    scrapedo_usage = get_scrapedo_usage()

    with ui.row().classes("w-full gap-10 mb-10"):
      with ui.column().classes("gap-1"):
        ui.label("USD / KRW").classes("text-xs text-tbd-text-secondary")
        ui.label(f"₩ {current_rate:,}").classes("text-2xl font-bold")
      with ui.column().classes("gap-1"):
        ui.label("Scrape.do 잔여 크레딧").classes("text-xs text-tbd-text-secondary")
        if scrapedo_usage:
          remaining = scrapedo_usage.get("RemainingMonthlyRequest", 0)
          max_credits = scrapedo_usage.get("MaxMonthlyRequest", 0)
          pct_left = f"{remaining / max_credits:.0%} 남음" if max_credits else ""
          ui.label(f"{remaining:,}").classes("text-2xl font-bold")
          if pct_left:
            ui.label(pct_left).classes("text-xs text-tbd-text-secondary")
        else:
          ui.label("조회 실패").classes("text-2xl font-bold")

    records = exclude_clone_rows(safe_fetch_records(on_error=lambda msg: ui.notify(msg, type="negative")))

    total = len(records)
    active_count, out_stock, check_needed = status_counts(records)
    cat_counts = {c: 0 for c in CATEGORIES}
    for r in records:
      c = r["fields"].get("Category")
      if c in cat_counts:
        cat_counts[c] += 1

    with ui.row().classes("w-full gap-5 mb-12"):
      for label, value, tone in [
          ("전체 상품", total, ""),
          ("판매 가능 (Active)", active_count, "success"),
          ("품절 (Out of Stock)", out_stock, "danger"),
          ("확인 필요 (Check Needed)", check_needed, "warning"),
          ("카테고리", len([c for c in cat_counts.values() if c > 0]), "accent"),
      ]:
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card(label, value, tone)

    ui.label("카테고리별 현황").classes("text-lg font-bold mb-1")
    ui.label("카드를 클릭하면 해당 카테고리의 상품/가격만 모아볼 수 있어요.").classes(
        "text-sm text-tbd-text-secondary mb-4"
    )

    with ui.grid(columns=4).classes("w-full gap-4 mb-12"):
      for cat in CATEGORIES:
        components.category_card(cat, cat_counts[cat])

    ui.label("전체 상품").classes("text-lg font-bold mb-3")
    sorted_records = sort_records_by_category_then_name(records)
    price_deltas = get_latest_price_deltas()
    table_html = build_products_table_html(
        sorted_records, _theme_name(), show_category=True, price_deltas=price_deltas
    )
    if table_html is None:
      ui.label("등록된 상품이 없습니다.").classes("text-tbd-text-secondary")
    else:
      ui.html(table_html)
