"""공통 설정 (/settings) - 브랜드 로고/문구, 구매·배송 안내 문구를 코드 수정
없이 바꾸는 페이지. 실제 값은 common_settings.json에 저장되고,
product_pages/scripts/build_pages.py가 상세페이지 생성 시 이 값을 읽어
UNIFI_BRAND/GLINET_BRAND/트러스트 템플릿 기본값 위에 덮어씌운다.

주의: 이미 생성된 .dc.html에는 소급 적용되지 않는다 - 값을 바꾼 뒤 해당
상품의 상세페이지를 다시 생성해야 반영된다."""
from __future__ import annotations

from nicegui import ui

import common_settings
from dashboard import components, layout

_BRAND_FIELDS = [
    ("header_logo_src", "헤더 로고 경로"),
    ("header_logo_alt", "헤더 로고 alt"),
    ("hero_logo_src", "히어로 로고 경로"),
    ("hero_logo_alt", "히어로 로고 alt"),
    ("hero_logo_height", "히어로 로고 높이 (예: 60px)"),
    ("eyebrow_label", "eyebrow 라벨"),
    ("supply_label", "supply 라벨 (파일명에도 쓰임)"),
    ("product_name", "제품 라인명 (트러스트 문구용)"),
    ("official_name", "제조사명 (공식채널/AS 문구용)"),
    ("store_line", "스토어 표기"),
]


@ui.page("/settings")
def settings_page() -> None:
  with layout.frame(active_path="/settings"):
    components.topbar("공통 설정")

    ui.label(
        "브랜드 로고/문구와 구매·배송 안내 문구를 여기서 바꾸면 다음에 생성하는 "
        "상세페이지부터 반영됩니다. 이미 만든 .dc.html은 소급 적용되지 않으니 "
        "값을 바꾼 뒤 해당 상품 상세페이지를 다시 생성해주세요."
    ).classes("text-sm text-tbd-text-secondary mb-6")

    settings = common_settings.load()
    brand_inputs: dict[str, dict[str, ui.input]] = {}

    with ui.row().classes("w-full gap-6 items-start"):
      for brand_key in ("UniFi", "GL.inet"):
        with ui.column().classes("flex-1 gap-2"):
          components.section_header(f"{brand_key} 브랜드")
          brand_inputs[brand_key] = {}
          for field_key, field_label in _BRAND_FIELDS:
            value = settings["brands"].get(brand_key, {}).get(field_key, "")
            brand_inputs[brand_key][field_key] = ui.input(field_label, value=value).classes("w-full")

    ui.separator().classes("my-6")

    components.section_header("공통 구매·배송 안내 문구", "상세페이지 트러스트 섹션에 쓰이는 숫자 값들입니다.")
    with ui.row().classes("w-full gap-4"):
      return_weeks_input = ui.number(
          "초기불량 보장 기간 (주)", value=settings["common_copy"].get("return_window_weeks", 2), min=1, step=1, precision=0
      ).classes("w-56")
      delivery_min_input = ui.number(
          "배송 소요 최소 (일)", value=settings["common_copy"].get("delivery_min_days", 7), min=1, step=1, precision=0
      ).classes("w-56")
      delivery_max_input = ui.number(
          "배송 소요 최대 (일)", value=settings["common_copy"].get("delivery_max_days", 14), min=1, step=1, precision=0
      ).classes("w-56")

    ui.separator().classes("my-6")

    def _do_save():
      new_settings = {
          "brands": {
              brand_key: {field_key: inp.value for field_key, inp in fields.items()}
              for brand_key, fields in brand_inputs.items()
          },
          "common_copy": {
              "return_window_weeks": int(return_weeks_input.value or 2),
              "delivery_min_days": int(delivery_min_input.value or 7),
              "delivery_max_days": int(delivery_max_input.value or 14),
          },
      }
      common_settings.save(new_settings)
      ui.notify("저장 완료 - 다음 상세페이지 생성부터 반영됩니다.", type="positive")

    components.primary_button("💾 저장", on_click=_do_save)
