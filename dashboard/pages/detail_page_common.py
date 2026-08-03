"""상세페이지 공통영역 편집 (/detail-page-common) - "➕ 신규등록" 하위메뉴 3.

상세페이지 하단의 공통 섹션(TBD Seoul 신뢰뱃지 ~ 통관안내 ~ 배송/반품 안내 ~
FAQ ~ Footer)을 브랜드별로 직접 HTML로 편집한다(2026-08-04 신설). 저장하면
`Product Pages_html/common/{brand}-footer.html`에 완성된 텍스트 그대로
저장되고, 다음에 생성하는 상세페이지부터 그 내용을 그대로 이어붙인다
(`build_detail_page.build_html()` 참고) - 예전처럼 `__EYEBROW__`/`__STORE__`
같은 플레이스홀더를 치환하는 방식이 아니라 완성된 HTML을 그대로 쓰기
때문에, 문구뿐 아니라 마크업 구조 자체도 브랜드마다 자유롭게 바꿀 수 있다.
이 전환으로 `common_settings.py`의 `common_copy`(초기불량 보장 기간/배송
소요일) 필드는 더 이상 안 쓴다 - 이제 이 HTML 안에 직접 텍스트로 들어있다.

이미 생성된 상세페이지엔 소급 적용되지 않는다(다른 공통 텍스트 변경과
동일한 관행) - 편집기로 직접 열어 고치거나 재생성해야 반영된다.

에디터는 detail_page_editor.py와 동일하게 `ui.codemirror`(HTML)를 쓴다 -
이유도 동일(WYSIWYG 리치텍스트 에디터는 인라인 스타일 구조를 깨뜨릴
위험이 있음)."""
from __future__ import annotations

import os
import sys

from nicegui import ui

from dashboard import components, layout

_SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "product_pages", "scripts")

_BRANDS = ["UniFi", "GL.inet"]


def _load_bdp():
  """build_detail_page는 product_pages/scripts/에 있어서 기본 sys.path에 없다."""
  if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
  import build_detail_page as bdp
  return bdp


@ui.page("/detail-page-common")
def detail_page_common_page() -> None:
  with layout.frame(active_path="/detail-page-common"):
    components.topbar("공통영역 편집")

    ui.label(
        "상세페이지 하단 공통 섹션(TBD Seoul 신뢰뱃지~통관안내~배송/반품 안내~FAQ~Footer)을 "
        "브랜드별로 직접 편집합니다. 저장하면 다음에 생성하는 상세페이지부터 반영되고, "
        "이미 만든 상세페이지엔 소급 적용되지 않습니다(편집기로 직접 열어 고치거나 재생성하세요)."
    ).classes("text-sm text-tbd-text-secondary mb-4")

    with ui.row().classes("w-full gap-4 items-end mb-2"):
      brand_select = ui.select(_BRANDS, value=_BRANDS[0], label="Brand").classes("w-40")
      load_button = ui.button("불러오기").props("outline")

    editor = ui.codemirror(language="HTML", theme="vscodeLight").classes("w-full").style("height: 600px;")

    save_button = components.primary_button("💾 저장하기").classes("mt-4")

    def _do_load():
      bdp = _load_bdp()
      try:
        content = bdp.read_common_footer(brand_select.value)
      except Exception as e:  # noqa: BLE001
        ui.notify(f"불러오기 실패: {e}", type="negative")
        return
      editor.value = content
      ui.notify(f"{brand_select.value} 공통영역을 불러왔습니다.", type="positive")

    load_button.on_click(_do_load)

    def _do_save():
      bdp = _load_bdp()
      try:
        path = bdp.write_common_footer(brand_select.value, editor.value)
      except Exception as e:  # noqa: BLE001
        ui.notify(f"저장 실패: {e}", type="negative")
        return
      ui.notify(f"저장 완료: {path}", type="positive")

    save_button.on_click(_do_save)

    # 처음 진입 시 기본 브랜드(UniFi)로 자동 시드.
    _do_load()
