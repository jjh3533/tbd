"""브랜드별 상품 리스트 (/brand/{slug}) - UniFi / GL.iNet 분리 뷰.

검색·정렬·카테고리 필터를 제공하며, 필터 변경 시 테이블을 즉시 갱신한다."""
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

_UNIFI_CATEGORIES = [c for c in CATEGORIES if c != "GLiNet"]

_BRAND_CONFIG = {
    "unifi": {
        "label": "UniFi",
        "brand_value": "UniFi",
        "categories": _UNIFI_CATEGORIES,
    },
    "glinet": {
        "label": "GL.iNet",
        "brand_value": "GL.inet",
        "categories": _UNIFI_CATEGORIES,
    },
}

_SORT_OPTIONS = ["카테고리순", "이름 A-Z", "이름 Z-A", "가격 낮은순", "가격 높은순"]
_STATUS_OPTIONS = ["전체 상태", "판매 가능", "품절", "확인 필요"]


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


def _filter_brand(records: list, config: dict) -> list:
    """Brand 필드 우선, 없으면 Category로 폴백."""
    brand_value = config["brand_value"]
    categories = set(config["categories"])
    result = []
    for r in records:
        brand = (r["fields"].get("Brand") or "").strip()
        category = (r["fields"].get("Category") or "").strip()
        if brand:
            if brand == brand_value:
                result.append(r)
        elif category in categories:
            result.append(r)
    return result


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


@ui.page("/brand/{slug}")
def brand_page(slug: str) -> None:
    config = _BRAND_CONFIG.get(slug)

    with layout.frame(active_path=f"/brand/{slug}"):
        if config is None:
            components.topbar("Not Found")
            ui.label(f"알 수 없는 브랜드: {slug}").classes("text-tbd-text-secondary")
            return

        components.topbar(config["label"])

        all_records = exclude_clone_rows(
            safe_fetch_records(on_error=lambda msg: ui.notify(msg, type="negative"))
        )
        brand_records = _filter_brand(all_records, config)

        active_c, out_c, check_c = status_counts(brand_records)
        with ui.row().classes("w-full gap-5 mb-10"):
            for label, value, tone in [
                ("상품 수", len(brand_records), ""),
                ("판매 가능", active_c, "success"),
                ("품절", out_c, "danger"),
                ("확인 필요", check_c, "warning"),
            ]:
                with ui.column().classes("flex-1 min-w-0"):
                    components.stat_card(label, value, tone)

        cat_options = ["전체 카테고리"] + config["categories"]
        show_cat_col = len(config["categories"]) > 1

        with ui.row().classes("w-full gap-4 items-center mb-6"):
            search_input = ui.input(placeholder="상품명 검색...").classes("flex-1")
            cat_select = ui.select(cat_options, value=cat_options[0], label="카테고리").classes("w-44")
            status_select = ui.select(_STATUS_OPTIONS, value=_STATUS_OPTIONS[0], label="상태").classes("w-32")
            sort_select = ui.select(_SORT_OPTIONS, value=_SORT_OPTIONS[0], label="정렬").classes("w-36")

        price_deltas = get_latest_price_deltas()
        table_wrap = ui.element("div").classes("w-full")

        def refresh_table():
            query = (search_input.value or "").strip().lower()
            cat_filter = cat_select.value
            status_filter = status_select.value
            sort_key = sort_select.value

            filtered = [
                r for r in brand_records
                if (not query or query in (r["fields"].get("SKU") or "").lower())
                and (cat_filter == "전체 카테고리" or r["fields"].get("Category") == cat_filter)
                and _matches_status(r, status_filter)
            ]
            result = _apply_sort(filtered, sort_key)

            table_wrap.clear()
            with table_wrap:
                if not result:
                    ui.label("조건에 맞는 상품이 없습니다.").classes("text-tbd-text-secondary mt-4")
                else:
                    html = build_products_table_html(
                        result, "light",
                        show_category=show_cat_col,
                        price_deltas=price_deltas,
                    )
                    if html:
                        ui.html(html, sanitize=False)

        refresh_table()

        search_input.on("update:model-value", lambda _: refresh_table())
        cat_select.on("update:model-value", lambda _: refresh_table())
        status_select.on("update:model-value", lambda _: refresh_table())
        sort_select.on("update:model-value", lambda _: refresh_table())
