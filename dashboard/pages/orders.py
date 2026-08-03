"""주문 관리 (/orders) - 주문관리 1단계.

스마트스토어에 들어온 주문을 카드 형식으로 보여준다. 각 카드는 주문일시/
주문번호/주문자명/전화번호/주소/개인통관고유부호를 노출하고, 배송 단계
(주문→발주→현지배송→국제배송→통관→국내배송→완료)를 그래픽으로
표시한다. 통합검색으로 여러 필드를 한 번에 검색할 수 있다.

상단엔 7단계 각각의 현재 주문 수를 보여주는 통계 카드가 있고, 조회기간은
프리셋 없이 시작일/종료일을 자유롭게 골라 조회한다. 15건 초과 시 하단에
페이지네이션이 나타난다.

**페이지 열람/새로고침은 Order_Fulfillment(NocoDB)만 읽는다 - 네이버·ACE
Express를 호출하지 않는다**(사용자 확정, 2026-08-03: "페이지를 열거나
새로고침을 누르면 외부 API를 호출하는 건 말이 안 되는 구조"). 실제 네이버
주문 목록/수령인정보/ACE 배송조회를 하고 그 결과를 DB에 반영하는 건 별도
"☁️ 네이버·배송 동기화" 버튼(`sync_orders`)만의 역할 - 이 버튼을 눌러야
새 주문이 생기거나 배송 단계가 진행된다. `load_from_db`는 그 결과를 읽어
보여주기만 한다.

배송 단계 판정 기준(사용자 확정):
- 발주: local_order_number 입력시
- 현지배송: local_tracking_number 입력시
- 국제배송: ACE Express 송장조회 이벤트가 처음 확인된 시각(ace_intl_shipped_at)
- 통관 시작: 이벤트 "항공기 도착" (ace_customs_started_at)
- 국내배송 시작: 이벤트 "반출" (비고 "KOR", ace_domestic_started_at)
- 완료: 네이버 주문상태(naver_order_status) 배송완료/구매확정 또는 ACE
  이벤트 "배달완료"(ace_delivered_at)
이 시각들은 전부 `sync_orders`가 동기화할 때만 갱신되고, 국내배송 시작까지
이미 확정된 주문은 더 이상 바뀔 사실이 없으므로(ace_domestic_started_at
저장됨) 재조회를 건너뛴다.

클레임 조회는 이 페이지에서 관리하지 않는다(엔드포인트 자체가 아직 404 -
CLAUDE.md 참고). naver_order_api.py의 클레임 관련 함수는 그대로 남겨두되
(나중에 필요해지면 다시 연결), 이 페이지의 UI에서는 뺀다.
"""
from __future__ import annotations

import asyncio
import math
from datetime import date, datetime, timedelta
from html import escape as html_escape

import pytz
from nicegui import run, ui

import ace_express_tracking as aet
import order_fulfillment as of
from dashboard import components, layout

_KST = pytz.timezone("Asia/Seoul")

_STAGE_LABELS = ["주문", "발주", "현지배송", "국제배송", "통관", "국내배송", "완료"]
_STAGE_TONES = ["", "warning", "accent", "accent", "accent", "accent", "success"]
_PAGE_SIZE = 15

_RECIPIENT_KEYS = (
    "recipient_name_kr", "recipient_phone", "recipient_postal_code",
    "recipient_address", "personal_customs_code",
)

# 네이버 주문 상태 중 "배송완료"로 간주할 값들.
_DELIVERED_STATUSES = ("DELIVERED", "PURCHASE_DECIDED")


def _compute_stage_index(fields: dict) -> int:
    """주문 이행 단계 인덱스(0~6)를 Order_Fulfillment에 저장된 값만으로
    계산한다 - 라이브 조회는 하지 않는다(동기화 버튼이 미리 채워둔 값을
    읽기만 함)."""
    index = 0
    if fields.get("local_order_number"):
        index = max(index, 1)
    if fields.get("local_tracking_number"):
        index = max(index, 2)
    if fields.get("ace_intl_shipped_at") or fields.get("ace_customs_started_at") or fields.get("ace_domestic_started_at"):
        index = max(index, 3)
    if fields.get("ace_customs_started_at"):
        index = max(index, 4)
    if fields.get("ace_domestic_started_at"):
        index = max(index, 5)
    if fields.get("naver_order_status") in _DELIVERED_STATUSES or fields.get("ace_delivered_at"):
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


