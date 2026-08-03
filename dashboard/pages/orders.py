"""주문 관리 (/orders) - 주문관리 1단계.

스마트스토어에 들어온 주문을 카드 형식으로 보여준다. 각 카드는 주문일시/
주문번호/주문자명/전화번호/주소/개인통관고유부호를 노출하고, 배송 단계
(주문→발주→현지배송→국제배송→통관→국내배송→완료)를 그래픽으로
표시한다. 통합검색으로 여러 필드를 한 번에 검색할 수 있다.

상단엔 7단계 각각의 현재 주문 수를 보여주는 통계 카드가 있고, 조회기간은
프리셋 없이 시작일/종료일을 자유롭게 골라 조회한다(네이버 API 자체는 1회
호출당 최대 24시간만 허용해 내부적으로 day_window 단위로 나눠 호출 - 기간이
길수록 호출 수가 늘어난다). 15건 초과 시 하단에 페이지네이션이 나타난다.

배송 단계 판정 기준(사용자 확정):
- 발주: local_order_number 입력시
- 현지배송: local_tracking_number 입력시
- 국제배송: ACE Express 송장조회 이벤트 "항공기 출발"
- 통관 시작: 이벤트 "항공기 도착"
- 국내배송 시작: 이벤트 "반출" (비고 "KOR")
- 완료: 네이버 주문상태 배송완료/구매확정 또는 ACE 이벤트 "배달완료"
국제배송/통관/국내배송 단계는 매 새로고침마다 ace_express_tracking으로 실제
조회해서 갱신한다 - 단, 국내배송 시작까지 이미 확정된 주문은 더 이상 바뀔
사실이 없으므로(ace_domestic_started_at 저장됨) 재조회를 건너뛴다.

클레임 조회는 이 페이지에서 관리하지 않는다(엔드포인트 자체가 아직 404 -
CLAUDE.md 참고). naver_order_api.py의 클레임 관련 함수는 그대로 남겨두되
(나중에 필요해지면 다시 연결), 이 페이지의 UI에서는 뺀다.
"""
from __future__ import annotations

import asyncio
import math
from datetime import date, datetime, timedelta
from html import escape as html_escape

from nicegui import run, ui

import ace_express_tracking as aet
import order_fulfillment as of
from dashboard import components, layout

_STAGE_LABELS = ["주문", "발주", "현지배송", "국제배송", "통관", "국내배송", "완료"]
_STAGE_TONES = ["", "warning", "accent", "accent", "accent", "accent", "success"]
_PAGE_SIZE = 15

_RECIPIENT_KEYS = (
    "recipient_name_kr", "recipient_phone", "recipient_postal_code",
    "recipient_address", "personal_customs_code",
)

# 네이버 주문 상태 중 "배송완료"로 간주할 값들.
_DELIVERED_STATUSES = ("DELIVERED", "PURCHASE_DECIDED")


def _compute_stage_index(fields: dict, naver_status: str, live_intl_shipped: bool = False) -> int:
    """주문 이행 단계 인덱스(0~6)를 계산. 통관/국내배송 단계는 ACE Express
    실측 이벤트 기준이라 fields에 저장된 ace_* 시각과, 이번 새로고침에서
    막 조회한 live_intl_shipped(아직 저장되지 않은 "항공기 출발만 확인됨"
    상태)를 함께 본다."""
    index = 0
    if fields.get("local_order_number"):
        index = max(index, 1)
    if fields.get("local_tracking_number"):
        index = max(index, 2)
    intl_shipped = live_intl_shipped or bool(fields.get("ace_customs_started_at")) or bool(fields.get("ace_domestic_started_at"))
    if intl_shipped:
        index = max(index, 3)
    if fields.get("ace_customs_started_at"):
        index = max(index, 4)
    if fields.get("ace_domestic_started_at"):
        index = max(index, 5)
    if naver_status in _DELIVERED_STATUSES or fields.get("ace_delivered_at"):
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


def _order_card_html(order: dict, fields: dict, recipient: dict, stage_index: int) -> str:
    order_id = order.get("productOrderId", "")
    product_name = order.get("productName", "")
    order_date = order.get("orderDate", "")[:16]
    orderer_name = recipient.get("recipient_name_kr") or order.get("ordererName", "")
    phone = recipient.get("recipient_phone", "") or "-"
    address = recipient.get("recipient_address", "") or "-"
    customs_code = fields.get("personal_customs_code") or "-"

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


