"""재사용 UI 조각 (app.py의 render_metric_card/카테고리 카드 대응).

sync_engine.build_products_table_html()이 만드는 테이블 HTML은 그대로
ui.html()로 꽂아 넣으면 되므로 별도 컴포넌트가 필요 없다 - dashboard/theme.py가
그 HTML이 쓰는 클래스(uic-table, uic-pill 등)를 새 디자인으로 스타일링한다.
"""
from __future__ import annotations

from nicegui import ui

from dashboard import theme

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
  """, sanitize=False).classes("w-full h-full")


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
  """, sanitize=False)


def status_donut_card(total: int, active: int, out_stock: int, needs_check: int) -> None:
  """판매 가능 / 품절 / 확인 필요를 반원 도넛 차트로 표시하는 카드."""
  dummy = max(total, 1)  # 하단 반원을 채우는 투명 세그먼트
  data = (
      [
          {'value': active,      'name': '판매 가능', 'itemStyle': {'color': '#2f6df6'}},
          {'value': out_stock,   'name': '품절',     'itemStyle': {'color': '#c9d9f7'}},
          {'value': needs_check, 'name': '확인 필요', 'itemStyle': {'color': '#e37574'}},
          {'value': dummy, 'itemStyle': {'color': 'rgba(0,0,0,0)'}, 'emphasis': {'disabled': True}},
      ] if total > 0 else [
          {'value': 1, 'itemStyle': {'color': '#e5e7eb'}},
          {'value': 1, 'itemStyle': {'color': 'rgba(0,0,0,0)'}, 'emphasis': {'disabled': True}},
      ]
  )
  option = {
      'animation': False,
      'graphic': {'elements': [
          {'type': 'text', 'left': 'center', 'top': '52%',
           'style': {'text': str(total), 'fontSize': 42, 'fontWeight': 'bold',
                     'fill': '#111827', 'textAlign': 'center'}},
      ]},
      'series': [{'type': 'pie', 'radius': ['60%', '88%'], 'center': ['50%', '72%'],
                  'startAngle': 180, 'label': {'show': False}, 'labelLine': {'show': False},
                  'emphasis': {'scale': False}, 'data': data}],
  }
  with ui.element('div').classes('tbd-card w-full h-full'):
    ui.label('상품 소싱 현황').classes('tbd-card-title px-4 pt-4 pb-1')
    ui.echart(option).classes('w-full').style('height: 260px')
    with ui.column().classes('px-4 pb-4 gap-2 w-full'):
      for label, value, color in [
          ('판매 가능', active, '#2f6df6'),
          ('품절', out_stock, '#c9d9f7'),
          ('확인 필요', needs_check, '#e37574'),
      ]:
        with ui.row().classes('w-full items-center justify-between'):
          with ui.row().classes('items-center gap-2'):
            ui.html(
                f'<span style="width:10px;height:10px;border-radius:50%;'
                f'background:{color};display:inline-block;flex-shrink:0"></span>',
                sanitize=False,
            )
            ui.label(label).classes('text-sm text-gray-500')
          ui.label(str(value)).classes('text-sm font-semibold')


def page_coverage_bar_card(brand_data: dict) -> None:
  """브랜드별 상세페이지 제작 현황 스택 바 차트 카드."""
  brands = list(brand_data.keys())
  detail_vals = [brand_data[b]["Detail"] for b in brands]
  simple_vals = [brand_data[b]["Simple"] for b in brands]
  none_vals   = [brand_data[b]["None"]   for b in brands]
  option = {
      'animation': False,
      'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
      'grid': {'top': 16, 'left': 40, 'right': 16, 'bottom': 24},
      'xAxis': {'type': 'category', 'data': brands,
                'axisLabel': {'fontSize': 12, 'fontWeight': 'bold', 'color': '#374151'}},
      'yAxis': {'type': 'value', 'minInterval': 1,
                'axisLabel': {'fontSize': 11, 'color': '#9ca3af'}},
      'series': [
          {
              'name': 'Detail', 'type': 'bar', 'stack': 'total',
              'data': detail_vals, 'itemStyle': {'color': '#2f6df6'},
              'label': {'show': True, 'position': 'inside',
                        'formatter': '{c}', 'color': '#fff', 'fontSize': 12, 'fontWeight': 'bold'},
          },
          {
              'name': 'Simple', 'type': 'bar', 'stack': 'total',
              'data': simple_vals, 'itemStyle': {'color': '#5996ef'},
              'label': {'show': True, 'position': 'inside',
                        'formatter': '{c}', 'color': '#fff', 'fontSize': 12, 'fontWeight': 'bold'},
          },
          {
              'name': 'None', 'type': 'bar', 'stack': 'total',
              'data': none_vals, 'itemStyle': {'color': '#dae4f2'},
              'label': {'show': True, 'position': 'inside',
                        'formatter': '{c}', 'color': '#6b7280', 'fontSize': 12, 'fontWeight': 'bold'},
          },
      ],
  }
  with ui.element('div').classes('tbd-card w-full h-full'):
    ui.label('상세페이지 제작 현황').classes('tbd-card-title px-4 pt-4 pb-2')
    with ui.row().classes('px-4 pb-2 gap-4 items-center'):
      for label, color in [('Detail', '#2f6df6'), ('Simple', '#5996ef'), ('미제작', '#dae4f2')]:
        with ui.row().classes('items-center gap-1.5'):
          ui.html(f'<span style="width:10px;height:10px;border-radius:2px;background:{color};'
                  f'display:inline-block;flex-shrink:0"></span>', sanitize=False)
          ui.label(label).classes('text-xs text-gray-600')
    ui.echart(option).classes('w-full').style('height: 260px')


