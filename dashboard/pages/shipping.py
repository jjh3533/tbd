"""배송 (/shipping) - 주문관리 3단계.

발주 완료된 주문을 모아 배송대행지(에코트랜스) 신청서 xlsx를 생성하고,
국제배송 송장이 나오면 등록한다. **현지(미국) 배송 송장은 이 두 단계보다
늦게 나오는 경우가 많아서** 순서상 그 다음(국제배송 송장 등록 아래)에
등록하고, 마지막으로 네이버 스마트스토어에 발송 처리를 한다.

"스마트스토어 등록"만 실제 라이브 API 쓰기(되돌리기 어려움)라 live_write_button +
confirm_dialog + 미리보기 토글을 쓴다. xlsx 생성/송장 등록은 NocoDB에만
쓰는 가벼운 작업이라 primary_button."""
from __future__ import annotations

from datetime import date, datetime

from nicegui import ui

import iecot_export
import naver_config
import order_fulfillment as of
from dashboard import components, layout


@ui.page("/shipping")
def shipping_page() -> None:
  with layout.frame(active_path="/shipping"):
    components.topbar("배송")

    if of.order_table is None:
      ui.label(
          "⚠️ NOCODB_ORDER_TABLE_ID가 설정되지 않았습니다 - create_order_fulfillment_table.py를 "
          "먼저 실행하고 .env에 값을 추가하세요."
      ).classes("text-negative")
      return

    stat_row = ui.row().classes("w-full gap-5 mb-10")
    content = ui.column().classes("w-full gap-6")

    def _refresh():
      stat_row.clear()
      content.clear()

      rows = of.get_all()
      awaiting_application = [r for r in rows if r["fields"].get("local_order_number") and not r["fields"].get("iecot_applied_at")]
      awaiting_intl_tracking = [r for r in rows if r["fields"].get("iecot_applied_at") and not r["fields"].get("intl_tracking_number")]
      awaiting_local_tracking = [r for r in rows if r["fields"].get("intl_tracking_number") and not r["fields"].get("local_tracking_number")]
      awaiting_dispatch = [r for r in rows if r["fields"].get("intl_tracking_number") and not r["fields"].get("naver_dispatched_at")]
      dispatched = len([r for r in rows if r["fields"].get("naver_dispatched_at")])

      with stat_row:
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card("배송대행지 신청대기", len(awaiting_application), "warning")
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card("국제송장 등록대기", len(awaiting_intl_tracking), "accent")
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card("현지배송 등록대기", len(awaiting_local_tracking), "accent")
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card("스마트스토어 등록대기", len(awaiting_dispatch), "accent")
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card("발송완료", dispatched, "success")

      with content:
        _render_application_section(awaiting_application)
        ui.separator().classes("my-6")
        _render_intl_tracking_section(awaiting_intl_tracking)
        ui.separator().classes("my-6")
        _render_local_tracking_section(awaiting_local_tracking)
        ui.separator().classes("my-6")
        _render_dispatch_section(awaiting_dispatch)

    def _render_application_section(rows: list[dict]):
      components.section_header(
          "배송대행지 신청서 생성", "체크박스로 원하는 건만 골라 에코트랜스 업로드용 xlsx를 만듭니다."
      )
      if not rows:
        ui.label("신청서 생성 대상이 없습니다.").classes("text-sm text-tbd-text-secondary")
        return

      checkboxes: dict[str, ui.checkbox] = {}
      for r in rows:
        f = r["fields"]
        with ui.row().classes("w-full gap-3 items-center tbd-card").style("padding: 12px 16px;"):
          checkboxes[r["id"]] = ui.checkbox()
          ui.label(f"{f.get('naver_product_name', '')[:40]} · 로컬주문번호 {f.get('local_order_number', '')}").classes(
              "text-sm flex-1"
          )

      def _generate():
        selected = [r for r in rows if checkboxes[r["id"]].value]
        if not selected:
          ui.notify("체크박스로 신청서에 포함할 주문을 선택하세요.", type="negative")
          return
        path = iecot_export.build_iecot_xlsx(selected)
        for r in selected:
          of.update_fields(r["id"], {"iecot_applied_at": datetime.now().isoformat()})
        ui.download(path, filename="iecot_신청서.xlsx")
        ui.notify(f"{len(selected)}건 신청서 생성 완료 - 다운로드된 파일을 에코트랜스에 업로드하세요.", type="positive")
        _refresh()

      components.primary_button("📄 신청서 xlsx 생성", on_click=_generate).classes("mt-2")

    def _render_intl_tracking_section(rows: list[dict]):
      components.section_header("국제배송 송장 등록", "배송대행지에서 국제배송 송장번호(ACE Express)가 나오면 입력하세요.")
      if not rows:
        ui.label("국제송장 등록 대기 중인 주문이 없습니다.").classes("text-sm text-tbd-text-secondary")
        return
      for r in rows:
        f = r["fields"]
        with ui.row().classes("w-full gap-3 items-end tbd-card").style("padding: 16px;"):
          with ui.column().classes("gap-0 flex-1"):
            ui.label(f.get("naver_product_name", "")[:40]).classes("text-sm font-semibold")
            ui.label(f"로컬주문번호 {f.get('local_order_number', '')}").classes("text-xs text-tbd-text-secondary")
          tracking_input = ui.input("국제배송 송장번호").classes("w-48")

          def _save(r=r, tracking_input=tracking_input):
            if not tracking_input.value:
              ui.notify("국제배송 송장번호를 입력하세요.", type="negative")
              return
            of.update_fields(r["id"], {
                "intl_tracking_number": tracking_input.value,
                "intl_tracking_registered_at": datetime.now().isoformat(),
            })
            ui.notify("국제배송 송장 등록 완료", type="positive")
            _refresh()

          components.primary_button("등록", on_click=_save)

    def _render_local_tracking_section(rows: list[dict]):
      components.section_header(
          "현지배송 등록", "현지(미국) 배송 송장이 나오면 입력하세요 - 국제배송 송장 등록 이후에 나오는 경우가 많습니다."
      )
      if not rows:
        ui.label("현지배송 등록 대기 중인 주문이 없습니다.").classes("text-sm text-tbd-text-secondary")
        return
      for r in rows:
        f = r["fields"]
        with ui.row().classes("w-full gap-3 items-end tbd-card").style("padding: 16px;"):
          with ui.column().classes("gap-0 flex-1"):
            ui.label(f.get("naver_product_name", "")[:40]).classes("text-sm font-semibold")
            ui.label(f"국제송장 {f.get('intl_tracking_number', '')}").classes("text-xs text-tbd-text-secondary")
          tracking_input = ui.input("현지 배송번호").classes("w-48")

          def _save(r=r, tracking_input=tracking_input):
            if not tracking_input.value:
              ui.notify("현지 배송번호를 입력하세요.", type="negative")
              return
            of.update_fields(r["id"], {"local_tracking_number": tracking_input.value})
            ui.notify("현지배송 등록 완료", type="positive")
            _refresh()

          components.primary_button("등록", on_click=_save)

    def _render_dispatch_section(rows: list[dict]):
      components.section_header(
          "스마트스토어 등록 (발송 처리)", "국제배송 송장까지 등록된 주문을 네이버에 발송 처리합니다. 실제 라이브 API 호출입니다."
      )
      if not rows:
        ui.label("발송 처리 대기 중인 주문이 없습니다.").classes("text-sm text-tbd-text-secondary")
        return

      preview_only = ui.checkbox("미리보기만 (실제 발송 처리 안 함)", value=True).classes("mb-2")

      for r in rows:
        f = r["fields"]
        with ui.row().classes("w-full gap-3 items-center tbd-card").style("padding: 16px;"):
          with ui.column().classes("gap-0 flex-1"):
            ui.label(f.get("naver_product_name", "")[:40]).classes("text-sm font-semibold")
            ui.label(
                f"주문번호 {f.get('naver_product_order_id', '')} · 국제송장 {f.get('intl_tracking_number', '')}"
            ).classes("text-xs text-tbd-text-secondary")

          async def _dispatch(r=r, f=f):
            payload = {
                "product_order_id": f.get("naver_product_order_id", ""),
                "dispatch_date": date.today().isoformat(),
                "delivery_company": naver_config.DELIVERY_COMPANY,  # "ACE" (ACE Express Inc.) - naver_config.py 참고
                "tracking_number": f.get("intl_tracking_number", ""),
            }
            if preview_only.value:
              ui.notify(f"미리보기: {payload} (실제 호출 안 됨)", type="info")
              return
            if not await components.confirm_dialog(
                "실제로 네이버 스마트스토어에 발송 처리를 등록합니다. 되돌리기 어려우니 먼저 "
                "미리보기로 확인했는지 다시 확인하세요. 계속하시겠습니까?"
            ):
              return
            try:
              import naver_order_api

              result = naver_order_api.dispatch_product_order(**payload)
              of.update_fields(r["id"], {
                  "naver_dispatch_date": payload["dispatch_date"],
                  "naver_dispatch_delivery_company": payload["delivery_company"],
                  "naver_dispatched_at": datetime.now().isoformat(),
                  "naver_dispatch_result": str(result),
              })
              ui.notify("발송 처리 완료", type="positive")
              _refresh()
            except Exception as e:  # noqa: BLE001
              of.update_fields(r["id"], {"naver_dispatch_result": f"실패: {e}"})
              ui.notify(f"발송 처리 실패: {e}", type="negative")

          components.live_write_button("🏪 스마트스토어 등록", on_click=_dispatch)

    _refresh()
