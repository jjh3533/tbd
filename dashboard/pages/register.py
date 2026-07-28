"""상품 등록 (/register) - app.py의 "➕ 상품 등록" 페이지 대응.

지금은 기존과 동일하게 NocoDB 추적 테이블에만 기록하는 폼이다 (실제 네이버
등록 파이프라인 main.py 연결은 계획서의 Phase 2에서 진행)."""
from __future__ import annotations

from nicegui import ui

from sync_engine import CATEGORIES, get_current_exchange_rate, table
from dashboard import components, layout


@ui.page("/register")
def register_page() -> None:
  with layout.frame(active_path="/register"):
    components.topbar("Register Product")
    ui.label(
        "모델명과 MSRP(관세 서차지 포함)를 입력하면 Adorama / Amazon / B&H 자동"
        " 모니터링이 시작됩니다."
    ).classes("text-sm text-tbd-text-secondary mb-4")

    with ui.row().classes("w-full gap-8"):
      with ui.column().classes("flex-1 gap-2"):
        sku_input = ui.input("Product Name / SKU *", placeholder="e.g. Ubiquiti Cloud Gateway Ultra").classes("w-full")
        msrp_input = ui.number("MSRP USD (Surcharge Included) *", value=199.0, min=0.0, step=1.0).classes("w-full")
        naver_id_input = ui.input("Naver SmartStore No.", placeholder="e.g. 10293848").classes("w-full")
        category_select = ui.select(CATEGORIES, value=CATEGORIES[0], label="Category").classes("w-full")

      with ui.column().classes("flex-1 gap-2"):
        adorama_input = ui.input("Adorama SKU (Optional)", placeholder="e.g. ubcgultr").classes("w-full")
        asin_input = ui.input("Amazon ASIN (Optional)", placeholder="e.g. B0CWLKD9RP").classes("w-full")
        bh_input = ui.input("B&H ID (Optional)", placeholder="e.g. 1815010-REG").classes("w-full")

    def _submit():
      sku = (sku_input.value or "").strip()
      msrp = msrp_input.value or 0.0
      if not sku or msrp <= 0:
        ui.notify("SKU and valid MSRP are required!", type="negative")
        return

      new_record_data = {
          "SKU": sku,
          "MSRP_USD": float(msrp),
          "Exchange_Rate": get_current_exchange_rate(),
          "Category": category_select.value,
      }
      if adorama_input.value:
        new_record_data["ADORAMA_ID"] = adorama_input.value.strip()
      if asin_input.value:
        new_record_data["ASIN"] = asin_input.value.strip().upper()
      if bh_input.value:
        new_record_data["BH_ID"] = bh_input.value.strip().upper()
      if naver_id_input.value:
        new_record_data["Naver_Product_No"] = naver_id_input.value.strip()

      try:
        table.create(new_record_data)
        ui.notify(f"⚡ [{sku}] successfully added to monitoring matrix!", type="positive")
        sku_input.value = ""
        naver_id_input.value = ""
        adorama_input.value = ""
        asin_input.value = ""
        bh_input.value = ""
      except Exception as e:  # noqa: BLE001
        ui.notify(f"NocoDB Registration Error: {e}", type="negative")

    ui.button("⚡ Add to Inventory System", on_click=_submit).props("unelevated color=primary").classes("mt-4")
