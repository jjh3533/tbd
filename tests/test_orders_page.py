"""dashboard/pages/orders.py의 "최근 7일" 분할 조회 관련 순수 함수 테스트.

NiceGUI 페이지 자체(@ui.page 데코레이터가 붙은 함수)는 실행 컨텍스트가 필요해
직접 테스트하지 않고, 그 안에서 쓰는 순수 헬퍼(_day_window, _merge_orders_by_id)
만 분리해서 검증한다.
"""
from datetime import datetime, timedelta

from dashboard.pages.orders import _day_window, _merge_orders_by_id


class TestDayWindow:
  def test_returns_start_and_end_of_day(self):
    dt = datetime(2026, 8, 3, 15, 30, 0)
    start, end = _day_window(dt)
    assert start == datetime(2026, 8, 3, 0, 0, 0)
    assert end == datetime(2026, 8, 3, 23, 59, 59)

  def test_window_is_within_24_hours(self):
    start, end = _day_window(datetime(2026, 8, 3, 15, 30, 0))
    assert (end - start).total_seconds() <= 24 * 3600

  def test_seven_day_range_covers_expected_dates(self):
    now = datetime(2026, 8, 3, 15, 30, 0)
    windows = [_day_window(now - timedelta(days=i)) for i in range(7)]
    assert len(windows) == 7
    assert windows[0][0].date() == now.date()
    assert windows[6][0].date() == (now - timedelta(days=6)).date()


class TestMergeOrdersById:
  def test_deduplicates_across_windows(self):
    order_lists = [
        [{"productOrderId": "A1", "productName": "x"}, {"productOrderId": "A2", "productName": "y"}],
        [{"productOrderId": "A1", "productName": "x-dup"}],  # A1이 두 구간에 걸쳐 중복 등장
    ]
    merged = _merge_orders_by_id(order_lists)
    assert len(merged) == 2
    assert set(merged.keys()) == {"A1", "A2"}

  def test_empty_lists_produce_empty_result(self):
    assert _merge_orders_by_id([]) == {}
    assert _merge_orders_by_id([[], []]) == {}

  def test_orders_without_id_are_skipped(self):
    order_lists = [[{"productName": "no id here"}]]
    assert _merge_orders_by_id(order_lists) == {}