def _parse_order_datetime(raw: str) -> datetime | None:
    """Order_Fulfillment의 naver_order_date를 KST aware datetime으로 변환.

    NocoDB DateTime 필드는 저장 시 UTC로 정규화해서 돌려준다(네이버 API가
    준 KST 오프셋 문자열을 그대로 저장한 게 아님) - 이걸 그대로 슬라이싱해
    표시/필터링하면 시각이 9시간 밀려 보인다(실제로 겪음). 항상 KST로
    변환한 뒤에 쓴다."""
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return _KST.localize(dt)
    return dt.astimezone(_KST)


def _order_card_html(fields: dict, stage_index: int) -> str:
    order_id = fields.get("naver_product_order_id", "")
    product_name = fields.get("naver_product_name", "")
    order_dt = _parse_order_datetime(fields.get("naver_order_date", ""))
    order_date = order_dt.strftime("%Y-%m-%d %H:%M") if order_dt else ""
    orderer_name = fields.get("recipient_name_kr") or fields.get("orderer_name", "")
    phone = fields.get("recipient_phone") or "-"
    address = fields.get("recipient_address") or "-"
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


async def _fetch_order_extras(order: dict, fields: dict) -> tuple[dict, dict | None, dict | None]:
    """주문 1건에 필요한 수령인정보/ACE 배송조회를 가져온다. `sync_orders`
    (☁️ 네이버·배송 동기화 버튼)에서만 호출된다 - 페이지 열람/새로고침은
    이 함수를 아예 부르지 않고 DB만 읽는다.

    수령인정보(주소/전화/이름 - 주문 시점에 확정되어 이후 안 바뀜)는
    Order_Fulfillment에 이미 캐시돼 있으면 그대로 쓰고 네트워크 호출을
    생략한다. 새로 조회한 경우에만 두 번째 반환값(recipient_fresh)에 담아
    호출부가 DB에 써서 다음 동기화부턴 캐시가 적중하게 한다.

    이 함수는 여러 주문에 대해 asyncio.gather로 동시에 호출되어야 한다 -
    한 주문씩 순서대로 await하면 전체 동기화 시간이 모든 주문의 네트워크
    왕복시간 합산이 되어버린다."""
    import naver_order_api  # noqa: PLC0415 - lazy import, 아래 sync_orders 주석 참고

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

    ace_updates: dict | None = None
    intl_no = fields.get("intl_tracking_number")
    if intl_no and not fields.get("ace_domestic_started_at"):
        try:
            events = await run.io_bound(aet.get_tracking_events, intl_no)
        except Exception as e:  # noqa: BLE001
            print(f"ACE Express 조회 실패 ({order_id}/{intl_no}): {e}")
            events = None
        ace_stage = aet.derive_ace_stage(events)
        ace_updates = {"ace_last_checked_at": datetime.now().isoformat()}
        if events and not fields.get("ace_intl_shipped_at"):
            ace_updates["ace_intl_shipped_at"] = datetime.now().isoformat()
        if ace_stage["customs_started_at"] and not fields.get("ace_customs_started_at"):
            ace_updates["ace_customs_started_at"] = ace_stage["customs_started_at"]
        if ace_stage["domestic_started_at"] and not fields.get("ace_domestic_started_at"):
            ace_updates["ace_domestic_started_at"] = ace_stage["domestic_started_at"]
        if ace_stage["delivered"] and not fields.get("ace_delivered_at"):
            ace_updates["ace_delivered_at"] = datetime.now().isoformat()

    return recipient, recipient_fresh, ace_updates


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
            sync_btn = components.safe_button("☁️ 네이버·배송 동기화")
            order_status = ui.label("").classes("text-sm text-tbd-text-secondary")
        ui.label(
            "새로고침은 저장된 데이터만 보여줍니다 - 새 주문을 받아오거나 배송 단계를 갱신하려면 동기화를 눌러주세요."
        ).classes("text-xs text-tbd-text-secondary -mt-3 mb-4")

        search_input = ui.input(
            label="통합검색", placeholder="주문번호/주문자명/전화번호/주소/상품명으로 검색"
        ).classes("w-full mb-4")

        cards_wrap = ui.element("div").classes("w-full")
        pagination_wrap = ui.row().classes("w-full justify-center mt-4")

        def _search_blob(fields: dict) -> str:
            parts = [
                fields.get("naver_product_order_id", ""),
                fields.get("naver_product_name", ""),
                fields.get("recipient_name_kr") or fields.get("orderer_name", ""),
                fields.get("recipient_phone", ""),
                fields.get("recipient_address", ""),
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

        def _selected_date_range() -> tuple[date, date]:
            try:
                from_date = date.fromisoformat(start_date_input.value)
            except (TypeError, ValueError):
                from_date = date.today() - timedelta(days=30)
            try:
                to_date = date.fromisoformat(end_date_input.value)
            except (TypeError, ValueError):
                to_date = date.today()
            return from_date, to_date

        async def load_from_db():
            """Order_Fulfillment를 읽기만 한다 - 네이버/ACE 호출 없음.
            페이지 최초 진입과 "새로고침" 버튼 둘 다 이 함수만 부른다."""
            order_status.text = "로딩 중..."
            refresh_btn.props("loading")
            try:
                from_date, to_date = _selected_date_range()

                rows = await run.io_bound(of.get_all)
                dated_rows = []
                for r in rows:
                    fields = r["fields"]
                    if not fields.get("naver_product_order_id"):
                        continue
                    dt = _parse_order_datetime(fields.get("naver_order_date", ""))
                    if dt is None or not (from_date <= dt.date() <= to_date):
                        continue
                    dated_rows.append((dt, fields))
                dated_rows.sort(key=lambda x: x[0], reverse=True)

                enriched = []
                stage_counts = [0] * 7
                for _d, fields in dated_rows:
                    stage_index = _compute_stage_index(fields)
                    stage_counts[stage_index] += 1
                    enriched.append({
                        "blob": _search_blob(fields),
                        "html": _order_card_html(fields, stage_index),
                    })

                state["enriched"] = enriched
                state["stage_counts"] = stage_counts
                state["page"] = 1
                _render_stat_cards()
                _render_cards()
                order_status.text = f"총 {len(enriched)}건 (저장된 데이터)"

            except Exception as e:
                order_status.text = "조회 실패"
                ui.notify(f"주문 조회 실패: {e}", type="negative")
            finally:
                refresh_btn.props(remove="loading")

        async def sync_orders():
            """네이버 주문 목록 + 수령인정보 + ACE Express 배송조회를 실제로
            조회해 Order_Fulfillment에 반영한다. 사용자 명시 요청(2026-08-03) -
            페이지 열람/새로고침은 절대 이 함수를 부르지 않고, 이 버튼을 눌러야만
            외부 API가 호출된다."""
            order_status.text = "동기화 중..."
            sync_btn.props("loading")
            refresh_btn.props("disable")

            try:
                # Lazy import - NAS에서는 시크릿이 없어도 대시보드가 기동되게 함
                import naver_order_api

                from_date, to_date = _selected_date_range()
                windows = of.date_range_windows(from_date, to_date)

                # 날짜창(하루 단위)을 하나씩 순서대로 호출 + 0.8초 텀을 두던 방식은
                # 30일 기본 범위 기준 30번의 왕복 + 29 * 0.8초 = 20초 이상이 그냥
                # 대기시간으로 날아가는 원인이었다. 세마포어로 동시 호출 수를 3개로
                # 제한해 병렬 조회하되, 완전 무제한 동시요청은 피한다 - 예전에 텀
                # 없이 31개를 한꺼번에 쏴서 429가 대량 발생한 적이 있어(HISTORY 81)
                # 그 재현을 막기 위한 최소한의 안전장치. 개별 호출의 지수 백오프
                # 재시도(get_product_orders 자체 내장)가 남은 429를 흡수한다.
                _window_sem = asyncio.Semaphore(3)

                async def _fetch_window(from_dt, to_dt):
                    async with _window_sem:
                        return await run.io_bound(
                            lambda f=from_dt, t=to_dt: naver_order_api.get_product_orders(f, t)
                        )

                window_results = await asyncio.gather(
                    *(_fetch_window(f, t) for f, t in windows), return_exceptions=True
                )

                order_lists: list[list[dict]] = []
                failed_days: list[str] = []
                for (from_dt, to_dt), result in zip(windows, window_results):
                    if isinstance(result, Exception):
                        print(f"주문 조회 실패 ({from_dt.strftime('%m/%d')}): {result}")
                        failed_days.append(from_dt.strftime("%m/%d"))
                    else:
                        order_lists.append(result.get("content", []))

                orders = list(of.merge_orders_by_id(order_lists).values())

                fulfillment_rows = await run.io_bound(of.get_all)
                fulfillment_by_id = {r["fields"].get("naver_product_order_id"): r for r in fulfillment_rows}

                # 주문별 fields 스냅샷을 먼저 뽑아두고, 수령인정보/ACE 조회를
                # asyncio.gather로 전부 동시에 실행한다 - 순서대로 하나씩
                # await하면 전체 동기화 시간이 모든 주문의 네트워크 왕복시간
                # 합산이 되어버린다. 수령인정보는 한 번 조회되면 Order_Fulfillment에
                # 캐시되어 다음 동기화부턴 재조회 자체가 생략된다.
                order_ctx = []
                for o in orders:
                    row = fulfillment_by_id.get(o.get("productOrderId", ""))
                    fields = dict(row["fields"]) if row else {}
                    order_ctx.append((o, row, fields))

                extras = await asyncio.gather(
                    *(_fetch_order_extras(o, fields) for o, row, fields in order_ctx)
                )

                synced = 0
                for (o, row, fields), (recipient, recipient_fresh, ace_updates) in zip(order_ctx, extras):
                    order_id = o.get("productOrderId", "")
                    new_status = o.get("orderStatus", "")

                    updates = dict(ace_updates) if ace_updates else {}
                    if recipient_fresh:
                        updates.update({k: v for k, v in recipient_fresh.items() if v})
                    if new_status and fields.get("naver_order_status") != new_status:
                        updates["naver_order_status"] = new_status

                    try:
                        if row:
                            if updates:
                                await run.io_bound(of.update_fields, row["id"], updates)
                        else:
                            # 이 주문의 로우가 아직 없다면(발주 전 신규주문) 부가정보
                            # 조회 성공 여부와 무관하게 항상 최소 필드로 로우를 만든다
                            # - 안 그러면 DB만 읽는 load_from_db()에서 이 주문 자체가
                            # 보이지 않게 된다.
                            defaults = {
                                **updates,
                                "naver_product_name": o.get("productName", ""),
                                "orderer_name": o.get("ordererName", ""),
                                "naver_order_date": o.get("orderDate", ""),
                                "quantity": o.get("quantity", 0),
                                "naver_order_status": new_status,
                            }
                            await run.io_bound(of.find_or_create, order_id, defaults, fulfillment_rows)
                        synced += 1
                    except Exception as e:  # noqa: BLE001
                        print(f"주문 캐시 저장 실패 ({order_id}): {e}")

                if failed_days:
                    ui.notify(f"일부 날짜 조회 실패: {', '.join(failed_days)} (새로고침으로 다시 시도해보세요)", type="warning")
                ui.notify(f"동기화 완료: {synced}/{len(orders)}건 반영", type="positive")

            except Exception as e:
                order_status.text = "동기화 실패"
                ui.notify(f"동기화 실패: {e}", type="negative")
            finally:
                sync_btn.props(remove="loading")
                refresh_btn.props(remove="disable")

            await load_from_db()

        refresh_btn.on_click(load_from_db)
        sync_btn.on_click(sync_orders)

        _render_stat_cards()

        # 초기 로드 - DB만 읽는다(네이버/ACE 호출 없음)
        ui.timer(0.1, load_from_db, once=True)
