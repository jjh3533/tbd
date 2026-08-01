"""상품 등록 (/register) - app.py의 "➕ 상품 등록" 페이지 대응.

지금은 기존과 동일하게 NocoDB 추적 테이블에만 기록하는 폼이다 (실제 네이버
등록 파이프라인 main.py 연결은 계획서의 Phase 2에서 진행).

Phase A(상품등록 확장)에서 "🔍 공홈에서 불러오기" 섹션이 추가됐다: 브랜드
공홈 URL만 넣으면 official_scrapers가 이미지/가격/설명을 크롤링해오고,
retailer_search가 아마존/B&H/Adorama 후보를 찾아준다. 크롤링/검색 결과는
전부 사람이 검토·수정한 뒤에만 저장되며(자동 저장 없음), 이미지는 저장과
별개로 "이미지 다운로드" 버튼을 눌러야 로컬 Product Images 폴더에 받아진다."""
from __future__ import annotations

import asyncio
import os
import re

import requests
from nicegui import ui

import official_scrapers
import retailer_search
from sync_engine import CATEGORIES, get_current_exchange_rate, table
from dashboard import components, layout

_UNSAFE_FOLDER_CHARS = re.compile(r'[\\/:*?"<>|]')


def _safe_folder_name(name: str) -> str:
  return _UNSAFE_FOLDER_CHARS.sub("", name).strip() or "unnamed"


def _download_images(image_urls: list[str], folder_name: str) -> tuple[str, int]:
  # 지연 import: image_uploader -> naver_config는 NAVER_CLIENT_ID/SECRET을
  # 필수로 요구하고 PRODUCT_IMAGES_DIR도 맥의 Google Drive 동기화 폴더를
  # 가리킨다. NAS(도커/Linux) 배포본에는 둘 다 없어서, 상단에서 즉시
  # import하면 그 배포본 전체가 기동 실패한다. 이 버튼은 애초에 로컬 Mac
  # 전용 기능이라 여기서만 지연 import해서, 실패해도 이 버튼 클릭 시에만
  # (호출부의 try/except로) 에러 알림이 뜨고 나머지 대시보드는 정상 동작한다.
  import image_uploader

  folder = image_uploader.resolve_product_image_folder(_safe_folder_name(folder_name))
  os.makedirs(folder, exist_ok=True)
  saved = 0
  for i, url in enumerate(image_urls, start=1):
    ext = os.path.splitext(url.split("?")[0])[1] or ".jpg"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with open(os.path.join(folder, f"{i:02d}{ext}"), "wb") as fh:
      fh.write(resp.content)
    saved += 1
  return folder, saved


