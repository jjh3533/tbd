"""상세페이지 편집 (/detail-page-editor) - "➕ 신규등록" 하위메뉴 2.

상세페이지 제작(하위메뉴 1)에서 만든 HTML 초안을 코드 에디터로 직접
다듬고, PNG export까지 마무리하는 페이지(2026-08-04 신설). 라이브
상세페이지는 860px 고정폭 + 인라인 스타일 + 커스텀 폰트로 짜인 정밀한
컴포넌트 마크업이라, Quill/TinyMCE 같은 WYSIWYG 리치텍스트 에디터를 쓰면
저장 시 자체 문서 모델로 재직렬화되면서 구조가 깨질 위험이 크다 - 그래서
원본을 그대로 보여주고 그대로 저장하는 NiceGUI 내장 `ui.codemirror`(HTML
문법 하이라이팅)를 쓴다(추가 pip 설치 불필요, 무손실).

**PNG export가 끝나야 그 상품의 NocoDB Product_Page를 "Detail"로 반영한다**
(사용자 확정, 2026-08-04) - "HTML 생성"(하위메뉴 1)이 아니라 여기가 실제
완성 시점이라는 판단. 파일명("{SKU}.html")에서 확장자만 뗀 게 곧 SKU라
`build_detail_page.find_nocodb_record()`로 바로 매칭한다.

미리보기 정적 서빙(`/detail-pages/...`)도 이 페이지가 등록한다 - 예전엔
detail_page_builder.py가 등록했지만 "완성된 상세페이지 보기" 기능 자체가
이 페이지로 옮겨왔다."""
from __future__ import annotations

import asyncio
import os
import sys
import urllib.parse

from nicegui import app, ui

import naver_config
from sync_engine import safe_fetch_records, table as products_table
from dashboard import components, layout

_SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "product_pages", "scripts")

# Synology CloudSync로 NAS에도 동기화되어 있어(TBD_SEOUL_ROOT 참고, 다만
# CloudSync 반영이 늦거나 안 될 때가 있었음 - CLAUDE.md 참고) my.tbd.kr에서도
# 미리보기가 그대로 동작한다.
_PAGES_ROOT = os.path.dirname(naver_config.PRODUCT_PAGES_DIR)
_PREVIEW_URL_PREFIX = "/detail-pages"

if os.path.isdir(_PAGES_ROOT):
  app.add_static_files(_PREVIEW_URL_PREFIX, _PAGES_ROOT)


def _load_bdp():
  """build_detail_page는 product_pages/scripts/에 있어서 기본 sys.path에 없다."""
  if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
  import build_detail_page as bdp
  return bdp


