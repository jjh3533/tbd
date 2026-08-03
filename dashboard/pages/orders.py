"""주문 관리 (/orders) - Phase C: 네이버 Pay-Order/Claims API 연동.

주문 목록 조회, 발송 처리, 클레임 관리 기능을 제공한다.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from html import escape as html_escape

from nicegui import run, ui

from sync_engine import _adorama_url, _amazon_url, _bh_url, _unifi_store_url, safe_fetch_records
from order_fulfillment import day_window as _day_window, match_sku_for_order, merge_orders_by_id as _merge_orders_by_id
from dashboard import components, layout


def _price_link_html(product_name: str, records: list[dict]) -> str:
    """주문의 상품명 셀 - 매칭되는 리테일러 URL이 있으면 링크로, 없으면 텍스트로."""
    label = html_escape(product_name[:30])
    record = match_sku_for_order(product_name, records)
    if not record:
        return label
    f = record["fields"]
    url = (
        _unifi_store_url(f.get("SKU", ""))
        or _bh_url(f.get("BH_ID"))
        or _adorama_url(f.get("ADORAMA_ID"))
        or _amazon_url(f.get("ASIN"))
    )
    if not url:
        return label
    return f'<a href="{html_escape(url)}" target="_blank" rel="noopener noreferrer">{label}</a>'


def _orders_table_html(orders: list[dict], records: list[dict]) -> str | None:
    if not orders:
        return None
    rows = []
    for o in orders:
        rows.append(
            "<tr>"
            f'<td class="uic-sku">{html_escape(o.get("productOrderId", ""))}</td>'
            f'<td>{html_escape(o.get("orderDate", "")[:16])}</td>'
            f'<td>{_price_link_html(o.get("productName", ""), records)}</td>'
            f'<td>{o.get("quantity", 0)}</td>'
            f'<td>₩{o.get("totalPaymentAmount", 0):,}</td>'
            f'<td>{html_escape(o.get("ordererName", ""))}</td>'
            f'<td>{html_escape(_format_order_status(o.get("orderStatus", "")))}</td>'
            "</tr>"
        )
    return f"""
  <div class="uic-table-wrap">
    <div class="uic-table-scroll">
      <table class="uic-table">
        <thead><tr><th>주문번호</th><th>주문일시</th><th>상품명</th><th>수량</th><th>결제금액</th><th>주문자</th><th>상태</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </div>
  """


def _claims_table_html(claims: list[dict]) -> str | None:
    if not claims:
        return None
    rows = []
    for c in claims:
        rows.append(
            "<tr>"
            f'<td class="uic-sku">{html_escape(c.get("claimNo", ""))}</td>'
            f'<td>{html_escape(c.get("productOrderId", ""))}</td>'
            f'<td>{html_escape(_format_claim_type(c.get("claimType", "")))}</td>'
            f'<td>{html_escape(_format_claim_status(c.get("claimStatus", "")))}</td>'
            f'<td>{html_escape(c.get("claimRequestDate", "")[:16])}</td>'
            "</tr>"
        )
    return f"""
  <div class="uic-table-wrap">
    <div class="uic-table-scroll">
      <table class="uic-table">
        <thead><tr><th>클레임번호</th><th>주문번호</th><th>유형</th><th>상태</th><th>신청일시</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </div>
  """


@ui.page("/orders")
def orders_page() -> None:
    with layout.frame(active_path="/orders"):
        components.topbar("Order Management")

        # 상태 저장
        state = {
            "orders": [],
            "claims": [],
            "selected_date": datetime.now(),
        }

        # 주문 상품명 → 리테일러 링크 매칭용 NocoDB 레코드 (읽기 전용, 가볍게 1회 조회)
        nocodb_records = safe_fetch_records(on_error=lambda msg: ui.notify(msg, type="negative"))

        # ------------------------------------------------------------------
        # 📦 주문 목록
        # ------------------------------------------------------------------
        components.section_header("📦 주문 목록")

        with ui.row().classes("w-full gap-4 items-end mb-4"):
            # 날짜 선택
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

        order_table_wrap = ui.element("div").classes("w-full")

        # ------------------------------------------------------------------
        # 🔁 클레임 목록
        # ------------------------------------------------------------------
        ui.separator().classes("my-8")
        components.section_header("🔁 클레임 목록")

        claim_table_wrap = ui.element("div").classes("w-full mb-4")

        # ------------------------------------------------------------------
        # 데이터 로드 함수
        # ------------------------------------------------------------------
        async def load_orders():
            """주문 목록 로드."""
            order_status.text = "로딩 중..."
            refresh_btn.props("loading")

            try:
                # Lazy import - NAS에서는 시크릿이 없어도 대시보드가 기동되게 함
                import naver_order_api

                # 날짜 범위 계산. 네이버 API가 한 번에 최대 24시간만 허용해서
                # "최근 7일"은 하루 단위 구간 7개로 나눠 각각 조회한 뒤 합친다
                # (예전엔 UI 라벨과 달리 실제로는 오늘 하루만 조회하고 있었음).
                period = date_select.value
                now = datetime.now()

                if period == "today":
                    windows = [_day_window(now)]
                elif period == "yesterday":
                    windows = [_day_window(now - timedelta(days=1))]
                else:  # last7
                    windows = [_day_window(now - timedelta(days=i)) for i in range(7)]

                order_lists: list[list[dict]] = []
                failed_days: list[str] = []
                for from_date, to_date in windows:
                    try:
                        loop = run.io_bound(
                            lambda f=from_date, t=to_date: naver_order_api.get_product_orders(f, t)
                        )
                        data = await loop
                        order_lists.append(data.get("content", []))
                    except Exception as e:  # noqa: BLE001
                        # 예전엔 여기서 원인을 아예 버려서, ui.run.io_bound가
                        # 이 NiceGUI 버전엔 없는 API(정확히는 nicegui.run.io_bound)라
                        # 매번 조회가 조용히 실패하고 있던 걸 한참 못 알아챘다.
                        print(f"주문 조회 실패 ({from_date.strftime('%m/%d')}): {e}")
                        failed_days.append(from_date.strftime("%m/%d"))

                orders = list(_merge_orders_by_id(order_lists).values())
                state["orders"] = orders

                # 테이블 업데이트
                order_table_wrap.clear()
                with order_table_wrap:
                    table_html = _orders_table_html(orders, nocodb_records)
                    if table_html is None:
                        ui.label("조회된 주문이 없습니다.").classes("text-tbd-text-secondary")
                    else:
                        ui.html(table_html, sanitize=False)

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

        async def load_claims():
            """클레임 목록 로드."""
            try:
                # Lazy import - NAS에서는 시크릿이 없어도 대시보드가 기동되게 함
                import naver_order_api

                now = datetime.now()
                from_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                to_date = from_date + timedelta(hours=23, minutes=59, seconds=59)

                loop = run.io_bound(lambda: naver_order_api.get_product_order_claims(from_date, to_date))
                data = await loop

                claims = data.get("content", [])
                state["claims"] = claims

                claim_table_wrap.clear()
                with claim_table_wrap:
                    table_html = _claims_table_html(claims)
                    if table_html is None:
                        ui.label("조회된 클레임이 없습니다.").classes("text-tbd-text-secondary")
                    else:
                        ui.html(table_html, sanitize=False)

                ui.notify(f"클레임 {len(claims)}건 조회 완료", type="positive")

            except Exception as e:
                ui.notify(f"클레임 조회 실패: {e}", type="negative")

        # ------------------------------------------------------------------
        # 이벤트 핸들러
        # ------------------------------------------------------------------
        async def on_refresh():
            """새로고침 버튼."""
            await load_orders()
            await load_claims()

        refresh_btn.on_click(on_refresh)

        # 초기 로드
        ui.timer(0.1, on_refresh, once=True)


def _format_order_status(status: str) -> str:
    """주문 상태 한글화."""
    status_map = {
        "PAYMENT_WAITING": "결제대기",
        "PAYED": "결제완료",
        "DELIVERING": "배송중",
        "DELIVERED": "배송완료",
        "PURCHASE_DECIDED": "구매확정",
        "EXCHANGED": "교환완료",
        "CANCELED": "취소완료",
        "RETURNED": "반품완료",
    }
    return status_map.get(status, status)


def _format_claim_type(claim_type: str) -> str:
    """클레임 유형 한글화."""
    type_map = {
        "CANCEL": "취소",
        "RETURN": "반품",
        "EXCHANGE": "교환",
    }
    return type_map.get(claim_type, claim_type)


def _format_claim_status(status: str) -> str:
    """클레임 상태 한글화."""
    status_map = {
        "CLAIM_REQUESTED": "신청됨",
        "APPROVAL_WAITING": "승인대기",
        "APPROVED": "승인됨",
        "REJECTED": "거부됨",
        "COMPLETED": "완료",
    }
    return status_map.get(status, status)
