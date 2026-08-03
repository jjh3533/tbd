"""스마트스토어 관리 페이지 (/smartstore) - 네이버 등록 상품 상세 관리 +
등록 파이프라인(원래 /register 페이지 하단에 있었으나, 등록 전 크롤링/검색과
등록 후 운영 작업을 분리하기 위해 이 페이지 상단으로 옮김)."""
from __future__ import annotations

import asyncio
import os
import sys
import threading
from html import escape as html_escape

from nicegui import ui

from sync_engine import (
    build_products_table_html,
    exclude_clone_rows,
    get_latest_price_deltas,
    safe_fetch_records,
)
from dashboard import components, layout

# 등록 파이프라인(main.py/run_pipeline.py/update_price_stock.py) 버튼들의 동시
# 실행 방지용 프로세스 전역 락. 실행 중 재클릭하거나 여러 브라우저 탭에서
# 동시에 눌러도 상품 중복 등록이나 가격 갱신이 겹치지 않도록,
# sync_engine._sync_lock과 동일한 패턴(non-blocking acquire + 전역 상태)을
# 여기서도 사용한다.
_pipeline_lock = threading.Lock()
_pipeline_status = {"running": False, "script": None}

# 완성된 .dc.html 목록(등록대기 매칭용) - detail_page_builder.py와 동일한
# 지연 로드 패턴. build_detail_page 자체는 Playwright 의존성이 없어(PNG export
# 함수를 호출할 때만 subprocess로 쓰임) NAS에서도 안전하게 import 가능하다.
_SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "product_pages", "scripts")


def _load_bdp():
  if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
  import build_detail_page as bdp
  return bdp


def is_pipeline_running() -> bool:
  return _pipeline_status["running"]


def get_pipeline_script():
  return _pipeline_status["script"]


def _match_detail_page(fields: dict, completed_filenames: list[str]) -> str | None:
  """Model_Number/SKU로 완성된 .dc.html 파일명과 best-effort 매칭.
  파일명은 "{브랜드 supply_label} - {title}.dc.html" 형태(build_detail_page.write_page
  참고)라 " - " 뒤 부분만 떼어 비교한다. 확실하지 않으면 None(미매칭)을 돌려준다."""
  candidates = [
      (fields.get("Model_Number") or "").strip().lower(),
      (fields.get("SKU") or "").strip().lower(),
  ]
  candidates = [c for c in candidates if c]
  if not candidates:
    return None
  for fname in completed_filenames:
    stem = fname[:-len(".dc.html")] if fname.endswith(".dc.html") else fname
    title_part = stem.partition(" - ")[2] or stem
    title_part = title_part.lower()
    for cand in candidates:
      if cand in title_part or title_part in cand:
        return fname
  return None


def _pending_registration_table_html(entries: list[dict]) -> str | None:
  """상세페이지는 있지만 아직 네이버에 등록 안 된 상품 목록 (inventory.py의
  _long_oos_table_html과 동일한 uic-table HTML 패턴)."""
  if not entries:
    return None
  rows = []
  for entry in entries:
    rows.append(
        "<tr>"
        f'<td class="uic-sku">{html_escape(entry["sku"])}</td>'
        f'<td><span class="uic-pill cat">{html_escape(entry["brand"] or "-")}</span></td>'
        f'<td><span class="uic-pill cat">{html_escape(entry["category"] or "-")}</span></td>'
        f'<td>{html_escape(entry["filename"])}</td>'
        "</tr>"
    )
  return f"""
  <div class="uic-table-wrap">
    <div class="uic-table-scroll">
      <table class="uic-table">
        <thead><tr><th>SKU / Model</th><th>Brand</th><th>Category</th><th>상세페이지 파일</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
  </div>
  """


