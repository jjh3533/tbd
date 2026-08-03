"""스마트스토어 관리 페이지 (/smartstore) - 네이버 등록 상품 상세 관리."""
from __future__ import annotations

import asyncio

from nicegui import ui

from sync_engine import (
    build_products_table_html,
    get_latest_price_deltas,
    safe_fetch_records,
)
from dashboard import components, layout


async def _confirm(message: str) -> bool:
  """예/아니오 확인 다이얼로그 (register.py의 등록 파이프라인과 동일한 패턴)."""
  with ui.dialog() as dialog, ui.card():
    ui.label(message)
    with ui.row().classes("w-full justify-end gap-2 mt-2"):
      ui.button("취소", on_click=lambda: dialog.submit(False)).props("flat")
      ui.button("확인", on_click=lambda: dialog.submit(True)).props("unelevated color=negative")
  return bool(await dialog)


@ui.page("/smartstore")
def smartstore_page() -> None:
  with layout.frame(active_path="/smartstore"):
    components.topbar("스마트스토어 관리")

    ui.label("네이버 스마트스토어에 등록된 상품 목록").classes("text-lg font-bold mb-1")
    ui.label("판매 상태별 필터링 및 상품 정보를 확인할 수 있어요.").classes(
        "text-sm text-tbd-text-secondary mb-4"
    )

    # 가격/재고 업데이트 안전장치 - 다른 데이터 수정 스크립트와 동일하게
    # dry-run 기본값 + limit + (실제 반영 시) 확인 다이얼로그를 거친다.
    with ui.row().classes("gap-4 mb-2 items-end"):
      price_dry_run = ui.checkbox("Dry-run (미리보기만)", value=True)
      price_limit = ui.number("Limit (빈칸 = 전체)", min=0, step=1, precision=0).classes("w-40")

    # 동기화 버튼 및 상태 표시
    with ui.row().classes("gap-4 mb-4 items-center"):
      sync_status_button = ui.button("네이버 상태 동기화").classes("!bg-[#03c75a] text-white")
      update_price_button = ui.button("가격/재고 업데이트").classes("!bg-blue-600 text-white")
      sync_status_label = ui.label("").classes("text-sm text-gray-500")

    async def run_sync():
      """네이버 상태 동기화 실행 (조회만 하고 SalesStatus를 NocoDB에 반영,
      네이버 쪽에는 아무것도 쓰지 않아 dry-run 개념이 필요 없음)."""
      sync_status_button.disable()
      sync_status_label.text = "상태 동기화 중..."
      sync_status_label.classes("text-sm text-blue-500", remove="text-gray-500 text-red-500 text-green-500")

      try:
        # lazy import로 NAS 환경에서도 에러 방지
        from sync_naver_status import sync_naver_sales_status

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sync_naver_sales_status)

        sync_status_label.text = (
            f"✅ 상태 동기화 완료: {result['updated']}개 업데이트, "
            f"{result['skipped']}개 변경없음, {result['errors']}개 오류"
        )
        sync_status_label.classes("text-sm text-green-600", remove="text-blue-500")
        ui.notify(f"상태 동기화 완료: {result['updated']}개 업데이트", type="positive")

        # 페이지 새로고침 (동기화 후 데이터 반영)
        ui.navigate.reload()

      except ImportError:
        sync_status_label.text = "❌ 네이버 커머스 API 시크릿이 설정되지 않았습니다 (NAS 환경)"
        sync_status_label.classes("text-sm text-red-500", remove="text-blue-500")
        ui.notify("네이버 API 시크릿이 필요합니다", type="negative")
      except Exception as e:
        sync_status_label.text = f"❌ 상태 동기화 실패: {e}"
        sync_status_label.classes("text-sm text-red-500", remove="text-blue-500")
        ui.notify(f"상태 동기화 실패: {e}", type="negative")
      finally:
        sync_status_button.enable()

    async def run_price_update():
      """네이버 가격/재고 업데이트 실행 - 실제로 라이브 API에 쓰는 작업이라
      dry-run이 꺼져있으면 확인 다이얼로그를 먼저 거친다."""
      dry_run = bool(price_dry_run.value)
      if not dry_run and not await _confirm(
          "실제 네이버 가격/재고를 업데이트합니다. 되돌리기 어려우니 먼저 "
          "Dry-run으로 결과를 확인했는지 다시 확인하세요. 계속하시겠습니까?"
      ):
        return

      limit = int(price_limit.value) if price_limit.value else None

      update_price_button.disable()
      sync_status_label.text = f"가격/재고 {'미리보기' if dry_run else '업데이트'} 중..."
      sync_status_label.classes("text-sm text-blue-500", remove="text-gray-500 text-red-500 text-green-500")

      try:
        # lazy import로 NAS 환경에서도 에러 방지
        from sync_naver_price import sync_naver_price_stock

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: sync_naver_price_stock(dry_run=dry_run, limit=limit)
        )

        verb = "미리보기" if dry_run else "업데이트"
        sync_status_label.text = (
            f"✅ 가격/재고 {verb} 완료: {result['updated']}개, "
            f"건너뜀 {result['skipped']}개, 오류 {result['errors']}개"
        )
        sync_status_label.classes("text-sm text-green-600", remove="text-blue-500")
        ui.notify(f"가격/재고 {verb} 완료: {result['updated']}개", type="positive")

        if not dry_run:
          ui.navigate.reload()

      except ImportError:
        sync_status_label.text = "❌ 네이버 커머스 API 시크릿이 설정되지 않았습니다 (NAS 환경)"
        sync_status_label.classes("text-sm text-red-500", remove="text-blue-500")
        ui.notify("네이버 API 시크릿이 필요합니다", type="negative")
      except Exception as e:
        sync_status_label.text = f"❌ 가격/재고 업데이트 실패: {e}"
        sync_status_label.classes("text-sm text-red-500", remove="text-blue-500")
        ui.notify(f"업데이트 실패: {e}", type="negative")
      finally:
        update_price_button.enable()

    sync_status_button.on("click", run_sync)
    update_price_button.on("click", run_price_update)

    # 전체 레코드 조회
    records = safe_fetch_records(on_error=lambda msg: ui.notify(msg, type="negative"))

    # Naver_Product_No가 있는 상품만 필터링 (Black 버전 제외)
    naver_records = [
        r for r in records
        if r["fields"].get("Naver_Product_No")
        and str(r["fields"]["Naver_Product_No"]).strip() not in ("", "-")
        and "Black" not in r["fields"].get("SKU", "")
    ]

    # 상태별 집계
    total = len(naver_records)
    sale_count = len([r for r in naver_records if r["fields"].get("SalesStatus") == "SALE"])
    out_count = len([r for r in naver_records if r["fields"].get("SalesStatus") == "OUTOFSTOCK"])
    suspension_count = len([r for r in naver_records if r["fields"].get("SalesStatus") == "SUSPENSION"])
    unknown_count = total - sale_count - out_count - suspension_count

    # 통계 카드 (가로 배치)
    with ui.row().classes("w-full gap-4 mb-6"):
      with ui.column().classes("flex-1"):
        components.stat_card("전체", total, "")
      with ui.column().classes("flex-1"):
        components.stat_card("판매중", sale_count, "success")
      with ui.column().classes("flex-1"):
        components.stat_card("품절", out_count, "danger")
      with ui.column().classes("flex-1"):
        if suspension_count > 0:
          components.stat_card("판매중지", suspension_count, "warning")
        elif unknown_count > 0:
          components.stat_card("상태 미동기화", unknown_count, "accent")
        else:
          ui.element("div")  # 빈 공간

    # 필터 UI
    with ui.row().classes("w-full gap-4 mb-4 items-center"):
      status_filter = ui.select(
          label="판매 상태",
          options=["전체", "판매중", "품절", "판매중지", "미동기화"],
          value="전체",
      ).classes("w-48")

      search_input = ui.input(label="상품 검색", placeholder="상품명 또는 SKU").classes("flex-1")

    # 테이블 래퍼
    table_wrap = ui.element("div").classes("w-full")

    def refresh_table():
      """필터 적용하여 테이블 새로고침."""
      table_wrap.clear()

      # 필터링
      filtered = naver_records[:]

      # 상태 필터
      status_val = status_filter.value
      if status_val == "판매중":
        filtered = [r for r in filtered if r["fields"].get("SalesStatus") == "SALE"]
      elif status_val == "품절":
        filtered = [r for r in filtered if r["fields"].get("SalesStatus") == "OUTOFSTOCK"]
      elif status_val == "판매중지":
        filtered = [r for r in filtered if r["fields"].get("SalesStatus") == "SUSPENSION"]
      elif status_val == "미동기화":
        filtered = [r for r in filtered if not r["fields"].get("SalesStatus")]

      # 검색어 필터
      search_val = search_input.value.strip().lower()
      if search_val:
        filtered = [
            r for r in filtered
            if search_val in r["fields"].get("SKU", "").lower()
            or search_val in r["fields"].get("Model_Number", "").lower()
        ]

      # 테이블 렌더링
      with table_wrap:
        if not filtered:
          ui.label("조건에 맞는 상품이 없습니다.").classes("text-tbd-text-secondary")
        else:
          price_deltas = get_latest_price_deltas()
          table_html = build_products_table_html(
              filtered, "light", show_category=True, price_deltas=price_deltas
          )
          if table_html:
            ui.html(table_html, sanitize=False)

    # 초기 렌더링
    refresh_table()

    # 필터 변경 시 테이블 새로고침
    status_filter.on("update:model-value", lambda: refresh_table())
    search_input.on("update:model-value", lambda: refresh_table())