def smartstore_donut_card(total: int, in_stock: int, out_stock: int) -> None:
  """스마트스토어 판매중 / 품절 반원 도넛 차트 카드."""
  dummy = max(total, 1)
  data = (
      [
          {'value': in_stock,  'name': '판매중', 'itemStyle': {'color': '#03c75a'}},
          {'value': out_stock, 'name': '품절',   'itemStyle': {'color': 'rgba(3, 199, 90, 0.25)'}},
          {'value': dummy, 'itemStyle': {'color': 'rgba(0,0,0,0)'}, 'emphasis': {'disabled': True}},
      ] if total > 0 else [
          {'value': 1, 'itemStyle': {'color': '#e5e7eb'}},
          {'value': 1, 'itemStyle': {'color': 'rgba(0,0,0,0)'}, 'emphasis': {'disabled': True}},
      ]
  )
  option = {
      'animation': False,
      'graphic': {'elements': [
          {'type': 'text', 'left': 'center', 'top': '52%',
           'style': {'text': str(total), 'fontSize': 42, 'fontWeight': 'bold',
                     'fill': '#111827', 'textAlign': 'center'}},
      ]},
      'series': [{'type': 'pie', 'radius': ['60%', '88%'], 'center': ['50%', '72%'],
                  'startAngle': 180, 'label': {'show': False}, 'labelLine': {'show': False},
                  'emphasis': {'scale': False}, 'data': data}],
  }
  with ui.element('div').classes('tbd-card w-full h-full'):
    ui.label('스마트스토어 현황').classes('tbd-card-title px-4 pt-4 pb-1')
    ui.echart(option).classes('w-full').style('height: 260px')
    with ui.column().classes('px-4 pb-4 gap-2 w-full'):
      for label, value, color in [
          ('판매중', in_stock, '#03c75a'),
          ('품절', out_stock, 'rgba(3, 199, 90, 0.25)'),
      ]:
        with ui.row().classes('w-full items-center justify-between'):
          with ui.row().classes('items-center gap-2'):
            ui.html(
                f'<span style="width:10px;height:10px;border-radius:50%;'
                f'background:{color};display:inline-block;flex-shrink:0"></span>',
                sanitize=False,
            )
            ui.label(label).classes('text-sm text-gray-500')
          ui.label(str(value)).classes('text-sm font-semibold')


