"""주문 관리 (/orders) - Phase C: 네이버 Pay-Order/Claims API 연동.

주문 목록 조회, 발송 처리, 클레임 관리 기능을 제공한다.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from nicegui import ui

from dashboard import components, layout


def _day_window(dt: datetime) -> tuple[datetime, datetime]:
    """dt가 속한 하루(00:00~23:59:59)의 (시작, 끝) 튜플. 네이버 API가 최대
    24시간 범위만 허용하므로, 여러 날짜를 조회할 땐 이 단위로 나눠 호출한다."""
    start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(hours=23, minutes=59, seconds=59)


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

        # ------------------------------------------------------------------
        # 📦 주문 목록
        # ------------------------------------------------------------------
        ui.label("📦 주문 목록").classes("text-lg font-semibold mb-2")

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

        # 주문 테이블
        order_table = ui.table(
            columns=[
                {"name": "productOrderId", "label": "주문번호", "field": "productOrderId", "align": "left"},
                {"name": "orderDate", "label": "주문일시", "field": "orderDate", "align": "left"},
                {"name": "productName", "label": "상품명", "field": "productName", "align": "left"},
                {"name": "quantity", "label": "수량", "field": "quantity", "align": "center"},
                {"name": "totalPaymentAmount", "label": "결제금액", "field": "totalPaymentAmount", "align": "right"},
                {"name": "ordererName", "label": "주문자", "field": "ordererName", "align": "left"},
                {"name": "orderStatus", "label": "상태", "field": "orderStatus", "align": "center"},
            ],
            rows=[],
            row_key="productOrderId",
        ).classes("w-full")

        # ------------------------------------------------------------------
        # 🔁 클레임 목록
        # ------------------------------------------------------------------
        ui.separator().classes("my-8")
        ui.label("🔁 클레임 목록").classes("text-lg font-semibold mb-2")

        claim_table = ui.table(
            columns=[
                {"name": "claimNo", "label": "클레임번호", "field": "claimNo", "align": "left"},
                {"name": "productOrderId", "label": "주문번호", "field": "productOrderId", "align": "left"},
                {"name": "claimType", "label": "유형", "field": "claimType", "align": "center"},
                {"name": "claimStatus", "label": "상태", "field": "claimStatus", "align": "center"},
                {"name": "claimRequestDate", "label": "신청일시", "field": "claimRequestDate", "align": "left"},
            ],
            rows=[],
            row_key="claimNo",
        ).classes("w-full mb-4")

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

                orders_by_id: dict[str, dict] = {}
                failed_days: list[str] = []
                for from_date, to_date in windows:
                    try:
                        loop = ui.run.io_bound(
                            lambda f=from_date, t=to_date: naver_order_api.get_product_orders(f, t)
                        )
                        data = await loop
                        for o in data.get("content", []):
                            order_id = o.get("productOrderId")
                            if order_id:
                                orders_by_id[order_id] = o
                    except Exception:
                        failed_days.append(from_date.strftime("%m/%d"))

                orders = list(orders_by_id.values())
                state["orders"] = orders

                # 테이블 업데이트
                order_table.rows = [
                    {
                        "productOrderId": o.get("productOrderId", ""),
                        "orderDate": o.get("orderDate", "")[:16],  # 시간까지만
                        "productName": o.get("productName", "")[:30],  # 최대 30자
                        "quantity": o.get("quantity", 0),
                        "totalPaymentAmount": f"₩{o.get('totalPaymentAmount', 0):,}",
                        "ordererName": o.get("ordererName", ""),
                        "orderStatus": _format_order_status(o.get("orderStatus", "")),
                    }
                    for o in orders
                ]

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

                loop = ui.run.io_bound(lambda: naver_order_api.get_product_order_claims(from_date, to_date))
                data = await loop

                claims = data.get("content", [])
                state["claims"] = claims

                claim_table.rows = [
                    {
                        "claimNo": c.get("claimNo", ""),
                        "productOrderId": c.get("productOrderId", ""),
                        "claimType": _format_claim_type(c.get("claimType", "")),
                        "claimStatus": _format_claim_status(c.get("claimStatus", "")),
                        "claimRequestDate": c.get("claimRequestDate", "")[:16],
                    }
                    for c in claims
                ]

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
