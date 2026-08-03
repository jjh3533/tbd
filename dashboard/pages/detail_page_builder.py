"""상세페이지 제작 (/detail-page-builder) - "➕ 신규등록" 하위메뉴 1.

product_pages/scripts/build_detail_page.py(브랜드 무관 상세페이지 생성 엔진)를
폼으로 감싼 페이지. 오퍼레이터가 카피(태그라인/Why 카드/스펙 등)를 직접 채워
넣으면 HTML 조립은 코드가 처리한다.

**2026-08-04 대개편**: 브리프를 파일로 저장/불러오지 않는다(이 페이지의
`state` dict 안에서만 조립했다가 버림) - 상세페이지를 마지막으로 다듬는 건
이 폼을 다시 채워서가 아니라 "HTML 편집"(하위메뉴 2, `/detail-page-editor`)의
코드 에디터로 직접 하는 흐름으로 바뀌었기 때문. 이미지 업로드 기능도 뺐다 -
이미지는 이제 "➕ 신규등록"(`/register`) 단계에서 히어로/디자인/스토어1~4
역할로 미리 골라서 저장해두고, 여기서는 그 결과를 읽기만 한다. PNG export와
NocoDB `Product_Page` 반영도 "HTML 편집" 페이지로 옮겨갔다 - "HTML 생성"은
초안을 만드는 단계일 뿐, 실제로 완성됐다고 볼 수 있는 시점은 편집을 마치고
PNG export까지 끝난 뒤이기 때문(사용자 확정).

my.tbd.kr(NAS)에서도 전체 기능이 동작한다(2026-08-03, NAS Dockerfile에
Playwright + 헤드리스 Chromium 추가 후 확인) - `naver_config`의
`TBD_SEOUL_ROOT` 오버라이드로 Product Images/Product Pages_html 경로가 이미
NAS에도 매핑돼 있었다. build_detail_page 임포트를 버튼 핸들러 안으로 미뤄두는
건 여전한데(register.py의 image_uploader 지연 임포트와 동일 패턴), NAS 회피
목적이 아니라 build_detail_page가 product_pages/scripts/에 있어 기본
sys.path에 없기 때문(`_load_bdp()` 참고)."""
from __future__ import annotations

import asyncio
import os
import re
import sys
import urllib.parse

from nicegui import ui

from sync_engine import safe_fetch_records
from dashboard import components, layout

_N_WHY_CARDS = 3

_SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "product_pages", "scripts")

