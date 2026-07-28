"""재사용 UI 조각 (app.py의 render_metric_card/카테고리 카드 대응).

sync_engine.build_products_table_html()이 만드는 테이블 HTML은 그대로
ui.html()로 꽂아 넣으면 되므로 별도 컴포넌트가 필요 없다 - dashboard/theme.py가
그 HTML이 쓰는 클래스(uic-table, uic-pill 등)를 새 디자인으로 스타일링한다.
"""
from __future__ import annotations

from nicegui import ui


_TONE_ICON = {
    "": "📦",
    "success": "✓",
    "danger": "⨯",
    "warning": "⚠",
    "accent": "▤",
}


def stat_card(label: str, value, tone: str = "") -> None:
  """상단 통계 카드 1장. tone: "" | "success" | "danger" | "warning" | "accent"
  - tone이 있으면 카드 전체에 파스텔 배경(.tbd-card--{tone})을 입히고,
    숫자 색도 함께 맞춘다 (참고 디자인의 톤온톤 카드 스타일).
  - 우측 상단에 작은 아이콘 배지를 둬서 참고 디자인(ProductPal)의 코너
    아이콘 디테일을 재현."""
  card_class = f"tbd-card tbd-card--{tone}" if tone else "tbd-card"
  icon = _TONE_ICON.get(tone, "📦")
  ui.html(f"""
    <div class="{card_class}">
      <div class="tbd-card-icon">{icon}</div>
      <div class="tbd-card-label">{label}</div>
      <div class="tbd-card-value {tone}">{value}</div>
    </div>
  """).classes("w-full h-full")


def category_card(name: str, count: int) -> None:
  """카테고리 카드 1장 - 클릭하면 /category/{slug}로 이동하는 링크.
  ui.link을 그대로 쓰지 않고 raw <a>로 만든 이유: 카드 전체를 클릭 영역으로
  만들면서 우리 커스텀 클래스(.tbd-cat-card)를 그대로 유지하기 위함."""
  from dashboard.pages.category import category_slug
  slug = category_slug(name)
  ui.html(f"""
    <a class="tbd-cat-card" href="/category/{slug}">
      <div class="tbd-cat-card-title">{name}</div>
      <div class="tbd-cat-card-count">
        <span class="tbd-cat-card-num">{count}</span>Products
      </div>
    </a>
  """)


def topbar(title: str) -> None:
  ui.html(f"""
    <div class="tbd-topbar">
      <div class="tbd-topbar-title">{title}</div>
      <div class="tbd-badge">System Active</div>
    </div>
  """)


class NiceGuiLogAdapter:
  """sync_engine.run_tbd_tracker()가 기대하는 log_container 인터페이스
  (.write(msg))를 ui.log가 쓰는 .push(msg)에 맞춰주는 얇은 어댑터."""

  def __init__(self, log_element: ui.log):
    self._log = log_element

  def write(self, msg) -> None:
    self._log.push(str(msg))