@ui.page("/detail-page-editor")
def detail_page_editor_page(file: str = "") -> None:
  """`file` 쿼리파라미터(예: /detail-page-editor?file=UniFi%20Pro%20Max%2016.html)로
  진입하면 그 파일을 바로 불러온다 - 상세페이지 제작 페이지의 "✏️ HTML 편집"
  버튼이 이 방식으로 넘어온다."""
  with layout.frame(active_path="/detail-page-editor"):
    components.topbar("상세페이지 편집")

    state: dict = {"filename": None}

    with ui.row().classes("w-full gap-4 items-end mb-2"):
      file_select = ui.select(_load_bdp().list_completed_pages(), label="완성된 상세페이지").classes("flex-1")
      refresh_button = ui.button("목록 새로고침").props("outline")
      load_button = ui.button("불러오기").props("outline")

    status_label = ui.label("먼저 상세페이지를 불러오세요.").classes("text-sm text-tbd-text-secondary mb-2")

    editor = ui.codemirror(language="HTML", theme="vscodeLight").classes("w-full").style("height: 600px;")

    with ui.row().classes("w-full gap-3 mt-4"):
      save_button = components.primary_button("💾 저장하기")
      preview_button = ui.button("🔍 미리보기").props("outline")
      export_button = components.primary_button("PNG로 Export")

    build_log = ui.log(max_lines=100).classes("tbd-log tbd-log--sm w-full mt-2")
    preview_gallery = ui.row().classes("w-full gap-3 flex-wrap mt-2")

    def _refresh_file_list():
      file_select.options = _load_bdp().list_completed_pages()
      file_select.update()

    def _do_refresh_list():
      _refresh_file_list()
      ui.notify(f"{len(file_select.options)}개 발견", type="positive")

    refresh_button.on_click(_do_refresh_list)

    def _load_file(filename: str):
      bdp = _load_bdp()
      try:
        content = bdp.read_page(filename)
      except Exception as e:  # noqa: BLE001
        ui.notify(f"불러오기 실패: {e}", type="negative")
        return
      editor.value = content
      state["filename"] = filename
      file_select.value = filename
      status_label.text = f"편집 중: {filename}"

    def _do_load():
      filename = file_select.value
      if not filename:
        ui.notify("불러올 상세페이지를 선택하세요.", type="negative")
        return
      _load_file(filename)

    load_button.on_click(_do_load)

    def _do_save():
      if not state["filename"]:
        ui.notify("먼저 상세페이지를 불러오세요.", type="negative")
        return
      bdp = _load_bdp()
      try:
        bdp.write_page_content(state["filename"], editor.value)
      except Exception as e:  # noqa: BLE001
        ui.notify(f"저장 실패: {e}", type="negative")
        return
      ui.notify("저장 완료", type="positive")

    save_button.on_click(_do_save)

    def _do_preview():
      if not state["filename"]:
        ui.notify("먼저 상세페이지를 불러오세요.", type="negative")
        return
      url = f"{_PREVIEW_URL_PREFIX}/{urllib.parse.quote(state['filename'])}"
      ui.navigate.to(url, new_tab=True)

    preview_button.on_click(_do_preview)

    async def _do_export():
      if not state["filename"]:
        ui.notify("먼저 상세페이지를 불러오세요.", type="negative")
        return

      bdp = _load_bdp()
      filename = state["filename"]
      html_path = os.path.join(bdp.PAGES_ROOT, filename)
      identity = filename[:-len(".html")] if filename.endswith(".html") else filename
      slug = bdp.slugify(identity)

      export_button.props("loading")
      preview_gallery.clear()
      build_log.clear()
      build_log.push("PNG export 중...")
      loop = asyncio.get_event_loop()
      try:
        pngs = await loop.run_in_executor(None, bdp.export_pngs, html_path, slug)
      except Exception as e:  # noqa: BLE001
        build_log.push(f"실패: {e}")
        ui.notify(f"PNG export 실패: {e}", type="negative")
        return
      finally:
        export_button.props(remove="loading")

      build_log.push(f"완료: {len(pngs)}장")
      with preview_gallery:
        for p in pngs:
          ui.image(p).classes("w-40 rounded border")
      ui.notify(f"PNG {len(pngs)}장 export 완료", type="positive")

      # PNG export까지 끝나야 진짜 완성이라고 본다(사용자 확정, 2026-08-04) -
      # 실패해도 export 자체는 이미 끝난 상태라 best-effort로 처리하고
      # 로그로만 알린다.
      try:
        records = await loop.run_in_executor(None, safe_fetch_records)
        match = bdp.find_nocodb_record(records, identity)
        if match is None:
          build_log.push("⚠️ NocoDB에서 일치하는 상품을 못 찾아 Product_Page는 수동으로 반영해야 합니다.")
        elif match["fields"].get("Product_Page") != "Detail":
          await loop.run_in_executor(None, products_table.update, match["id"], {"Product_Page": "Detail"})
          build_log.push(f"NocoDB Product_Page → Detail 반영됨 ({match['fields'].get('SKU', '')})")
        else:
          build_log.push("NocoDB Product_Page 이미 Detail 상태.")
      except Exception as e:  # noqa: BLE001
        build_log.push(f"⚠️ NocoDB Product_Page 반영 실패: {e}")

    export_button.on_click(_do_export)

    if file:
      _load_file(file)
