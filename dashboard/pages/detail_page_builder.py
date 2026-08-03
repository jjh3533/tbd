"""상세페이지 제작 (/detail-page-builder) - "➕ 신규등록" 하위 메뉴.

product_pages/scripts/build_detail_page.py(브랜드 무관 상세페이지 생성 엔진)를
폼으로 감싼 페이지. 오퍼레이터가 카피(태그라인/Why 카드/스펙 등)를 직접 채워
넣으면 .dc.html 조립과 PNG export는 전부 코드가 처리한다 - 매 상품마다 AI
대화로 전체 파이프라인을 새로 훑지 않아도 되게 하는 게 목적.

로컬 전용 기능이다: Google Drive 동기화 폴더(Product Images/Product Pages_html)와
Playwright 헤드리스 Chromium(export_sections.py)이 필요해서 NAS 배포본에는 안
맞는다. 그래서 이 파일은 register.py의 image_uploader 지연 임포트와 동일한
이유로, build_detail_page 임포트를 전부 버튼 핸들러 안으로 미뤄둔다 - 그래야
NAS에서 이 페이지 라우트가 있어도 대시보드 전체 기동에는 영향이 없다."""
from __future__ import annotations

import asyncio
import os
import re
import sys
import urllib.parse

from nicegui import app, ui

import naver_config
from sync_engine import safe_fetch_records
from dashboard import components, layout

_N_WHY_CARDS = 3

_SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "product_pages", "scripts")

# 완성된 .dc.html이 있는 폴더 - PNG export(Playwright, 로컬 전용)와 달리 이
# 폴더 자체는 Synology Drive로 NAS에도 동기화되어 있어(TBD_SEOUL_ROOT 참고)
# my.tbd.kr에서도 미리보기가 그대로 동작한다.
_PAGES_ROOT = os.path.dirname(naver_config.PRODUCT_PAGES_DIR)
_PREVIEW_URL_PREFIX = "/detail-pages"

if os.path.isdir(_PAGES_ROOT):
  app.add_static_files(_PREVIEW_URL_PREFIX, _PAGES_ROOT)


def _load_bdp():
  """build_detail_page는 product_pages/scripts/에 있어서 기본 sys.path에 없다 -
  다른 임포트와 마찬가지로 버튼 핸들러 안에서만 지연 로드한다."""
  if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
  import build_detail_page as bdp
  return bdp


