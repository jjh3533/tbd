"""메인 대시보드 (/) - app.py의 is_dashboard 분기 대응."""
from __future__ import annotations

from nicegui import ui

from sync_engine import (
    CATEGORIES,
    exclude_clone_rows,
    get_current_exchange_rate,
    get_exchange_rate_history,
    get_scrapedo_usage,
    safe_fetch_records,
    status_counts,
)
from dashboard import components, layout


@ui.page("/")
def home_page() -> None:
  with layout.frame(active_path="/"):
    components.topbar("Main Dashboard")

    current_rate = get_current_exchange_rate()
    rate_history = get_exchange_rate_history()
    scrapedo_usage = get_scrapedo_usage()

    with ui.row().classes("gap-5 mb-6 items-stretch"):
      with ui.element('div').style('width: 320px; flex-shrink: 0; display: flex; flex-direction: column'):
        components.exchange_rate_line_card(rate_history, current_rate)
      with ui.element('div').style('width: 220px; flex-shrink: 0; display: flex; flex-direction: column'):
        components.scrapedo_donut_card(scrapedo_usage)

    records = exclude_clone_rows(safe_fetch_records(on_error=lambda msg: ui.notify(msg, type="negative")))

    total = len(records)
    active_count, out_stock, check_needed = status_counts(records)
    cat_counts = {c: 0 for c in CATEGORIES}
    for r in records:
      c = r["fields"].get("Category")
      if c in cat_counts:
        cat_counts[c] += 1

    page_by_brand: dict = {
        "UniFi":  {"Detail": 0, "Simple": 0, "None": 0},
        "GL.iNet": {"Detail": 0, "Simple": 0, "None": 0},
    }
    smartstore_sale = 0
    smartstore_out = 0
    for r in records:
      fields = r["fields"]
      brand = fields.get("Brand") or ""
      b_key = "GL.iNet" if "GL" in brand else "UniFi"
      page = fields.get("Product_Page") or ""
      if page in ("Detail", "Simple"):
        page_by_brand[b_key][page] += 1
      else:
        page_by_brand[b_key]["None"] += 1

      # 스마트스토어 상태 집계 (Naver_Product_No가 있는 상품만, Black 버전 제외)
      naver_id = fields.get("Naver_Product_No")
      sku = fields.get("SKU", "")
      if naver_id and str(naver_id).strip() not in ("", "-") and "Black" not in sku:
        sales_status = fields.get("SalesStatus", "")
        if sales_status == "SALE":
          smartstore_sale += 1
        elif sales_status in ("OUTOFSTOCK", "SUSPENSION"):
          smartstore_out += 1

    with ui.row().classes("w-full gap-5 mb-6 items-stretch"):
      with ui.column().classes("flex-1 min-w-0"):
        components.status_donut_card(total, active_count, out_stock, check_needed)
      with ui.column().classes("flex-1 min-w-0"):
        components.page_coverage_bar_card(page_by_brand)
      with ui.column().classes("flex-1 min-w-0"):
        components.smartstore_donut_card(smartstore_sale + smartstore_out, smartstore_sale, smartstore_out)

    components.section_header("카테고리별 현황", "카드를 클릭하면 해당 카테고리의 상품/가격만 모아볼 수 있어요.")

    with ui.grid(columns=4).classes("w-full gap-4"):
      for cat in CATEGORIES:
        components.category_card(cat, cat_counts[cat])
