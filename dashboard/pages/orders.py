"""주문 관리 (/orders) - 주문관리 1단계.

스마트스토어에 들어온 주문을 카드 형식으로 보여준다. 각 카드는 주문일시/
주문번호/주문자명/전화번호/주소/개인통관고유부호를 노출하고, 배송 단계
(주문→발주→현지배송→국제배송→통관→국내배송→배송완료)를 그래픽으로
표시한다. 통합검색으로 여러 필드를 한 번에 검색할 수 있다.

클레임 조회는 이 페이지에서 관리하지 않는다(엔드포인트 자체가 아직 404 -
CLAUDE.md 참고). naver_order_api.py의 클레임 관련 함수는 그대로 남겨두되
(나중에 필요해지면 다시 연결), 이 페이지의 UI에서는 뺀다.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from html import escape as html_escape

from nicegui import run, ui

import order_fulfillment as of
from dashboard import components, layout

_STAGE_LABELS = ["주문", "발주", "현지배송", "국제배송", "통관", "국내배송", "배송완료"]

# 네이버 주문 상태 중 "배송완료"로 간주할 값들.
_DELIVERED_STATUSES = ("DELIVERED", "PURCHASE_DECIDED")


def _compute_stage_index(fields: dict, naver_status: str) -> int:
    """주문 이행 단계 인덱스(0~6)를 계산. 저장된 값이 아니라 매번 계산하는
    이유는 order_fulfillment.derive_fulfillment_status()와 동일 - 데이터가
    쌓이는 순서가 항상 같지 않기 때문(예: 현지배송 송장이 국제배송/배송대행지
    신청보다 늦게 나오는 경우)."""
    index = 0
    if fields.get("local_order_number"):
        index = max(index, 1)
    if fields.get("local_tracking_number"):
        index = max(index, 2)
    if fields.get("intl_tracking_number"):
        index = max(index, 3)
    if fields.get("naver_dispatched_at"):
        # 발송 처리 시점엔 통관(4)까지는 이미 끝난 것으로 간주하고 국내배송(5)까지 표시.
        index = max(index, 5)
    if naver_status in _DELIVERED_STATUSES:
        index = 6
    return index


def _stage_tracker_html(current_index: int) -> str:
    steps = []
    for i, label in enumerate(_STAGE_LABELS):
        done = i <= current_index
        step_cls = "tbd-stage-step done" if done else "tbd-stage-step"
        steps.append(
            f'<div class="{step_cls}"><div class="tbd-stage-dot"></div>'
            f'<div class="tbd-stage-label">{html_escape(label)}</div></div>'
        )
        if i < len(_STAGE_LABELS) - 1:
            connector_done = i < current_index
            connector_cls = "tbd-stage-connector done" if connector_done else "tbd-stage-connector"
            steps.append(f'<div class="{connector_cls}"></div>')
    return f'<div class="tbd-stage-track">{"".join(steps)}</div>'


def _order_card_html(order: dict, fields: dict, recipient: dict, naver_status: str) -> str:
    order_id = order.get("productOrderId", "")
    product_name = order.get("productName", "")
    order_date = order.get("orderDate", "")[:16]
    orderer_name = recipient.get("recipient_name_kr") or order.get("ordererName", "")
    phone = recipient.get("recipient_phone", "") or "-"
    address = recipient.get("recipient_address", "") or "-"
    customs_code = fields.get("personal_customs_code") or "-"

    stage_index = _compute_stage_index(fields, naver_status)

    return f"""
  <div class="tbd-order-card">
    <div class="tbd-order-card-header">
      <div class="tbd-order-card-title">{html_escape(product_name[:50])}</div>
      <div class="tbd-order-card-id">주문번호 {html_escape(order_id)} · {html_escape(order_date)}</div>
    </div>
    <div class="tbd-order-card-grid">
      <div><span class="k">주문자명</span>{html_escape(orderer_name)}</div>
      <div><span class="k">전화번호</span>{html_escape(phone)}</div>
      <div><span class="k">주소</span>{html_escape(address)}</div>
      <div><span class="k">개인통관고유부호</span>{html_escape(customs_code)}</div>
    </div>
    {_stage_tracker_html(stage_index)}
  </div>
  """


@ui.page("/orders")
def orders_page() -> None:
    with layout.frame(active_path="/orders"):
        components.topbar("Order Management")

        state: dict = {"enriched": []}

        components.section_header("📦 주문 목록")

        with ui.row().classes("w-full gap-4 items-end mb-4"):
            date_select = ui.select(
                {
                    "today": "오늘",
                    "yesterday": "어제",
                    "last7": "최근 7일",
                },
                value="today",
                label="조회 기간",
            ).classes("w-40")

            refresh_btn = ui.button("🔄 새로고침").props("outline")
            order_status = ui.label("").classes("text-sm text-tbd-text-secondary")

        search_input = ui.input(
            label="통합검색", placeholder="주문번호/주문자명/전화번호/주소/상품명으로 검색"
        ).classes("w-full mb-4")

        cards_wrap = ui.element("div").classes("w-full")

        def _search_blob(order: dict, fields: dict, recipient: dict) -> str:
            parts = [
                order.get("productOrderId", ""),
                order.get("productName", ""),
                recipient.get("recipient_name_kr") or order.get("ordererName", ""),
                recipient.get("recipient_phone", ""),
                recipient.get("recipient_address", ""),
                fields.get("local_order_number") or "",
            ]
            return " ".join(parts).lower()

        def _render_cards():
            query = (search_input.value or "").strip().lower()
            cards_wrap.clear()
            filtered = [
                e for e in state["enriched"]
                if not query or query in e["blob"]
            ]
            with cards_wrap:
                if not state["enriched"]:
                    ui.label("조회된 주문이 없습니다.").classes("text-tbd-text-secondary")
                elif not filtered:
                    ui.label("검색 결과가 없습니다.").classes("text-tbd-text-secondary")
                else:
                    for e in filtered:
                        ui.html(e["html"], sanitize=False)

        search_input.on("update:model-value", lambda: _render_cards())

        async def load_orders():
            """주문 목록 로드 - 각 주문의 수령인 정보(우편번호/주소/연락처)를
            네이버 주문 상세에서 함께 가져오고, Order_Fulfillment 데이터와
            교차 참조해 배송 단계를 계산한다."""
            order_status.text = "로딩 중..."
            refresh_btn.props("loading")

            try:
                # Lazy import - NAS에서는 시크릿이 없어도 대시보드가 기동되게 함
                import naver_order_api

                period = date_select.value
                now = datetime.now()

                if period == "today":
                    windows = [of.day_window(now)]
                elif period == "yesterday":
                    windows = [of.day_window(now - timedelta(days=1))]
                else:  # last7
                    windows = [of.day_window(now - timedelta(days=i)) for i in range(7)]

                order_lists: list[list[dict]] = []
                failed_days: list[str] = []
                for from_date, to_date in windows:
                    try:
                        data = await run.io_bound(
                            lambda f=from_date, t=to_date: naver_order_api.get_product_orders(f, t)
                        )
                        order_lists.append(data.get("content", []))
                    except Exception as e:  # noqa: BLE001
                        print(f"주문 조회 실패 ({from_date.strftime('%m/%d')}): {e}")
                        failed_days.append(from_date.strftime("%m/%d"))

                orders = list(of.merge_orders_by_id(order_lists).values())

                fulfillment_by_id = {
                    r["fields"].get("naver_product_order_id"): r["fields"]
                    for r in of.get_all()
                }

                enriched = []
                for o in orders:
                    order_id = o.get("productOrderId", "")
                    fields = fulfillment_by_id.get(order_id, {})
                    try:
                        recipient = await run.io_bound(naver_order_api.get_recipient_info, order_id)
                    except Exception as e:  # noqa: BLE001
                        print(f"주문 카드 - 수령인 정보 조회 실패 ({order_id}): {e}")
                        recipient = {}
                    naver_status = o.get("orderStatus", "")
                    enriched.append({
                        "blob": _search_blob(o, fields, recipient),
                        "html": _order_card_html(o, fields, recipient, naver_status),
                    })

                state["enriched"] = enriched
                _render_cards()

                if failed_days:
                    order_status.text = f"총 {len(orders)}건 (⚠️ {', '.join(failed_days)} 조회 실패 - 일부 누락 가능)"
                    ui.notify(f"일부 날짜 조회 실패: {', '.join(failed_days)}", type="warning")
                else:
                    order_status.text = f"총 {len(orders)}건"
                    ui.notify(f"주문 {len(orders)}건 조회 완료", type="positive")

            except Exception as e:
                order_status.text = "조회 실패"
                ui.notify(f"주문 조회 실패: {e}", type="negative")
            finally:
                refresh_btn.props(remove="loading")

        refresh_btn.on_click(load_orders)

        # 초기 로드
        ui.timer(0.1, load_orders, once=True)