@ui.page("/detail-page-builder")
def detail_page_builder_page() -> None:
  with layout.frame(active_path="/detail-page-builder"):
    components.topbar("상세페이지 제작")

    state: dict = {
        "hero_source": None,
        "design_source": None,
        "html_path": None,
        "slug": None,
        "spec_rows": [],  # list[(label_input, value_input)]
    }

    # ------------------------------------------------------------------
    # 📂 저장된 브리프 불러오기 (선택) - 이전에 만들었던 상품을 다시 고칠 때
    # ------------------------------------------------------------------
    components.section_header("📂 저장된 브리프 불러오기 (선택)")
    with ui.row().classes("w-full gap-4 items-end mb-2"):
      brief_select = ui.select([], label="저장된 브리프").classes("flex-1")
      refresh_briefs_button = ui.button("목록 새로고침").props("outline")
      load_brief_button = ui.button("불러오기").props("outline")

    ui.separator().classes("my-4")

    # ------------------------------------------------------------------
    # 🔎 NocoDB에서 불러오기 (선택) - SKU로 검색해서 브랜드/상품명/이미지폴더 자동채움
    # ------------------------------------------------------------------
    components.section_header("🔎 NocoDB에서 불러오기 (선택)")
    with ui.row().classes("w-full gap-4 items-end mb-2"):
      nocodb_search_input = ui.input("SKU 검색", placeholder="e.g. Slate 7").classes("flex-1")
      nocodb_search_button = ui.button("검색").props("outline")
    nocodb_results = ui.column().classes("w-full gap-1 mb-2")

    ui.separator().classes("my-4")

    # ------------------------------------------------------------------
    # 1) 기본 정보
    # ------------------------------------------------------------------
    components.section_header("1) 기본 정보")
    with ui.row().classes("w-full gap-4"):
      brand_select = ui.select(["UniFi", "GL.inet"], value="UniFi", label="Brand").classes("w-40")
      title_input = ui.input("상품명 (Title)", placeholder="e.g. Slate 7").classes("flex-1")
    tagline_input = ui.textarea(
        "태그라인 (<br>로 줄바꿈)", placeholder="예: 터치스크린으로 제어하는 Wi-Fi 7 트래블 라우터."
    ).classes("w-full").props("rows=2")

    with ui.row().classes("w-full gap-4 items-end mt-2"):
      image_folder_input = ui.input(
          "제품이미지 폴더명", placeholder="e.g. GLiNET GL-BE3600"
      ).classes("flex-1")
      load_images_button = ui.button("이미지 불러오기").props("outline")
    ui.upload(
        label="직접 이미지 업로드 (공홈 크롤링/다운로드 대신 파일을 바로 추가)",
        multiple=True, auto_upload=True, on_multi_upload=lambda e: _do_upload_images(e),
    ).props('accept="image/*"').classes("w-full mb-2")
    image_gallery = ui.column().classes("w-full gap-2 mb-2")
    selection_status = ui.label("히어로/디자인 이미지를 아직 선택하지 않았습니다.").classes(
        "text-sm text-tbd-text-secondary"
    )

    def _refresh_status():
      hero_name = state["hero_source"].split("/")[-1] if state["hero_source"] else "미선택"
      design_name = state["design_source"].split("/")[-1] if state["design_source"] else "미선택"
      selection_status.text = f"히어로: {hero_name} · 디자인: {design_name}"

    ui.separator().classes("my-4")

    # ------------------------------------------------------------------
    # 🤖 Claude로 브리프 초안 생성 (선택)
    # ------------------------------------------------------------------
    components.section_header("🤖 Claude로 브리프 초안 생성 (선택)")
    ui.label(
        "공홈 설명/스펙을 참고 자료 칸에 붙여넣거나 URL로 가져온 뒤 생성하면 "
        "태그라인/Why 3카드/Design/Tech Specs를 Claude가 초안으로 채워줍니다. "
        "생성 후에도 전부 수정 가능하니 저장·업로드 전에 꼭 검토하세요."
    ).classes("text-sm text-tbd-text-secondary mb-2")

    with ui.row().classes("w-full gap-4 items-end mb-2"):
      reference_url_input = ui.input(
          "공홈 URL (선택 - 자동으로 참고자료 채우기)",
          placeholder="e.g. https://store.ui.com/us/en/products/u6-pro",
      ).classes("flex-1")
      fetch_reference_button = ui.button("가져오기").props("outline")

    reference_text_area = ui.textarea(
        "참고 자료 (공홈 설명/스펙 - 직접 붙여넣기도 가능)"
    ).classes("w-full").props("rows=6")

    with ui.row().classes("w-full gap-3 mb-2"):
      generate_brief_button = components.primary_button("🤖 브리프 초안 생성")

    ui.separator().classes("my-4")

    # ------------------------------------------------------------------
    # 2) Why 섹션 (3카드)
    # ------------------------------------------------------------------
    components.section_header("2) Why 섹션")
    with ui.row().classes("w-full gap-4"):
      why_headline_input = ui.input("헤드라인 (<br> 가능)").classes("flex-1")
      why_bg_checkbox = ui.checkbox("회색 배경", value=True)
    why_sub_input = ui.input("서브텍스트").classes("w-full")

    why_card_inputs: list[tuple[ui.input, ui.textarea]] = []
    with ui.row().classes("w-full gap-4 mt-2"):
      for i in range(_N_WHY_CARDS):
        with ui.column().classes("flex-1 gap-1"):
          ui.label(f"카드 {i + 1}").classes("text-sm font-medium text-tbd-text-secondary")
          heading_input = ui.input("제목 (<br> 가능)").classes("w-full")
          body_input = ui.textarea("본문").classes("w-full").props("rows=4")
          why_card_inputs.append((heading_input, body_input))

    ui.separator().classes("my-4")

    # ------------------------------------------------------------------
    # 3) Design 섹션
    # ------------------------------------------------------------------
    components.section_header("3) Design 섹션")
    ui.label("이미지는 위 갤러리에서 \"디자인 섹션 이미지로 사용\"으로 고른 걸 그대로 씁니다.").classes(
        "text-sm text-tbd-text-secondary mb-2"
    )
    design_headline_input = ui.input("헤드라인 (<br> 가능)").classes("w-full")
    design_body_input = ui.textarea("본문").classes("w-full").props("rows=3")

    ui.separator().classes("my-4")

    # ------------------------------------------------------------------
    # 4) Tech Specs
    # ------------------------------------------------------------------
    components.section_header("4) Tech Specs")
    specs_column = ui.column().classes("w-full gap-2 mb-2")

    def _add_spec_row(label: str = "", value: str = ""):
      with specs_column:
        with ui.row().classes("w-full gap-2 items-center") as row:
          label_input = ui.input("항목", value=label).classes("w-56")
          value_input = ui.input("값", value=value).classes("flex-1")
          entry = (label_input, value_input)

          def _remove(r=row, e=entry):
            state["spec_rows"].remove(e)
            r.delete()

          ui.button(icon="close", on_click=_remove).props("flat dense round size=sm")
      state["spec_rows"].append(entry)

    with ui.row().classes("mb-2"):
      ui.button("+ 행 추가", on_click=lambda: _add_spec_row()).props("outline dense")

    for _ in range(6):
      _add_spec_row()

    ui.separator().classes("my-4")

    # ------------------------------------------------------------------
    # 5) 실행
    # ------------------------------------------------------------------
    components.section_header("5) 생성")
    with ui.row().classes("w-full gap-3 mb-2"):
      save_brief_button = ui.button("💾 브리프 저장").props("outline")
      generate_button = components.primary_button("1) .dc.html 생성")
      export_button = components.primary_button("2) PNG로 Export")
      export_button.disable()

    build_log = ui.log(max_lines=100).classes("tbd-log tbd-log--sm w-full")
    preview_gallery = ui.row().classes("w-full gap-3 flex-wrap")

    ui.separator().classes("my-4")

    # ------------------------------------------------------------------
    # 6) 완성된 상세페이지 보기
    # ------------------------------------------------------------------
    components.section_header("6) 완성된 상세페이지 보기")
    ui.label(
        "지금까지 만든 .dc.html을 브라우저 새 탭에서 그대로 열어봅니다 - "
        "PNG export 없이도(로컬 전용 기능이라 my.tbd.kr에선 안 됨) 실제 레이아웃을 바로 확인할 수 있어요."
    ).classes("text-sm text-tbd-text-secondary mb-2")

    with ui.row().classes("w-full gap-4 items-end mb-2"):
      completed_pages_select = ui.select(
          _load_bdp().list_completed_pages(), label="완성된 상세페이지"
      ).classes("flex-1")
      refresh_completed_button = ui.button("목록 새로고침").props("outline")

    def _do_refresh_completed():
      completed_pages_select.options = _load_bdp().list_completed_pages()
      completed_pages_select.update()
      ui.notify(f"{len(completed_pages_select.options)}개 발견", type="positive")

    refresh_completed_button.on_click(_do_refresh_completed)

    def _do_preview_completed():
      filename = completed_pages_select.value
      if not filename:
        ui.notify("미리볼 상세페이지를 선택하세요.", type="negative")
        return
      url = f"{_PREVIEW_URL_PREFIX}/{urllib.parse.quote(filename)}"
      ui.navigate.to(url, new_tab=True)

    components.primary_button("🔍 미리보기", on_click=_do_preview_completed)

    # -- NocoDB 검색 -----------------------------------------------------
    async def _do_nocodb_search():
      query = (nocodb_search_input.value or "").strip().lower()
      if not query:
        ui.notify("검색어를 입력하세요.", type="negative")
        return
      nocodb_search_button.props("loading")
      nocodb_results.clear()
      try:
        loop = asyncio.get_event_loop()
        records = await loop.run_in_executor(None, safe_fetch_records)
      finally:
        nocodb_search_button.props(remove="loading")

      matches = [r for r in records if query in str(r.get("fields", {}).get("SKU", "")).lower()][:10]
      with nocodb_results:
        if not matches:
          ui.label("일치하는 상품이 없습니다.").classes("text-sm text-tbd-text-secondary")
        for rec in matches:
          fields = rec.get("fields", {})

          async def _apply(fields=fields):
            brand = fields.get("Brand") or "UniFi"
            brand_select.value = brand if brand in ("UniFi", "GL.inet") else "UniFi"
            model_number = (fields.get("Model Number") or "").strip()
            title_input.value = model_number or fields.get("SKU", "")
            folder_brand = {"UniFi": "UniFi", "GL.inet": "GLiNET"}.get(brand_select.value, brand_select.value)
            if model_number:
              image_folder_input.value = f"{folder_brand} {model_number}"
              # 폴더명이 정해지자마자 기본 이미지 위치(제품이미지 루트/이 폴더)를
              # 자동으로 불러온다 - 예전엔 "이미지 불러오기" 버튼을 한 번 더
              # 눌러야만 갤러리가 떴음(사용자 요청 2026-08-03).
              await _do_load_images()
            ui.notify(f"[{fields.get('SKU')}] 적용됨", type="positive")

          ui.button(f"{fields.get('SKU', '')[:60]}", on_click=_apply).props("outline dense align=left").classes("w-full justify-start")

    nocodb_search_button.on_click(_do_nocodb_search)

    # -- 저장된 브리프 목록/불러오기 ------------------------------------------
    async def _do_refresh_briefs():
      refresh_briefs_button.props("loading")
      try:
        bdp = _load_bdp()
        loop = asyncio.get_event_loop()
        slugs = await loop.run_in_executor(None, bdp.list_briefs)
      except Exception as e:  # noqa: BLE001
        ui.notify(f"브리프 목록 불러오기 실패: {e}", type="negative")
        return
      finally:
        refresh_briefs_button.props(remove="loading")

      brief_select.options = slugs
      brief_select.update()
      ui.notify(f"브리프 {len(slugs)}개 발견", type="positive")

    refresh_briefs_button.on_click(_do_refresh_briefs)

    async def _do_load_brief():
      slug = brief_select.value
      if not slug:
        ui.notify("불러올 브리프를 선택하세요.", type="negative")
        return

      load_brief_button.props("loading")
      try:
        bdp = _load_bdp()
        loop = asyncio.get_event_loop()
        brief = await loop.run_in_executor(None, bdp.load_brief, slug)
      except Exception as e:  # noqa: BLE001
        ui.notify(f"브리프 불러오기 실패: {e}", type="negative")
        return
      finally:
        load_brief_button.props(remove="loading")

      brand_select.value = brief.get("brand", "UniFi")
      title_input.value = brief.get("title", "")
      tagline_input.value = brief.get("tagline", "")
      state["hero_source"] = brief.get("hero_source")
      state["design_source"] = brief.get("design_source")
      _refresh_status()

      # 브리프에 저장된 히어로/디자인 이미지 경로에서 제품이미지 폴더명을
      # 역산해 기본 위치를 자동으로 채우고 갤러리도 바로 불러온다(사용자
      # 요청 2026-08-03) - 예전엔 이 필드가 비어있어 "이미지 불러오기"를
      # 다시 누르기 전엔 폴더명조차 안 보였음.
      source_path = state["hero_source"] or state["design_source"]
      if source_path:
        image_folder_input.value = os.path.basename(os.path.dirname(source_path))
        await _do_load_images()

      why_headline_input.value = brief.get("why_headline", "")
      why_sub_input.value = brief.get("why_sub", "")
      why_bg_checkbox.value = bool(brief.get("why_bg_gray", True))
      for i, (heading_input, body_input) in enumerate(why_card_inputs):
        card = brief.get("why_cards", [])
        heading_input.value = card[i][0] if i < len(card) else ""
        body_input.value = card[i][1] if i < len(card) else ""

      design_headline_input.value = brief.get("design_headline", "")
      design_body_input.value = brief.get("design_body", "")

      specs_column.clear()
      state["spec_rows"].clear()
      specs = brief.get("specs") or [["", ""]]
      for label, value in specs:
        _add_spec_row(label, value)

      ui.notify(f"브리프 불러옴: {slug}", type="positive")

    load_brief_button.on_click(_do_load_brief)

    # -- 직접 이미지 업로드 (공홈 크롤링/다운로드 대신 파일을 바로 폴더에 추가) ------
    _UPLOAD_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")

    async def _do_upload_images(e):
      folder_name = (image_folder_input.value or "").strip()
      if not folder_name:
        ui.notify("업로드 전에 제품이미지 폴더명을 먼저 입력하세요.", type="negative")
        return

      folder = os.path.join(naver_config.PRODUCT_IMAGES_DIR, folder_name)
      os.makedirs(folder, exist_ok=True)

      existing = [f for f in os.listdir(folder) if f.lower().endswith(_UPLOAD_IMAGE_EXTENSIONS)]
      next_num = 1
      for f in existing:
        m = re.match(r"^(\d+)", f)
        if m:
          next_num = max(next_num, int(m.group(1)) + 1)

      saved = 0
      for i, file in enumerate(e.files):
        ext = os.path.splitext(file.name)[1].lower() or ".jpg"
        if ext not in _UPLOAD_IMAGE_EXTENSIONS:
          continue
        dest_name = f"{next_num + i:02d}{ext}"
        await file.save(os.path.join(folder, dest_name))
        saved += 1

      ui.notify(f"이미지 {saved}장 업로드 완료", type="positive")
      await _do_load_images()

    # -- 이미지 불러오기 ---------------------------------------------------
    async def _do_load_images():
      folder_name = (image_folder_input.value or "").strip()
      if not folder_name:
        ui.notify("제품이미지 폴더명을 입력하세요.", type="negative")
        return

      load_images_button.props("loading")
      image_gallery.clear()
      try:
        bdp = _load_bdp()

        loop = asyncio.get_event_loop()
        images = await loop.run_in_executor(None, bdp.list_source_images, folder_name)
      except Exception as e:  # noqa: BLE001
        ui.notify(f"이미지 불러오기 실패: {e}", type="negative")
        return
      finally:
        load_images_button.props(remove="loading")

      if not images:
        with image_gallery:
          ui.label("이미지를 찾을 수 없습니다. 폴더명을 확인하세요.").classes("text-sm text-tbd-text-secondary")
        return

      with image_gallery:
        with ui.row().classes("w-full gap-3 flex-wrap"):
          for path in images:
            with ui.column().classes("gap-1 items-center"):
              ui.image(path).classes("w-28 h-28 object-cover rounded border")

              def _use_hero(p=path):
                state["hero_source"] = p
                _refresh_status()
                ui.notify("히어로 이미지로 선택됨", type="positive")

              def _use_design(p=path):
                state["design_source"] = p
                _refresh_status()
                ui.notify("디자인 섹션 이미지로 선택됨", type="positive")

              with ui.row().classes("gap-1"):
                ui.button("히어로", on_click=_use_hero).props("dense outline size=sm")
                ui.button("디자인", on_click=_use_design).props("dense outline size=sm")

      ui.notify(f"이미지 {len(images)}장 불러옴", type="positive")

    load_images_button.on_click(_do_load_images)

    # -- 공홈 URL로 참고자료 자동 채우기 ---------------------------------------
    async def _do_fetch_reference():
      url = (reference_url_input.value or "").strip()
      if not url:
        ui.notify("공홈 URL을 입력하세요.", type="negative")
        return

      fetch_reference_button.props("loading")
      try:
        import official_scrapers  # 지연 import - NAS에도 있지만 이 페이지 자체가 로컬 전용이라 통일

        loop = asyncio.get_event_loop()
        product = await loop.run_in_executor(
            None, official_scrapers.fetch_product, brand_select.value, url
        )
      except Exception as e:  # noqa: BLE001
        ui.notify(f"크롤링 실패: {e}", type="negative")
        return
      finally:
        fetch_reference_button.props(remove="loading")

      reference_text_area.value = product.description
      if not title_input.value:
        title_input.value = product.title
      ui.notify("참고 자료를 불러왔습니다.", type="positive")

    fetch_reference_button.on_click(_do_fetch_reference)

    # -- Claude로 브리프 초안 생성 --------------------------------------------
    async def _do_generate_brief():
      reference_text = (reference_text_area.value or "").strip()
      if not reference_text:
        ui.notify("참고 자료를 입력하거나 공홈 URL로 가져오세요.", type="negative")
        return
      title = (title_input.value or "").strip()
      if not title:
        ui.notify("상품명을 입력하세요.", type="negative")
        return

      generate_brief_button.props("loading")
      try:
        import brief_generator  # 지연 import - anthropic 패키지는 NAS Dockerfile에 없음(로컬 전용 기능)

        folder_brand = {"UniFi": "UniFi", "GL.inet": "GLiNET"}.get(brand_select.value, brand_select.value)
        folder_name = (image_folder_input.value or "").strip()
        prefix = f"{folder_brand} "
        model_number = folder_name[len(prefix):] if folder_name.startswith(prefix) else ""

        loop = asyncio.get_event_loop()
        draft = await loop.run_in_executor(
            None, brief_generator.generate_brief_draft,
            brand_select.value, title, model_number, reference_text, "",
        )
      except Exception as e:  # noqa: BLE001
        ui.notify(f"브리프 생성 실패: {e}", type="negative")
        return
      finally:
        generate_brief_button.props(remove="loading")

      tagline_input.value = draft["tagline"]
      why_headline_input.value = draft["why_headline"]
      why_sub_input.value = draft["why_sub"]
      for i, (heading_input, body_input) in enumerate(why_card_inputs):
        card = draft["why_cards"]
        heading_input.value = card[i][0] if i < len(card) else ""
        body_input.value = card[i][1] if i < len(card) else ""
      design_headline_input.value = draft["design_headline"]
      design_body_input.value = draft["design_body"]

      specs_column.clear()
      state["spec_rows"].clear()
      for label, value in (draft["specs"] or [["", ""]]):
        _add_spec_row(label, value)

      ui.notify("Claude 초안 생성 완료 - 검토한 뒤 저장하세요.", type="positive")

    generate_brief_button.on_click(_do_generate_brief)

    # -- 브리프 조립 -------------------------------------------------------
    def _collect_brief() -> dict | None:
      title = (title_input.value or "").strip()
      if not title:
        ui.notify("상품명을 입력하세요.", type="negative")
        return None
      if not state["hero_source"]:
        ui.notify("히어로 이미지를 선택하세요.", type="negative")
        return None
      if not state["design_source"]:
        ui.notify("디자인 섹션 이미지를 선택하세요.", type="negative")
        return None

      why_cards = []
      for heading_input, body_input in why_card_inputs:
        h = (heading_input.value or "").strip()
        b = (body_input.value or "").strip()
        if h or b:
          why_cards.append([h, b])
      if len(why_cards) != _N_WHY_CARDS:
        ui.notify(f"Why 카드 {_N_WHY_CARDS}개를 모두 채우세요.", type="negative")
        return None

      specs = []
      for label_input, value_input in state["spec_rows"]:
        label = (label_input.value or "").strip()
        value = (value_input.value or "").strip()
        if label and value:
          specs.append([label, value])
      if not specs:
        ui.notify("Tech Specs를 최소 1개 입력하세요.", type="negative")
        return None

      return {
          "brand": brand_select.value,
          "title": title,
          "tagline": tagline_input.value or "",
          "hero_source": state["hero_source"],
          "why_headline": why_headline_input.value or "",
          "why_sub": why_sub_input.value or "",
          "why_cards": why_cards,
          "why_bg_gray": bool(why_bg_checkbox.value),
          "design_source": state["design_source"],
          "design_headline": design_headline_input.value or "",
          "design_body": design_body_input.value or "",
          "specs": specs,
      }

    # -- 브리프 저장 -------------------------------------------------------
    async def _do_save_brief():
      brief = _collect_brief()
      if not brief:
        return
      try:
        bdp = _load_bdp()

        loop = asyncio.get_event_loop()
        path = await loop.run_in_executor(None, bdp.save_brief, brief)
        ui.notify(f"브리프 저장됨: {path}", type="positive")
      except Exception as e:  # noqa: BLE001
        ui.notify(f"브리프 저장 실패: {e}", type="negative")

    save_brief_button.on_click(_do_save_brief)

    # -- .dc.html 생성 -----------------------------------------------------
    async def _do_generate():
      brief = _collect_brief()
      if not brief:
        return

      generate_button.props("loading")
      build_log.clear()
      build_log.push("생성 중...")
      try:
        bdp = _load_bdp()

        loop = asyncio.get_event_loop()
        html_path, slug = await loop.run_in_executor(None, bdp.write_page, brief)
      except Exception as e:  # noqa: BLE001
        build_log.push(f"실패: {e}")
        ui.notify(f".dc.html 생성 실패: {e}", type="negative")
        return
      finally:
        generate_button.props(remove="loading")

      state["html_path"] = html_path
      state["slug"] = slug
      build_log.push(f"완료: {html_path}")
      export_button.enable()
      ui.notify(".dc.html 생성 완료 - PNG Export를 진행하세요.", type="positive")

    generate_button.on_click(_do_generate)

    # -- PNG Export --------------------------------------------------------
    async def _do_export():
      if not state["html_path"]:
        ui.notify("먼저 .dc.html을 생성하세요.", type="negative")
        return

      export_button.props("loading")
      preview_gallery.clear()
      build_log.push("PNG export 중...")
      try:
        bdp = _load_bdp()

        loop = asyncio.get_event_loop()
        pngs = await loop.run_in_executor(None, bdp.export_pngs, state["html_path"], state["slug"])
      except Exception as e:  # noqa: BLE001
        build_log.push(f"export 실패: {e}")
        ui.notify(f"PNG export 실패: {e}", type="negative")
        return
      finally:
        export_button.props(remove="loading")

      build_log.push(f"완료: {len(pngs)}장")
      with preview_gallery:
        for p in pngs:
          ui.image(p).classes("w-40 rounded border")
      ui.notify(f"PNG {len(pngs)}장 export 완료", type="positive")

    export_button.on_click(_do_export)
