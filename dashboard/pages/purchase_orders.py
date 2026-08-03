"""발주 (/purchase) - 주문관리 2단계.

스마트스토어에 들어온 신규 주문 중 아직 현지(미국) 사이트에서 발주하지 않은
건을 찾아 주문정보(발주 사이트/로컬 주문번호/단가)를 등록한다.

**현지배송 등록은 이 페이지가 아니라 /shipping에 있다** - 현지(미국) 배송
송장은 실제로는 배송대행지 신청서 생성·국제배송 송장 등록보다 나중에 나오는
경우가 많아서, 등록 시점 순서상 /shipping의 "국제배송 송장 등록" 다음
단계로 옮겨져 있다.

Order_Fulfillment 데이터는 NocoDB에만 쓰는 가벼운 작업이라(라이브 네이버 API
호출 없음) primary_button을 쓴다 - 되돌리기 쉬움(NocoDB UI에서 바로 삭제 가능).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from html import escape as html_escape

from nicegui import run, ui

import order_fulfillment as of
from sync_engine import _adorama_url, _amazon_url, _bh_url, _unifi_store_url, fmt_usd, safe_fetch_records
from dashboard import components, layout

_PURCHASE_SITES = ["Amazon", "B&H", "Adorama", "공홈"]


def _purchase_items_table_html(orders: list[dict], by_id: dict, nocodb_records: list[dict]) -> str | None:
  """발주 항목 전체(대기+완료)를 리테일러 가격 비교와 함께 보여주는 표.
  가격 셀은 클릭하면 새 탭으로 해당 상품 페이지가 열린다."""
  if not orders:
    return None
  rows = []
  for o in orders:
    order_id = o.get("productOrderId", "")
    product_name = o.get("productName", "")
    match = of.match_sku_for_order(product_name, nocodb_records)
    f = match["fields"] if match else {}
    sku = f.get("SKU") or product_name

    msrp = f.get("MSRP_USD", 0.0) or 0.0
    amazon_usd = f.get("Amazon_USD", 0.0) or 0.0
    adorama_usd = f.get("Adorama_USD", 0.0) or 0.0
    bh_usd = f.get("BH_USD", 0.0) or 0.0

    official_url = _unifi_store_url(f.get("SKU", "")) or f.get("Official_URL")
    amazon_url = _amazon_url(f.get("ASIN"))
    adorama_url = _adorama_url(f.get("ADORAMA_ID"))
    bh_url = _bh_url(f.get("BH_ID"))

    def _price_cell(price, url):
      text = fmt_usd(price) if price else "-"
      if url:
        return f'<a href="{html_escape(url)}" target="_blank" rel="noopener noreferrer">{text}</a>'
      return text

    fulfillment_row = by_id.get(order_id)
    fulfillment = fulfillment_row["fields"] if fulfillment_row else {}
    purchase_status = fulfillment.get("purchase_status")
    if purchase_status == "발주완료":
      status_html = (
          f'<span class="uic-pill ok">발주완료</span> '
          f'{html_escape(fulfillment.get("purchase_site", "") or "")} '
          f'{html_escape(fulfillment.get("local_order_number", "") or "")}'
      )
    else:
      status_html = '<span class="uic-pill check">발주대기</span>'

    orderer_name = fulfillment.get("orderer_name") or o.get("ordererName", "") or "-"

    rows.append(
        "<tr>"
        f'<td>{html_escape(order_id)}</td>'
        f'<td>{html_escape(orderer_name)}</td>'
        f'<td class="uic-sku">{html_escape(sku[:40])}</td>'
        f'<td>{_price_cell(msrp, official_url)}</td>'
        f'<td>{_price_cell(amazon_usd, amazon_url)}</td>'
        f'<td>{_price_cell(adorama_usd, adorama_url)}</td>'
        f'<td>{_price_cell(bh_usd, bh_url)}</td>'
        f'<td>{status_html}</td>'
        "</tr>"
    )
  return f"""
  <div class="uic-table-wrap">
    <div class="uic-table-scroll">
      <table class="uic-table">
        <thead><tr><th>주문번호</th><th>성명</th><th>SKU / Model</th><th>공홈 ($)</th><th>Amazon ($)</th><th>Adorama ($)</th><th>B&H ($)</th><th>발주 상태</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </div>
  """


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
      purchased = 0  # 로컬 주문번호 있음 (이후 단계는 /shipping에서 진행)
      for o in orders:
        order_id = o.get("productOrderId")
        row = by_id.get(order_id)
        fields = row["fields"] if row else {}
        if not fields.get("local_order_number"):
          awaiting_purchase.append(o)
        else:
          purchased += 1

      with stat_row:
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card("발주대기", len(awaiting_purchase), "warning")
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card("발주완료", purchased, "success")

      with content:
        components.section_header(
            "발주 항목 리스트", "리테일러별 가격을 비교하고 클릭하면 새 탭에서 해당 상품 페이지로 이동합니다. 발주완료된 항목도 계속 표시됩니다."
        )
        items_html = _purchase_items_table_html(orders, by_id, nocodb_records)
        if items_html is None:
          ui.label("표시할 발주 항목이 없습니다.").classes("text-sm text-tbd-text-secondary")
        else:
          ui.html(items_html, sanitize=False).classes("w-full mb-8")

        components.section_header("신규 발주 대기", "현지(미국) 사이트에서 주문 완료 후 주문정보를 입력하세요.")
        if not awaiting_purchase:
          ui.label("발주 대기 중인 주문이 없습니다.").classes("text-sm text-tbd-text-secondary")
        for o in awaiting_purchase:
          _render_purchase_row(o, nocodb_records)

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

          fields_to_save = {
              "purchase_site": site_select.value,
              "local_order_number": order_number_input.value,
              "local_order_date": date.today().isoformat(),
              "local_unit_price_usd": price_input.value or 0,
              "purchase_status": "발주완료",
          }

          # 배송대행지 신청서(에코트랜스 xlsx)에 필요한 우편번호/주소/연락처를
          # 네이버 주문 상세에서 가져와 같이 채운다(수령인 이름도 함께 -
          # 개인통관고유부호만은 네이버 API에 없어 여기서 채워지지 않음).
          try:
            import naver_order_api

            recipient = await run.io_bound(naver_order_api.get_recipient_info, order_id)
            # 빈 값(특히 personal_customs_code - 네이버 API엔 애초에 없어 항상
            # 빈 문자열)은 반영하지 않는다 - 재저장 시 기존에 수동으로 채워둔
            # 값을 빈 값으로 덮어쓰지 않기 위함.
            fields_to_save.update({k: v for k, v in recipient.items() if v})
          except Exception as e:  # noqa: BLE001
            print(f"발주 페이지 - 수령인 정보 조회 실패 ({order_id}): {e}")

          of.update_fields(row["id"], fields_to_save)
          ui.notify("발주 정보 저장 완료", type="positive")
          await _refresh()

        components.primary_button("발주 등록", on_click=_save)

    ui.timer(0.1, _refresh, once=True)