@ui.page("/register")
def register_page() -> None:
  with layout.frame(active_path="/register"):
    components.topbar("Register Product")

    crawl_state: dict = {"image_urls": []}

    # ------------------------------------------------------------------
    # 🔍 공홈에서 불러오기
    # ------------------------------------------------------------------
    ui.label("🔍 공홈에서 불러오기").classes("text-lg font-semibold mb-2")
    ui.label(
        "브랜드와 공홈 상품 URL을 넣고 크롤링하면 이미지/가격/설명을 자동으로"
        " 가져옵니다. 아래 필드는 전부 수정 가능하니 크롤링 결과가 틀리면"
        " 직접 고친 뒤 저장하세요."
    ).classes("text-sm text-tbd-text-secondary mb-4")

    with ui.row().classes("w-full gap-4 items-end"):
      brand_select = ui.select(
          official_scrapers.supported_brands(),
          value=official_scrapers.supported_brands()[0],
          label="Brand",
      ).classes("w-40")
      crawl_url_input = ui.input(
          "공홈 상품 URL", placeholder="e.g. https://store.ui.com/us/en/products/u6-pro"
      ).classes("flex-1")
      crawl_button = ui.button("크롤링").props("unelevated color=primary")

    crawl_status = ui.label("").classes("text-sm text-tbd-text-secondary")
    preview_images_row = ui.row().classes("w-full gap-2 flex-wrap mb-2")
    description_area = ui.textarea("설명/스펙 (참고용, 저장되지 않음)").classes("w-full").props("rows=6")
    description_area.visible = False

    with ui.row().classes("w-full gap-4 items-center"):
      download_button = ui.button("이미지 다운로드").props("outline")
      download_status = ui.label("").classes("text-sm text-tbd-text-secondary")

    ui.separator().classes("my-4")

    # ------------------------------------------------------------------
    # 🔎 리테일러 후보 검색
    # ------------------------------------------------------------------
    ui.label("🔎 리테일러 후보 검색").classes("text-lg font-semibold mb-2")
    with ui.row().classes("w-full gap-4 items-end"):
      model_number_input = ui.input("Model Number", placeholder="e.g. U6-Pro").classes("flex-1")
      search_button = ui.button("검색").props("unelevated color=primary")

    candidates_column = ui.column().classes("w-full gap-3 mb-2")

    ui.separator().classes("my-4")

    # ------------------------------------------------------------------
    # 저장 (기존 수동 입력 폼)
    # ------------------------------------------------------------------
    ui.label(
        "모델명과 MSRP(관세 서차지 포함)를 확인한 뒤 저장하면 Adorama / Amazon"
        " / B&H 자동 모니터링이 시작됩니다."
    ).classes("text-sm text-tbd-text-secondary mb-4")

    with ui.row().classes("w-full gap-8"):
      with ui.column().classes("flex-1 gap-2"):
        sku_input = ui.input("Product Name / SKU *", placeholder="e.g. Ubiquiti Cloud Gateway Ultra").classes("w-full")
        msrp_input = ui.number("MSRP USD (Surcharge Included) *", value=199.0, min=0.0, step=1.0).classes("w-full")
        naver_id_input = ui.input("Naver SmartStore No.", placeholder="e.g. 10293848").classes("w-full")
        category_select = ui.select(CATEGORIES, value=CATEGORIES[0], label="Category").classes("w-full")

      with ui.column().classes("flex-1 gap-2"):
        adorama_input = ui.input("Adorama SKU (Optional)", placeholder="e.g. ubcgultr").classes("w-full")
        asin_input = ui.input("Amazon ASIN (Optional)", placeholder="e.g. B0CWLKD9RP").classes("w-full")
        bh_input = ui.input("B&H ID (Optional)", placeholder="e.g. 1815010-REG").classes("w-full")

    # -- 크롤링 --------------------------------------------------------
    async def _do_crawl():
      url = (crawl_url_input.value or "").strip()
      if not url:
        ui.notify("공홈 URL을 입력하세요.", type="negative")
        return

      crawl_button.props("loading")
      crawl_status.text = "크롤링 중..."
      preview_images_row.clear()
      description_area.visible = False
      try:
        loop = asyncio.get_event_loop()
        product = await loop.run_in_executor(
            None, official_scrapers.fetch_product, brand_select.value, url
        )
      except Exception as e:  # noqa: BLE001
        crawl_status.text = f"크롤링 실패: {e}"
        ui.notify(f"크롤링 실패: {e}", type="negative")
        return
      finally:
        crawl_button.props(remove="loading")

      crawl_state["image_urls"] = product.image_urls
      sku_input.value = product.title
      if product.price_usd:
        msrp_input.value = product.price_usd
      model_number_input.value = product.model_number

      with preview_images_row:
        for url_img in product.image_urls:
          ui.image(url_img).classes("w-24 h-24 object-cover rounded")

      description_area.value = product.description
      description_area.visible = True
      crawl_status.text = f"이미지 {len(product.image_urls)}장 · USD {product.price_usd:.2f}"
      ui.notify("크롤링 완료 - 내용을 확인한 뒤 저장하세요.", type="positive")

    crawl_button.on_click(_do_crawl)

    # -- 이미지 다운로드 -------------------------------------------------
    async def _do_download_images():
      image_urls = crawl_state.get("image_urls") or []
      if not image_urls:
        ui.notify("먼저 크롤링해서 이미지를 불러오세요.", type="negative")
        return
      folder_name = (sku_input.value or "").strip()
      if not folder_name:
        ui.notify("SKU를 먼저 입력하세요 (폴더명으로 사용됩니다).", type="negative")
        return

      download_button.props("loading")
      download_status.text = "다운로드 중..."
      try:
        loop = asyncio.get_event_loop()
        folder, saved = await loop.run_in_executor(
            None, _download_images, image_urls, folder_name
        )
      except Exception as e:  # noqa: BLE001
        download_status.text = f"다운로드 실패: {e}"
        ui.notify(f"다운로드 실패: {e}", type="negative")
        return
      finally:
        download_button.props(remove="loading")

      download_status.text = f"{folder}에 {saved}장 저장 완료"
      ui.notify(f"이미지 {saved}장 저장 완료", type="positive")

    download_button.on_click(_do_download_images)

    # -- 리테일러 후보 검색 ------------------------------------------------
    async def _do_retailer_search():
      model_number = (model_number_input.value or "").strip()
      if not model_number:
        ui.notify("Model Number를 입력하세요.", type="negative")
        return

      search_button.props("loading")
      candidates_column.clear()
      query = f"{brand_select.value} {model_number}"

      searchers = (
          ("Amazon", retailer_search.search_amazon, asin_input),
          ("B&H", retailer_search.search_bh, bh_input),
          ("Adorama", retailer_search.search_adorama, adorama_input),
      )

      try:
        loop = asyncio.get_event_loop()
        for label, search_fn, target_input in searchers:
          with candidates_column:
            ui.label(label).classes("font-medium")
            row = ui.row().classes("w-full gap-2 flex-wrap items-center")

          matches, error = await loop.run_in_executor(None, search_fn, query, model_number)

          with row:
            if error:
              ui.label(f"확인 필요 - {error}").classes("text-sm text-tbd-text-secondary")
            elif not matches:
              ui.label("후보 없음 - 직접 입력").classes("text-sm text-tbd-text-secondary")
            else:
              for m in matches:
                def _apply(candidate=m, inp=target_input):
                  inp.value = candidate["id"]
                  ui.notify(f"{candidate['id']} 적용됨", type="positive")

                price_text = f" · ${m['price']}" if m.get("price") else ""
                ui.button(f"{m['title'][:40]}{price_text}", on_click=_apply).props("outline dense")
      finally:
        search_button.props(remove="loading")

    search_button.on_click(_do_retailer_search)

    # -- 저장 -----------------------------------------------------------
    def _submit():
      sku = (sku_input.value or "").strip()
      msrp = msrp_input.value or 0.0
      if not sku or msrp <= 0:
        ui.notify("SKU and valid MSRP are required!", type="negative")
        return

      new_record_data = {
          "SKU": sku,
          "Brand": brand_select.value,
          "MSRP_USD": float(msrp),
          "Exchange_Rate": get_current_exchange_rate(),
          "Category": category_select.value,
      }
      if model_number_input.value:
        new_record_data["Model Number"] = model_number_input.value.strip()
      if adorama_input.value:
        new_record_data["ADORAMA_ID"] = adorama_input.value.strip()
      if asin_input.value:
        new_record_data["ASIN"] = asin_input.value.strip().upper()
      if bh_input.value:
        new_record_data["BH_ID"] = bh_input.value.strip().upper()
      if naver_id_input.value:
        new_record_data["Naver_Product_No"] = naver_id_input.value.strip()

      try:
        table.create(new_record_data)
        ui.notify(f"⚡ [{sku}] successfully added to monitoring matrix!", type="positive")
        sku_input.value = ""
        naver_id_input.value = ""
        adorama_input.value = ""
        asin_input.value = ""
        bh_input.value = ""
        model_number_input.value = ""
        crawl_url_input.value = ""
        crawl_state["image_urls"] = []
        preview_images_row.clear()
        description_area.visible = False
        candidates_column.clear()
      except Exception as e:  # noqa: BLE001
        ui.notify(f"NocoDB Registration Error: {e}", type="negative")

    ui.button("⚡ Add to Inventory System", on_click=_submit).props("unelevated color=primary").classes("mt-4")