def exchange_rate_line_card(history: list, current_rate: float) -> None:
  """환율 추세 꺾은선 그래프 카드 (소형)."""
  dates = [item["date"] for item in history]
  rates = [item["rate"] for item in history]

  if len(rates) >= 2:
    diff = round(rates[-1] - rates[0], 1)
    trend_str = f"+{diff}" if diff >= 0 else str(diff)
    trend_color = "#e37574" if diff >= 0 else "#2f6df6"
  else:
    trend_str = ""
    trend_color = "#9ca3af"

  option = {
      'animation': False,
      'grid': {'top': 8, 'left': 8, 'right': 8, 'bottom': 24, 'containLabel': True},
      'tooltip': {
          'trigger': 'axis',
          'axisPointer': {'type': 'line', 'lineStyle': {'color': '#c9d9f7', 'width': 1}},
          'formatter': '{b}<br/>₩{c}',
          'backgroundColor': '#fff',
          'borderColor': '#e5e7eb',
          'textStyle': {'color': '#1A1B1E', 'fontSize': 11},
      },
      'xAxis': {
          'type': 'category',
          'data': dates,
          'boundaryGap': False,
          'axisLine': {'show': False},
          'axisTick': {'show': False},
          'axisLabel': {
              'fontSize': 10, 'color': '#9ca3af',
              'interval': max(len(dates) // 3 - 1, 0),
          },
          'splitLine': {'show': False},
      },
      'yAxis': {
          'type': 'value',
          'scale': True,
          'axisLabel': {'show': False},
          'axisLine': {'show': False},
          'axisTick': {'show': False},
          'splitLine': {'lineStyle': {'color': '#f3f4f6', 'width': 1}},
      },
      'series': [{
          'type': 'line',
          'data': rates,
          'smooth': True,
          'symbol': 'none',
          'lineStyle': {'color': '#2f6df6', 'width': 2},
          'areaStyle': {
              'color': {
                  'type': 'linear', 'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                  'colorStops': [
                      {'offset': 0, 'color': 'rgba(47,109,246,0.18)'},
                      {'offset': 1, 'color': 'rgba(47,109,246,0.0)'},
                  ],
              }
          },
      }],
  }
  with ui.element('div').classes('tbd-card w-full h-full'):
    with ui.row().classes('px-4 pt-4 pb-0 items-center justify-between w-full'):
      ui.label('USD / KRW 환율').classes('tbd-card-title')
      if trend_str:
        ui.html(
            f'<span style="font-size:11px;color:{trend_color};font-weight:600;'
            f'background:{"rgba(227,117,116,0.1)" if "+" in trend_str else "rgba(201,217,247,0.5)"};'
            f'padding:2px 7px;border-radius:999px">{trend_str} 14일</span>',
            sanitize=False,
        )
    with ui.row().classes('px-4 pt-1 pb-0 items-baseline gap-1'):
      ui.label(f'₩{current_rate:,.1f}').classes('text-2xl font-bold')
    ui.echart(option).classes('w-full').style('height: 120px')


def scrapedo_donut_card(usage: dict | None) -> None:
  """Scrape.do 잔여 크레딧 원형 도넛 카드 (소형)."""
  if usage:
    remaining = usage.get("RemainingMonthlyRequest", 0)
    max_credits = usage.get("MaxMonthlyRequest", 1)
    used = max(max_credits - remaining, 0)
    pct = remaining / max_credits if max_credits else 0
  else:
    remaining = used = 0
    max_credits = 1
    pct = 0

  data = (
      [
          {'value': remaining, 'name': '잔여', 'itemStyle': {'color': '#2f6df6'}},
          {'value': used,      'name': '사용', 'itemStyle': {'color': '#c9d9f7'}},
      ] if usage else [
          {'value': 1, 'itemStyle': {'color': '#e5e7eb'}},
      ]
  )
  option = {
      'animation': False,
      'tooltip': {
          'trigger': 'item',
          'formatter': '{b}: {c}',
          'backgroundColor': '#fff',
          'borderColor': '#e5e7eb',
          'textStyle': {'color': '#1A1B1E', 'fontSize': 11},
      },
      'graphic': {'elements': [
          {'type': 'text', 'left': 'center', 'top': '36%',
           'style': {'text': f'{pct:.0%}', 'fontSize': 18, 'fontWeight': 'bold',
                     'fill': '#111827', 'textAlign': 'center'}},
          {'type': 'text', 'left': 'center', 'top': '54%',
           'style': {'text': '잔여', 'fontSize': 10, 'fill': '#9ca3af', 'textAlign': 'center'}},
      ]},
      'series': [{'type': 'pie', 'radius': ['56%', '78%'], 'center': ['50%', '52%'],
                  'label': {'show': False}, 'labelLine': {'show': False},
                  'emphasis': {'scale': False}, 'data': data}],
  }
  with ui.element('div').classes('tbd-card w-full h-full'):
    ui.label('Scrape.do 크레딧').classes('tbd-card-title px-4 pt-4 pb-0')
    ui.echart(option).classes('w-full').style('height: 148px')
    with ui.row().classes('px-4 pb-3 gap-4 w-full justify-center'):
      for label, value, color in [
          ('잔여', f'{remaining:,}', '#2f6df6'),
          ('사용', f'{used:,}', '#c9d9f7'),
      ]:
        with ui.row().classes('items-center gap-1.5'):
          ui.html(
              f'<span style="width:8px;height:8px;border-radius:50%;background:{color};'
              f'display:inline-block;flex-shrink:0"></span>',
              sanitize=False,
          )
          ui.label(f'{label} {value}').classes('text-xs text-gray-500')