async def _fetch_order_extras(order: dict, fields: dict) -> tuple[dict, dict | None, bool, dict | None]:
    """주문 1건에 필요한 수령인정보/ACE 배송조회를 가져온다.

    수령인정보(주소/전화/이름 - 주문 시점에 확정되어 이후 안 바뀜)는
    Order_Fulfillment에 이미 캐시돼 있으면 그대로 쓰고 네트워크 호출을
    생략한다(사용자 제안 - "배송 크롤링 데이터를 DB에 저장 후 재사용").
    새로 조회한 경우에만 두 번째 반환값(recipient_fresh)에 담아 호출부가
    DB에 써서 다음 로드부턴 캐시가 적중하게 한다.

    이 함수는 여러 주문에 대해 asyncio.gather로 동시에 호출되어야 한다 -
    한 주문씩 순서대로 await하면 전체 로딩 시간이 모든 주문의 네트워크
    왕복시간 합산이 되어버린다(느린 원인의 핵심)."""
    import naver_order_api  # noqa: PLC0415 - lazy import, 위 load_orders 주석 참고

    order_id = order.get("productOrderId", "")

    recipient_fresh: dict | None = None
    if fields.get("recipient_name_kr") or fields.get("recipient_address"):
        recipient = {k: fields.get(k, "") for k in _RECIPIENT_KEYS}
    else:
        try:
            recipient = await run.io_bound(naver_order_api.get_recipient_info, order_id)
            recipient_fresh = recipient
        except Exception as e:  # noqa: BLE001
            print(f"주문 카드 - 수령인 정보 조회 실패 ({order_id}): {e}")
            recipient = {}

    live_intl_shipped = False
    ace_updates: dict | None = None
    intl_no = fields.get("intl_tracking_number")
    if intl_no and not fields.get("ace_domestic_started_at"):
        try:
            events = await run.io_bound(aet.get_tracking_events, intl_no)
        except Exception as e:  # noqa: BLE001
            print(f"ACE Express 조회 실패 ({order_id}/{intl_no}): {e}")
            events = None
        live_intl_shipped = bool(events)
        ace_stage = aet.derive_ace_stage(events)
        ace_updates = {"ace_last_checked_at": datetime.now().isoformat()}
        if ace_stage["customs_started_at"] and not fields.get("ace_customs_started_at"):
            ace_updates["ace_customs_started_at"] = ace_stage["customs_started_at"]
        if ace_stage["domestic_started_at"] and not fields.get("ace_domestic_started_at"):
            ace_updates["ace_domestic_started_at"] = ace_stage["domestic_started_at"]
        if ace_stage["delivered"] and not fields.get("ace_delivered_at"):
            ace_updates["ace_delivered_at"] = datetime.now().isoformat()

    return recipient, recipient_fresh, live_intl_shipped, ace_updates


