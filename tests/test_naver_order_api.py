"""naver_order_api.py의 시간대 정규화 + 24시간 제한 검증 테스트."""
from datetime import datetime, timedelta, timezone

import pytest
from unittest.mock import patch

import naver_order_api as api


class TestToKst:
  def test_naive_datetime_is_localized_as_is(self):
    naive = datetime(2026, 8, 3, 10, 0, 0)
    result = api._to_kst(naive)
    assert result.strftime("%Y-%m-%dT%H:%M:%S.000+09:00") == "2026-08-03T10:00:00.000+09:00"

  def test_aware_utc_datetime_converts_correctly(self):
    """예전 버그: tzinfo와 무관하게 문자열 끝에 무조건 +09:00을 붙여서, aware
    UTC datetime이 들어오면 실제 조회 시간이 9시간 어긋났음."""
    utc_dt = datetime(2026, 8, 3, 1, 0, 0, tzinfo=timezone.utc)  # UTC 01:00 = KST 10:00
    result = api._to_kst(utc_dt)
    assert result.hour == 10
    assert result.day == 3


class Test24HourLimit:
  def test_get_product_orders_rejects_over_24h(self):
    with patch.object(api, "_get_headers", return_value={}):
      with pytest.raises(ValueError):
        api.get_product_orders(datetime(2026, 8, 1), datetime(2026, 8, 3))

  def test_get_product_order_claims_rejects_over_24h(self):
    """예전엔 get_product_orders에만 있고 클레임 조회엔 이 검증이 빠져있었음."""
    with patch.object(api, "_get_headers", return_value={}):
      with pytest.raises(ValueError):
        api.get_product_order_claims(datetime(2026, 8, 1), datetime(2026, 8, 3))

  def test_get_product_order_claims_accepts_24h_window(self):
    with patch.object(api, "_get_headers", return_value={}), \
         patch.object(api.requests, "get") as mock_get:
      mock_get.return_value.raise_for_status = lambda: None
      mock_get.return_value.json = lambda: {"content": []}
      from_date = datetime(2026, 8, 1, 0, 0, 0)
      to_date = from_date + timedelta(hours=23, minutes=59, seconds=59)
      api.get_product_order_claims(from_date, to_date)
      mock_get.assert_called_once()
