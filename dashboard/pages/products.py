"""상품 리스트 (/products) - 등록된 전체 상품에 대한 필터 가능한 리스트 페이지.

기존 "/"(Main Dashboard)의 하단 표 + `/category/{slug}`/`/brand/{slug}` 두 라우트를
여기 하나로 흡수했다(2026-08-04) - 브랜드/카테고리/상태/상세페이지 유무 필터를
모두 이 페이지 하나에서 조합할 수 있다. `/`의 카테고리 카드 클릭은 `category`
쿼리 파라미터로 진입해 해당 카테고리를 초기 필터로 채운다."""
from __future__ import annotations

from nicegui import ui

from sync_engine import (
    CATEGORIES,
    build_products_table_html,
    exclude_clone_rows,
    get_latest_price_deltas,
    safe_fetch_records,
    sort_records_by_category_then_name,
    status_counts,
)
from dashboard import components, layout

_BRAND_OPTIONS = ["전체 브랜드", "UniFi", "GL.iNet"]
_SORT_OPTIONS = ["카테고리순", "이름 A-Z", "이름 Z-A", "가격 낮은순", "가격 높은순"]
_STATUS_OPTIONS = ["전체 상태", "판매 가능", "품절", "확인 필요"]
_PAGE_OPTIONS = ["전체", "Detail", "Simple", "없음"]


def _matches_status(r: dict, status: str) -> bool:
  if status == "전체 상태":
    return True
  f = r["fields"]
  needs_check = f.get("Needs_Check")
  in_stock = f.get("In_Stock")
  if status == "확인 필요":
    return bool(needs_check)
  if status == "판매 가능":
    return not needs_check and bool(in_stock)
  if status == "품절":
    return not needs_check and not in_stock
  return True


def _matches_brand(r: dict, brand_filter: str) -> bool:
  if brand_filter == "전체 브랜드":
    return True
  brand = (r["fields"].get("Brand") or "").strip()
  category = (r["fields"].get("Category") or "").strip()
  if brand_filter == "UniFi":
    return brand == "UniFi" if brand else category != "GLiNet"
  return brand == "GL.inet" if brand else category == "GLiNet"


def _matches_page(r: dict, page_filter: str) -> bool:
  if page_filter == "전체":
    return True
  page = r["fields"].get("Product_Page") or ""
  if page_filter == "없음":
    return page not in ("Detail", "Simple")
  return page == page_filter


def _apply_sort(records: list, key: str) -> list:
  if key == "이름 A-Z":
    return sorted(records, key=lambda r: (r["fields"].get("SKU") or "").lower())
  if key == "이름 Z-A":
    return sorted(records, key=lambda r: (r["fields"].get("SKU") or "").lower(), reverse=True)
  if key == "가격 낮은순":
    return sorted(records, key=lambda r: float(r["fields"].get("sale_price") or 0))
  if key == "가격 높은순":
    return sorted(records, key=lambda r: float(r["fields"].get("sale_price") or 0), reverse=True)
  return sort_records_by_category_then_name(records)


@ui.page("/products")
def products_page(category: str = "") -> None:
  with layout.frame(active_path="/products"):
    components.topbar("상품 리스트")

    records = exclude_clone_rows(safe_fetch_records(on_error=lambda msg: ui.notify(msg, type="negative")))

    total = len(records)
    active_c, out_c, check_c = status_counts(records)
    with ui.row().classes("w-full gap-5 mb-10"):
      for label, value, tone in [
          ("상품 수", total, ""),
          ("판매 가능", active_c, "success"),
          ("품절", out_c, "danger"),
          ("확인 필요", check_c, "warning"),
      ]:
        with ui.column().classes("flex-1 min-w-0"):
          components.stat_card(label, value, tone)

    cat_options = ["전체 카테고리"] + CATEGORIES
    initial_cat = category if category in CATEGORIES else cat_options[0]

    with ui.row().classes("w-full gap-4 items-center mb-6"):
      search_input = ui.input(placeholder="상품명 검색...").classes("flex-1")
      brand_select = ui.select(_BRAND_OPTIONS, value=_BRAND_OPTIONS[0], label="브랜드").classes("w-36")
      cat_select = ui.select(cat_options, value=initial_cat, label="카테고리").classes("w-44")
      status_select = ui.select(_STATUS_OPTIONS, value=_STATUS_OPTIONS[0], label="상태").classes("w-32")
      page_select = ui.select(_PAGE_OPTIONS, value=_PAGE_OPTIONS[0], label="상세페이지").classes("w-28")
      sort_select = ui.select(_SORT_OPTIONS, value=_SORT_OPTIONS[0], label="정렬").classes("w-36")

    price_deltas = get_latest_price_deltas()
    table_wrap = ui.element("div").classes("w-full")

    def refresh_table():
      query = (search_input.value or "").strip().lower()
      brand_filter = brand_select.value
      cat_filter = cat_select.value
      status_filter = status_select.value
      page_filter = page_select.value
      sort_key = sort_select.value

      filtered = [
          r for r in records
          if (not query or query in (r["fields"].get("SKU") or "").lower())
          and _matches_brand(r, brand_filter)
          and (cat_filter == "전체 카테고리" or r["fields"].get("Category") == cat_filter)
          and _matches_status(r, status_filter)
          and _matches_page(r, page_filter)
      ]
      result = _apply_sort(filtered, sort_key)

      table_wrap.clear()
      with table_wrap:
        if not result:
          ui.label("조건에 맞는 상품이 없습니다.").classes("text-tbd-text-secondary mt-4")
        else:
          html = build_products_table_html(
              result, "light",
              show_category=(cat_filter == "전체 카테고리"),
              price_deltas=price_deltas,
          )
          if html:
            ui.html(html, sanitize=False)

    refresh_table()

    search_input.on("update:model-value", lambda _: refresh_table())
    brand_select.on("update:model-value", lambda _: refresh_table())
    cat_select.on("update:model-value", lambda _: refresh_table())
    status_select.on("update:model-value", lambda _: refresh_table())
    page_select.on("update:model-value", lambda _: refresh_table())
    sort_select.on("update:model-value", lambda _: refresh_table())