@ui.page("/orders")
def orders_page() -> None:
    with layout.frame(active_path="/orders"):
        components.topbar("Order Management")

        state: dict = {"enriched": [], "stage_counts": [0] * 7, "page": 1}

        components.section_header("📦 주문 목록")

        stat_row = ui.row().classes("w-full gap-3 mb-8 flex-nowrap overflow-x-auto")

        def _render_stat_cards():
            stat_row.clear()
            with stat_row:
                for label, tone, count in zip(_STAGE_LABELS, _STAGE_TONES, state["stage_counts"]):
                    with ui.column().classes("flex-1 min-w-0"):
                        components.stat_card(label, count, tone)

        with ui.row().classes("w-full gap-4 items-end mb-4"):
            start_date_input = ui.input(
                "시작일", value=(date.today() - timedelta(days=30)).isoformat()
            ).props("type=date").classes("w-40")
            end_date_input = ui.input("종료일", value=date.today().isoformat()).props("type=date").classes("w-40")
            refresh_btn = ui.button("🔄 새로고침").props("outline")
            order_status = ui.label("").classes("text-sm text-tbd-text-secondary")

        search_input = ui.input(
            label="통합검색", placeholder="주문번호/주문자명/전화번호/주소/상품명으로 검색"
        ).classes("w-full mb-4")

        cards_wrap = ui.element("div").classes("w-full")
        pagination_wrap = ui.row().classes("w-full justify-center mt-4")

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
            filtered = [e for e in state["enriched"] if not query or query in e["blob"]]

            total_pages = max(1, math.ceil(len(filtered) / _PAGE_SIZE))
            state["page"] = min(state["page"], total_pages)
            page = state["page"]
            page_items = filtered[(page - 1) * _PAGE_SIZE : page * _PAGE_SIZE]

            cards_wrap.clear()
            with cards_wrap:
                if not state["enriched"]:
                    ui.label("조회된 주문이 없습니다.").classes("text-tbd-text-secondary")
                elif not filtered:
                    ui.label("검색 결과가 없습니다.").classes("text-tbd-text-secondary")
                else:
                    for e in page_items:
                        ui.html(e["html"], sanitize=False)

            pagination_wrap.clear()
            if len(filtered) > _PAGE_SIZE:
                with pagination_wrap:
                    def _on_page_change(e):
                        state["page"] = e.value
                        _render_cards()

                    ui.pagination(1, total_pages, value=page, on_change=_on_page_change)

        def _on_search_change():
            state["page"] = 1
            _render_cards()

        search_input.on("update:model-value", lambda: _on_search_change())

        async def load_orders():
            """주문 목록 로드 - 각 주문의 수령인 정보(우편번호/주소/연락처)를
            네이버 주문 상세에서, 통관/국내배송 단계는 ACE Express 송장조회로
            함께 가져와 Order_Fulfillment 데이터와 교차 참조한다."""
            order_status.text = "로딩 중..."
            refresh_btn.props("loading")

            try:
                # Lazy import - NAS에서는 시크릿이 없어도 대시보드가 기동되게 함
                import naver_order_api

                try:
                    from_date = date.fromisoformat(start_date_input.value)
                except (TypeError, ValueError):
                    from_date = date.today() - timedelta(days=30)
                try:
                    to_date = date.fromisoformat(end_date_input.value)
                except (TypeError, ValueError):
                    to_date = date.today()

                windows = of.date_range_windows(from_date, to_date)

                order_lists: list[list[dict]] = []
                failed_days: list[str] = []
                for i, (from_dt, to_dt) in enumerate(windows):
                    if i > 0:
                        # 네이버 주문 API가 초당 호출 수 제한이 있어(30일 범위 연속
                        # 조회 중 429 Too Many Requests가 실제로 관측됨) 호출 사이에
                        # 짧게 텀을 둔다 - get_product_orders 자체의 429 재시도와
                        # 함께 써야 넓은 기간에서도 안정적으로 전부 조회된다.
                        await asyncio.sleep(0.8)
                    try:
                        data = await run.io_bound(
                            lambda f=from_dt, t=to_dt: naver_order_api.get_product_orders(f, t)
                        )
                        order_lists.append(data.get("content", []))
                    except Exception as e:  # noqa: BLE001
                        print(f"주문 조회 실패 ({from_dt.strftime('%m/%d')}): {e}")
                        failed_days.append(from_dt.strftime("%m/%d"))

                orders = list(of.merge_orders_by_id(order_lists).values())

                fulfillment_rows = of.get_all()
                fulfillment_by_id = {r["fields"].get("naver_product_order_id"): r for r in fulfillment_rows}

                # 주문별 fields 스냅샷을 먼저 뽑아두고, 수령인정보/ACE 조회를
                # asyncio.gather로 전부 동시에 실행한다 - 순서대로 하나씩
                # await하면 전체 로딩 시간이 모든 주문의 네트워크 왕복시간
                # 합산이 되어버려(주문이 많을수록 선형으로 느려짐) 페이지
                # 로딩이 오래 걸리는 원인이었다. 수령인정보는 한 번 조회되면
                # Order_Fulfillment에 캐시되어 재조회 자체가 생략된다.
                order_ctx = []
                for o in orders:
                    row = fulfillment_by_id.get(o.get("productOrderId", ""))
                    fields = dict(row["fields"]) if row else {}
                    order_ctx.append((o, row, fields))

                extras = await asyncio.gather(
                    *(_fetch_order_extras(o, fields) for o, row, fields in order_ctx)
                )

                enriched = []
                stage_counts = [0] * 7
                for (o, row, fields), (recipient, recipient_fresh, live_intl_shipped, ace_updates) in zip(order_ctx, extras):
                    order_id = o.get("productOrderId", "")
                    naver_status = o.get("orderStatus", "")

                    updates = dict(ace_updates) if ace_updates else {}
                    if recipient_fresh:
                        updates.update({k: v for k, v in recipient_fresh.items() if v})
                    if updates:
                        try:
                            if row:
                                await run.io_bound(of.update_fields, row["id"], updates)
                            else:
                                defaults = {
                                    **updates,
                                    "naver_product_name": o.get("productName", ""),
                                    "orderer_name": o.get("ordererName", ""),
                                    "naver_order_date": o.get("orderDate", ""),
                                    "quantity": o.get("quantity", 0),
                                }
                                await run.io_bound(of.find_or_create, order_id, defaults, fulfillment_rows)
                        except Exception as e:  # noqa: BLE001
                            print(f"주문 캐시 저장 실패 ({order_id}): {e}")
                        fields.update(updates)

                    stage_index = _compute_stage_index(fields, naver_status, live_intl_shipped)
                    stage_counts[stage_index] += 1

                    enriched.append({
                        "blob": _search_blob(o, fields, recipient),
                        "html": _order_card_html(o, fields, recipient, stage_index),
                    })

                state["enriched"] = enriched
                state["stage_counts"] = stage_counts
                state["page"] = 1
                _render_stat_cards()
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

        _render_stat_cards()

        # 초기 로드
        ui.timer(0.1, load_orders, once=True)