def topbar(title: str) -> None:
  ui.html(f"""
    <div class="tbd-topbar">
      <div class="tbd-topbar-title">{title}</div>
      <div class="tbd-badge">System Active</div>
    </div>
  """, sanitize=False)


# ---------------------------------------------------------------------------
# 시맨틱 액션 버튼 - 페이지마다 제각각이던 버튼 색(검정/초록/파랑 하드코딩)을
# 위험도 기준 4종으로 통일. Tailwind "!bg-[...]" 임의값 클래스로 직접 색을
# 강제한다 - Quasar의 기본 color=primary 배경이 자체 !important 규칙을 쓰고
# 있어서 theme.py의 <style> 블록에 새 클래스를 추가하는 방식으로는(specificity를
# 올려도) 이길 수 없었다(실제로 겪음). Tailwind의 "!" 임의값 클래스가 이
# 프로젝트에서 유일하게 검증된 override 방법이라(sync.py의 기존 검정 버튼이
# 이미 이 방식으로 잘 동작 중이었음) 전부 이 방식으로 통일한다.
# ---------------------------------------------------------------------------

def primary_button(text: str, on_click=None, **kwargs) -> ui.button:
  """일반 진행 액션 (예: 로그인, 검색/생성처럼 되돌리기 쉬운 진행 버튼)."""
  return ui.button(text, on_click=on_click, **kwargs).props("unelevated rounded").classes(
      f"!bg-[{theme.BLACK_BTN_BG}] !text-[{theme.BLACK_BTN_TEXT}]"
  )


def safe_button(text: str, on_click=None, **kwargs) -> ui.button:
  """읽기 전용 / 항상 눌러도 안전한 액션 (예: 상태 조회·동기화)."""
  return ui.button(text, on_click=on_click, **kwargs).props("unelevated rounded").classes(
      f"!bg-[{theme.SUCCESS_BTN_BG}] !text-white"
  )


def live_write_button(text: str, on_click=None, **kwargs) -> ui.button:
  """실제 라이브 외부 API에 쓰는 되돌리기 어려운 액션 - 의도적으로 눈에 띄게."""
  return ui.button(text, on_click=on_click, **kwargs).props("unelevated rounded").classes(
      f"!bg-[{theme.DANGER_BTN_BG}] !text-white font-semibold"
  )


def utility_button(text: str, on_click=None, **kwargs) -> ui.button:
  """드문 관리/1회성 스크립트용 - 평소엔 안 보이게 outline으로."""
  return ui.button(text, on_click=on_click, **kwargs).props("outline rounded").classes(
      f"!text-[{theme.WARNING_BTN_TEXT}] !border-[{theme.WARNING_BTN_TEXT}]"
  )


def section_header(title: str, subtitle: str | None = None) -> None:
  """섹션 제목 - 예전엔 페이지마다 (font-bold mb-1 + 별도 서브타이틀)과
  (font-semibold mb-2, 서브타이틀 없음) 두 컨벤션이 공존했음(smartstore.py는
  한 페이지 안에서 둘 다 섞어 쓰기도 함). 이 함수 하나로 통일."""
  if subtitle:
    ui.label(title).classes("text-lg font-bold mb-1")
    ui.label(subtitle).classes("text-sm text-tbd-text-secondary mb-4")
  else:
    ui.label(title).classes("text-lg font-semibold mb-2")


async def confirm_dialog(message: str) -> bool:
  """예/아니오 확인 다이얼로그 (원래 smartstore.py의 _confirm() - 배송 페이지도
  동일 패턴이 필요해 공용으로 승격)."""
  with ui.dialog() as dialog, ui.card():
    ui.label(message)
    with ui.row().classes("w-full justify-end gap-2 mt-2"):
      ui.button("취소", on_click=lambda: dialog.submit(False)).props("flat")
      ui.button("확인", on_click=lambda: dialog.submit(True)).props("unelevated color=negative")
  return bool(await dialog)


class NiceGuiLogAdapter:
  """sync_engine.run_tbd_tracker()가 기대하는 log_container 인터페이스
  (.write(msg))를 ui.log가 쓰는 .push(msg)에 맞춰주는 얇은 어댑터."""

  def __init__(self, log_element: ui.log):
    self._log = log_element

  def write(self, msg) -> None:
    self._log.push(str(msg))
