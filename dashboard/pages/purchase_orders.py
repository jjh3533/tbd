"""발주 (/purchase) - 주문관리 2단계.

스마트스토어에 들어온 신규 주문 중 아직 현지(미국) 사이트에서 발주하지 않은
건을 찾아 주문정보(발주 사이트/로컬 주문번호/단가)를 등록하고, 이미 발주한
건은 현지배송 시작 시 현지 배송번호를 입력한다. 현지배송 송장이 입력되면
"현지배송 시작"으로 간주한다 (TBD Pipeline.md의 규칙 그대로).

Order_Fulfillment 데이터는 NocoDB에만 쓰는 가벼운 작업이라(라이브 네이버 API
호출 없음) primary_button을 쓴다 - 되돌리기 쉬움(NocoDB UI에서 바로 삭제 가능).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from nicegui import run, ui

import order_fulfillment as of
from sync_engine import safe_fetch_records
from dashboard import components, layout

_PURCHASE_SITES = ["Amazon", "B&H", "Adorama", "공홈"]


@ui.page("/purchase")
def purchase_orders_page() -> None:
  with layout.frame(active_path="/purchase"):
    components.topbar("발주")

    if of.order_table is None:
      ui.label(
          "⚠️ NOCODB_ORDER_TABLE_ID가 설정되지 않았습니다 - create_order_fulfillment_table.py를 "
          "먼저 실행하고 .env에 값을 추가하세요."
      ).classes("text-negative")
      return

    state: dict = {"orders": [], "fulfillment_by_order_id": {}}

    stat_row = ui.row().classes("w-full gap-5 mb-10")
    content = ui.column().classes("w-full gap-6")

    async def _refresh():
      stat_row.clear()
      content.clear()

      try:
        import naver_order_api
      except Exception as e:  # noqa: BLE001
        with content:
          ui.label(f"네이버 주문 API를 불러올 수 없습니다: {e}").classes("text-negative")
        return

      now = datetime.now()
      windows = [of.day_window(now - timedelta(days=i)) for i in range(7)]
      order_lists = []
      for from_date, to_date in windows:
        try:
          data = await run.io_bound(
              lambda f=from_date, t=to_date: naver_order_api.get_product_orders(f, t)
          )
          order_lists.append(data.get("content", []))
        except Exception as e:  # noqa: BLE001
          print(f"발주 페이지 - 주문 조회 실패 ({from_date.strftime('%m/%d')}): {e}")

      orders = list(of.merge_orders_by_id(order_lists).values())
      state["orders"] = orders

      fulfillment_rows = of.get_all()
      by_id = {r["fields"].get("naver_product_order_id"): r for r in fulfillment_rows}
      state["fulfillment_by_order_id"] = by_id

      nocodb_records = safe_fetch_records(on_error=lambda msg: ui.notify(msg, type="negative"))

      awaiting_purchase = []  # 로컬 주문번호 없음
      awaiting_shipping = []  # 로컬 주문번호는 있는데 현지배송번호 없음
      in_progress = 0
      for o in orders:
        order_id = o.get("productOrderId")
        row = by_id.get(order_id)
        fields = row["fields"] if row else {}
        if not fields.get("local_order_number"):
          awaiting_purchase.append(o)
        elif not fields.get("local_tracking_number"):
          awaiting_shipping.append((o, row))
        else:
          in_progress += 1

      with stat_row:
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card("발주대기", len(awaiting_purchase), "warning")
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card("현지배송 등록대기", len(awaiting_shipping), "accent")
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card("현지배송중 이후", in_progress, "success")

      with content:
        components.section_header("신규 발주 대기", "현지(미국) 사이트에서 주문 완료 후 주문정보를 입력하세요.")
        if not awaiting_purchase:
          ui.label("발주 대기 중인 주문이 없습니다.").classes("text-sm text-tbd-text-secondary")
        for o in awaiting_purchase:
          _render_purchase_row(o, nocodb_records)

        ui.separator().classes("my-6")

        components.section_header("현지배송 등록", "현지배송 송장을 입력하면 '현지배송중'으로 전환됩니다.")
        if not awaiting_shipping:
          ui.label("현지배송 등록 대기 중인 주문이 없습니다.").classes("text-sm text-tbd-text-secondary")
        for o, row in awaiting_shipping:
          _render_shipping_row(o, row)

    def _render_purchase_row(order: dict, nocodb_records: list[dict]):
      order_id = order.get("productOrderId", "")
      product_name = order.get("productName", "")
      match = of.match_sku_for_order(product_name, nocodb_records)
      sku = match["fields"].get("SKU", "") if match else ""

      with ui.row().classes("w-full gap-3 items-end tbd-card").style("padding: 16px;"):
        with ui.column().classes("gap-0"):
          ui.label(product_name[:40]).classes("text-sm font-semibold")
          ui.label(f"주문번호 {order_id} · {sku or '매칭 안 됨'}").classes("text-xs text-tbd-text-secondary")
        site_select = ui.select(_PURCHASE_SITES, value="Amazon", label="구매 사이트").classes("w-32")
        order_number_input = ui.input("로컬 주문번호").classes("w-40")
        price_input = ui.number("단가 (USD)", min=0, step=0.01).classes("w-32")

        async def _save(order_id=order_id, product_name=product_name, sku=sku,
                         site_select=site_select, order_number_input=order_number_input,
                         price_input=price_input):
          if not order_number_input.value:
            ui.notify("로컬 주문번호를 입력하세요.", type="negative")
            return
          defaults = {
              "sku": sku,
              "naver_order_date": order.get("orderDate", ""),
              "naver_product_name": product_name,
              "quantity": order.get("quantity", 0),
              "orderer_name": order.get("ordererName", ""),
              "purchase_status": "발주대기",
          }
          rows = list(state["fulfillment_by_order_id"].values())
          row = of.find_or_create(order_id, defaults, rows)
          of.update_fields(row["id"], {
              "purchase_site": site_select.value,
              "local_order_number": order_number_input.value,
              "local_order_date": date.today().isoformat(),
              "local_unit_price_usd": price_input.value or 0,
              "purchase_status": "발주완료",
          })
          ui.notify("발주 정보 저장 완료", type="positive")
          await _refresh()

        components.primary_button("발주 등록", on_click=_save)

    def _render_shipping_row(order: dict, row: dict):
      order_id = order.get("productOrderId", "")
      product_name = order.get("productName", "")
      fields = row["fields"]

      with ui.row().classes("w-full gap-3 items-end tbd-card").style("padding: 16px;"):
        with ui.column().classes("gap-0"):
          ui.label(product_name[:40]).classes("text-sm font-semibold")
          ui.label(
              f"주문번호 {order_id} · {fields.get('purchase_site', '')} · "
              f"로컬주문번호 {fields.get('local_order_number', '')}"
          ).classes("text-xs text-tbd-text-secondary")
        tracking_input = ui.input("현지 배송번호").classes("w-48")

        async def _save(row=row, tracking_input=tracking_input):
          if not tracking_input.value:
            ui.notify("현지 배송번호를 입력하세요.", type="negative")
            return
          of.update_fields(row["id"], {
              "local_tracking_number": tracking_input.value,
              "purchase_status": "현지배송중",
          })
          ui.notify("현지배송 등록 완료 - 현지배송중으로 전환됩니다.", type="positive")
          await _refresh()

        components.primary_button("배송 등록", on_click=_save)

    ui.timer(0.1, _refresh, once=True)