# 이미지 파일명 역할 접미사 - register.py가 다운로드할 때 붙이는 규칙과 동일
# ("01-hero.ext", "02-design.ext", "03-store-1.ext" ...). 이 접미사가 있으면
# 자동으로 히어로/디자인을 프리셋하고, 없는(레거시) 이미지는 예전처럼 사람이
# 직접 버튼으로 골라야 한다.
_STORE_SUFFIX_RE = re.compile(r"-store-\d\.", re.IGNORECASE)


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
        "spec_rows": [],  # list[(label_input, value_input)]
        "last_filename": None,
        # NocoDB 검색으로 상품을 골랐을 때의 SKU - title_input.value는 사람이
        # 마케팅 문구로 자유롭게 다듬는 게 정상 워크플로우라, 파일명("{SKU}.html")
        # 기준은 title이 아니라 이 안정적인 식별자를 쓴다(title만 쓰면 다듬을
        # 때마다 파일명이 바뀜 - 사용자가 실사용 중 발견, 2026-08-04).
        "sku": "",
    }

    # ------------------------------------------------------------------
    # 🔎 NocoDB에서 불러오기 (선택) - SKU로 검색해서 브랜드/상품명/이미지폴더/
    # 공홈 URL까지 자동채움
    # ------------------------------------------------------------------
    components.section_header("🔎 NocoDB에서 불러오기 (선택)")
    with ui.row().classes("w-full gap-4 items-end mb-2"):
      nocodb_search_input = ui.input("SKU 검색", placeholder="e.g. Slate 7").classes("flex-1")
      nocodb_search_button = ui.button("검색").props("outline")
    nocodb_results = ui.column().classes("w-full gap-1 mb-2")

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
    # 5) 생성
    # ------------------------------------------------------------------
    components.section_header("5) 생성")
    with ui.row().classes("w-full gap-3 mb-2"):
      generate_button = components.primary_button("HTML 생성")
      edit_button = components.primary_button("✏️ HTML 편집")
      edit_button.disable()

    build_log = ui.log(max_lines=100).classes("tbd-log tbd-log--sm w-full")

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
            # title_input은 이후 사람이 마케팅 문구로 다듬을 수 있지만, SKU는
            # 그대로 고정해서 파일명("{SKU}.html")에 쓴다.
            state["sku"] = fields.get("SKU", "")
            folder_brand = {"UniFi": "UniFi", "GL.inet": "GLiNET"}.get(brand_select.value, brand_select.value)
            if model_number:
              image_folder_input.value = f"{folder_brand} {model_number}"
              # 폴더명이 정해지자마자 이미지를 자동으로 불러온다 - 예전엔
              # "이미지 불러오기" 버튼을 한 번 더 눌러야만 갤러리가 떴음
              # (사용자 요청 2026-08-03).
              await _do_load_images()
            official_url = (fields.get("Official_URL") or "").strip()
            if official_url:
              # 공홈 URL도 알고 있으면 참고자료까지 자동으로 크롤링해온다
              # (사용자 요청 2026-08-04) - 예전엔 이것도 사람이 URL을 다시
              # 붙여넣고 "가져오기"를 눌러야 했음.
              reference_url_input.value = official_url
              await _do_fetch_reference()
            ui.notify(f"[{fields.get('SKU')}] 적용됨", type="positive")

          ui.button(f"{fields.get('SKU', '')[:60]}", on_click=_apply).props("outline dense align=left").classes("w-full justify-start")

    nocodb_search_button.on_click(_do_nocodb_search)

    # -- 이미지 불러오기 ---------------------------------------------------
    # 파일명이 "-hero."/"-design."로 끝나면(register.py의 신규 다운로드 규칙)
    # 자동으로 히어로/디자인을 프리셋한다. "-store-N."인 4장은 참고용
    # 썸네일로만 보여준다(상세페이지 생성에는 안 씀 - 네이버 등록용). 역할
    # 접미사가 없는 레거시 폴더는 예전처럼 사람이 버튼으로 직접 고른다.
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

      store_images = []
      manual_images = []
      for path in images:
        fname = os.path.basename(path).lower()
        if "-hero." in fname:
          state["hero_source"] = path
        elif "-design." in fname:
          state["design_source"] = path
        elif _STORE_SUFFIX_RE.search(fname):
          store_images.append(path)
        else:
          manual_images.append(path)
      _refresh_status()

      with image_gallery:
        if state["hero_source"] or state["design_source"]:
          ui.label("자동 프리셋됨").classes("text-xs text-tbd-text-secondary")
          with ui.row().classes("w-full gap-3 flex-wrap mb-2"):
            for role_label, source_key in (("히어로", "hero_source"), ("디자인", "design_source")):
              if state[source_key]:
                with ui.column().classes("gap-1 items-center"):
                  ui.image(state[source_key]).classes("w-28 h-28 object-cover rounded border-2 border-primary")
                  ui.label(role_label).classes("text-xs text-primary font-medium")

        if manual_images:
          ui.label("이미지 선택 (파일명에 역할이 없어 직접 골라주세요)").classes(
              "text-xs text-tbd-text-secondary"
          )
          with ui.row().classes("w-full gap-3 flex-wrap mb-2"):
            for path in manual_images:
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

        if store_images:
          ui.label("스토어 이미지 (참고용 - 네이버 등록에 쓰임, 상세페이지엔 안 들어감)").classes(
              "text-xs text-tbd-text-secondary"
          )
          with ui.row().classes("w-full gap-2 flex-wrap"):
            for path in store_images:
              ui.image(path).classes("w-20 h-20 object-cover rounded border")

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
        import official_scrapers  # 지연 import - 다른 버튼 핸들러들과 패턴 통일(NAS에도 정상 배포되어 있음)

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
        import brief_generator  # 지연 import - anthropic 패키지는 NAS Dockerfile에도 있음(정상 배포됨), 다른 핸들러들과 패턴만 통일

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

    # -- 브리프 조립(파일로 저장하지 않고 write_page()에 바로 넘길 dict만 조립) --
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
          "sku": state["sku"],
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

    # -- HTML 생성 -----------------------------------------------------
    def _go_to_editor():
      if not state["last_filename"]:
        return
      ui.navigate.to(f"/detail-page-editor?file={urllib.parse.quote(state['last_filename'])}")

    edit_button.on_click(_go_to_editor)

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
        html_path, _slug = await loop.run_in_executor(None, bdp.write_page, brief)
      except Exception as e:  # noqa: BLE001
        build_log.push(f"실패: {e}")
        ui.notify(f"HTML 생성 실패: {e}", type="negative")
        return
      finally:
        generate_button.props(remove="loading")

      filename = os.path.basename(html_path)
      state["last_filename"] = filename
      build_log.push(f"완료: {filename}")
      edit_button.enable()
      ui.notify("HTML 생성 완료 - 'HTML 편집'을 눌러 마무리하세요.", type="positive")

    generate_button.on_click(_do_generate)