@ui.page("/smartstore")
def smartstore_page() -> None:
  with layout.frame(active_path="/smartstore"):
    components.topbar("스마트스토어 관리")

    # ------------------------------------------------------------------
    # 🛠️ 등록 파이프라인
    # ------------------------------------------------------------------
    components.section_header("🛠️ 등록 파이프라인")
    ui.label(
        "엑셀 템플릿 기반 등록/운영 스크립트를 버튼으로 실행합니다. 모든 작업은 실제 네이버 API를 호출하니 신중히 사용하세요. "
        "(가격/재고 반영은 아래 \"네이버 동기화\" 섹션의 버튼 하나로 통합됨)"
    ).classes("text-sm text-tbd-text-secondary mb-4")

    with ui.row().classes("w-full gap-4 items-end mb-4"):
      pipeline_dry_run = ui.checkbox("Dry-run (미리보기만)", value=True)
      pipeline_limit = ui.number("Limit (빈칸 = 전체)", min=0, step=1, precision=0).classes("w-40")

    with ui.row().classes("w-full items-center gap-2 mb-2").style("display:none") as pipeline_status_row:
      ui.spinner(size="sm")
      pipeline_status_label = ui.label("실행 중...").classes("text-xs flex-1")

    with ui.row().classes("w-full gap-4 mb-4 items-start"):
      with ui.column().classes("gap-1"):
        btn_main = components.live_write_button("상품 등록 (main.py)")
        ui.label("엑셀 템플릿(naver_상품등록_템플릿.xlsx)의 신규 상품을 네이버에 등록합니다.").classes(
            "text-xs text-tbd-text-secondary max-w-56"
        )
      with ui.column().classes("gap-1"):
        btn_pipeline = components.live_write_button("전체 파이프라인")
        ui.label("상품 등록 → 채널상품번호 동기화 → 가격/재고 반영을 순서대로 한 번에 실행합니다.").classes(
            "text-xs text-tbd-text-secondary max-w-56"
        )

    _pipeline_buttons = [btn_main, btn_pipeline]

    pipeline_log = ui.log(max_lines=200).classes("tbd-log tbd-log--md w-full")

    async def _run_script(script_name: str, extra_args: list = None):
      """스크립트 실행 헬퍼 - 백그라운드에서 subprocess 실행하고 로그 스트리밍.
      프로세스 전역 락으로 재클릭/다중 탭 동시 실행을 막는다."""
      if not _pipeline_lock.acquire(blocking=False):
        ui.notify(
            f"이미 다른 작업({_pipeline_status['script']})이 실행 중입니다 - 끝난 뒤 다시 시도해주세요.",
            type="warning",
        )
        return

      _pipeline_status["running"] = True
      _pipeline_status["script"] = script_name
      try:
        extra_args = extra_args or []
        cmd = [sys.executable, f"{script_name}.py"]

        if pipeline_dry_run.value:
          cmd.append("--dry-run")

        if pipeline_limit.value and pipeline_limit.value > 0:
          cmd += ["--limit", str(int(pipeline_limit.value))]

        cmd += extra_args

        pipeline_log.clear()
        pipeline_log.push(f"실행 중: {' '.join(cmd)}\n")
        pipeline_log.push("=" * 60 + "\n")

        try:
          process = await asyncio.create_subprocess_exec(
              *cmd,
              stdout=asyncio.subprocess.PIPE,
              stderr=asyncio.subprocess.STDOUT,
              cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
          )

          while True:
            line = await process.stdout.readline()
            if not line:
              break
            pipeline_log.push(line.decode('utf-8', errors='replace'))

          await process.wait()

          if process.returncode == 0:
            pipeline_log.push("\n✅ 완료\n")
            ui.notify("스크립트 실행 완료", type="positive")
          else:
            pipeline_log.push(f"\n⚠️ 종료 코드: {process.returncode}\n")
            ui.notify(f"스크립트가 코드 {process.returncode}로 종료됨", type="warning")
        except Exception as e:
          pipeline_log.push(f"\n❌ 실행 실패: {e}\n")
          ui.notify(f"실행 실패: {e}", type="negative")
      finally:
        _pipeline_status["running"] = False
        _pipeline_status["script"] = None
        _pipeline_lock.release()

    async def _on_main():
      # dry-run은 미리보기일 뿐 실제 API를 호출하지 않으니 확인 없이 바로 실행
      if not pipeline_dry_run.value and not await components.confirm_dialog("실제 네이버 API를 호출합니다. 계속하시겠습니까?"):
        return
      await _run_script("main")

    async def _on_pipeline():
      if not pipeline_dry_run.value and not await components.confirm_dialog("전체 파이프라인을 실행합니다. 계속하시겠습니까?"):
        return
      await _run_script("run_pipeline")

    btn_main.on_click(_on_main)
    btn_pipeline.on_click(_on_pipeline)

    def _poll_pipeline_status():
      running = is_pipeline_running()
      pipeline_status_row.style(f"display:{'flex' if running else 'none'}")
      if running:
        pipeline_status_label.set_text(f"{get_pipeline_script()}.py 실행 중...")
        for btn in _pipeline_buttons:
          btn.disable()
      else:
        for btn in _pipeline_buttons:
          btn.enable()

    ui.timer(1.0, _poll_pipeline_status)

    ui.separator().classes("my-8")

    components.section_header("네이버 스마트스토어에 등록된 상품 목록", "판매 상태별 필터링 및 상품 정보를 확인할 수 있어요.")

    # 가격/재고 업데이트 안전장치 - 다른 데이터 수정 스크립트와 동일하게
    # dry-run 기본값 + limit + (실제 반영 시) 확인 다이얼로그를 거친다.
    with ui.row().classes("gap-4 mb-2 items-end"):
      price_dry_run = ui.checkbox("Dry-run (미리보기만)", value=True)
      price_limit = ui.number("Limit (빈칸 = 전체)", min=0, step=1, precision=0).classes("w-40")

    # 동기화 버튼 및 상태 표시
    with ui.row().classes("gap-4 mb-1 items-start"):
      with ui.column().classes("gap-1"):
        sync_status_button = components.safe_button("네이버 상태 동기화")
        ui.label("네이버 → NocoDB (읽기 전용): 네이버의 실제 판매상태를 조회해 NocoDB에 반영만 합니다. 네이버 쪽 데이터는 바뀌지 않아 안전하게 아무 때나 눌러도 됩니다.").classes(
            "text-xs text-tbd-text-secondary max-w-72"
        )
      with ui.column().classes("gap-1"):
        update_price_button = components.live_write_button("가격/재고 업데이트")
        ui.label("NocoDB → 네이버 (라이브 반영): 등록된 상품 전체의 판매가/재고를 네이버에 실제로 씁니다. 되돌리기 어려우니 먼저 Dry-run으로 확인 후 실행하세요.").classes(
            "text-xs text-tbd-text-secondary max-w-72"
        )
      sync_status_label = ui.label("").classes("text-sm text-gray-500 self-center")

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
      if not dry_run and not await components.confirm_dialog(
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
    fourth_label = "판매중지" if suspension_count > 0 else "상태 미동기화"
    fourth_value = suspension_count if suspension_count > 0 else unknown_count
    fourth_tone = "warning" if suspension_count > 0 else "accent"

    # 등록대기: Naver_Product_No가 없는(=미등록) 상품 중 완성된 .dc.html이
    # 있는 것들 (Clone 색상옵션 로우는 독립 등록 대상이 아니라 제외).
    def _has_naver_id(fields: dict) -> bool:
      v = fields.get("Naver_Product_No")
      return bool(v) and str(v).strip() not in ("", "-")

    unregistered = [r for r in exclude_clone_rows(records) if not _has_naver_id(r["fields"])]
    completed_filenames = _load_bdp().list_completed_pages()
    pending_registration = []
    for r in unregistered:
      fname = _match_detail_page(r["fields"], completed_filenames)
      if fname:
        pending_registration.append({
            "sku": r["fields"].get("SKU", "") or r["fields"].get("Model_Number", ""),
            "brand": r["fields"].get("Brand", ""),
            "category": r["fields"].get("Category", ""),
            "filename": fname,
        })

    # 통계 카드 (가로 배치)
    with ui.row().classes("w-full gap-5 mb-10"):
      with ui.column().classes("flex-1 min-w-0"):
        components.stat_card("전체", total, "")
      with ui.column().classes("flex-1 min-w-0"):
        components.stat_card("판매중", sale_count, "success")
      with ui.column().classes("flex-1 min-w-0"):
        components.stat_card("품절", out_count, "danger")
      with ui.column().classes("flex-1 min-w-0"):
        components.stat_card(fourth_label, fourth_value, fourth_tone)
      with ui.column().classes("flex-1 min-w-0"):
        components.stat_card("등록대기", len(pending_registration), "accent")

    if pending_registration:
      components.section_header("상세페이지는 있지만 아직 등록되지 않은 상품", "완성된 상세페이지를 참고해 등록 파이프라인으로 등록하세요.")
      pending_html = _pending_registration_table_html(pending_registration)
      ui.html(pending_html, sanitize=False).classes("mb-8")

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
