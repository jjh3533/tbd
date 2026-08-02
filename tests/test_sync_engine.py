"""sync_engine.py의 핵심 순수 로직에 대한 회귀 테스트.

외부 HTTP/NocoDB는 전부 mock으로 격리한다 - 실제 네트워크를 타지 않는다.
"""
from unittest.mock import patch

import sync_engine


def _record(**field_overrides):
  fields = {
      "SKU": "Test SKU",
      "Brand": "UniFi",
      "ADORAMA_ID": None,
      "ASIN": None,
      "BH_ID": None,
      "MSRP_USD": 100.0,
      "In_Stock": True,
      "Needs_Check": False,
      "Naver_Product_No": "123",
  }
  fields.update(field_overrides)
  return {"id": "rec1", "fields": fields}


def _no_retailer_hits():
  """Adorama/Amazon/B&H 전부 품절(oos)로 응답하는 patch 세트."""
  return (
      patch.object(sync_engine, "fetch_adorama_info", return_value={"price": 0.0, "in_stock": False, "status": "oos", "detail": ""}),
      patch.object(sync_engine, "fetch_amazon_info", return_value={"price": 0.0, "in_stock": False, "status": "oos", "detail": ""}),
      patch.object(sync_engine, "fetch_bh_info", return_value={"price": 0.0, "in_stock": False, "weight_kg": None, "status": "oos", "detail": ""}),
  )


class TestNocoDBUpdateFailurePropagation:
  """P1-1: table.update() 실패를 삼키지 않고 전파 + Price History 순서."""

  def test_update_failure_skips_price_history_and_status_change(self):
    record = _record(In_Stock=True, Needs_Check=False)
    patches = _no_retailer_hits()
    with patches[0], patches[1], patches[2], \
         patch.object(sync_engine.table, "update", side_effect=RuntimeError("boom")), \
         patch.object(sync_engine, "_log_change") as mock_log_change:
      log_line, status_change, ok = sync_engine.process_single_record(
          record, 1300, retailers=("Adorama", "Amazon", "B&H")
      )

    assert ok is False
    assert "실패" in log_line
    assert status_change is None
    mock_log_change.assert_not_called()

  def test_update_success_preserves_existing_behavior(self):
    record = _record(In_Stock=False, Needs_Check=False, ADORAMA_ID="x")
    with patch.object(sync_engine, "fetch_adorama_info", return_value={"price": 50.0, "in_stock": True, "status": "ok", "detail": ""}), \
         patch.object(sync_engine, "fetch_amazon_info", return_value={"price": 0.0, "in_stock": False, "status": "oos", "detail": ""}), \
         patch.object(sync_engine, "fetch_bh_info", return_value={"price": 0.0, "in_stock": False, "weight_kg": None, "status": "oos", "detail": ""}), \
         patch.object(sync_engine.table, "update") as mock_update, \
         patch.object(sync_engine.table, "get", return_value={"fields": {"sale_price": 70000}}), \
         patch.object(sync_engine, "_log_change") as mock_log_change:
      log_line, status_change, ok = sync_engine.process_single_record(
          record, 1300, retailers=("Adorama", "Amazon", "B&H")
      )

    assert ok is True
    assert status_change[0] == "IN_STOCK"
    mock_update.assert_called_once()
    assert mock_log_change.called


class TestSyncGenerationStaleness:
  """P1-2: 취소된 이전 Sync 세대의 워커는 NocoDB에 쓰지 않고 건너뜀."""

  def test_stale_generation_worker_skips_write(self):
    record = _record()
    gen1 = sync_engine._bump_sync_generation()
    gen2 = sync_engine._bump_sync_generation()
    assert gen2 == gen1 + 1

    patches = _no_retailer_hits()
    with patches[0], patches[1], patches[2], \
         patch.object(sync_engine.table, "update") as mock_update, \
         patch.object(sync_engine, "_log_change") as mock_log_change:
      log_line, status_change, ok = sync_engine.process_single_record(
          record, 1300, retailers=("Adorama", "Amazon", "B&H"), generation=gen1
      )

    assert ok is True  # 스킵이지 에러 아님
    assert status_change is None
    mock_update.assert_not_called()
    mock_log_change.assert_not_called()

  def test_current_generation_worker_writes_normally(self):
    record = _record()
    gen = sync_engine._bump_sync_generation()

    patches = _no_retailer_hits()
    with patches[0], patches[1], patches[2], \
         patch.object(sync_engine.table, "update") as mock_update:
      log_line, status_change, ok = sync_engine.process_single_record(
          record, 1300, retailers=("Adorama", "Amazon", "B&H"), generation=gen
      )

    assert ok is True
    mock_update.assert_called_once()


class TestOfficialScraperSingleCallAndNeedsCheck:
  """P2-4/5: 신규 브랜드(공홈 크롤링)를 한 번만 호출 + 실패를 Needs_Check에 반영."""

  def _glinet_record(self):
    return _record(
        Brand="GL.inet",
        Official_URL="https://gl-inet.com/products/x",
        MSRP_USD=100.0,
        In_Stock=True,
        Needs_Check=False,
    )

  def test_official_scrape_failure_sets_needs_check_with_single_call(self):
    record = self._glinet_record()
    call_count = {"n": 0}

    def fake_fetch(brand, url):
      call_count["n"] += 1
      return {"price": 0.0, "status": "check_needed", "detail": "scraper_failed: RuntimeError"}

    with patch.object(sync_engine, "fetch_official_price", side_effect=fake_fetch), \
         patch.object(sync_engine.table, "update") as mock_update:
      sync_engine.process_single_record(record, 1300, retailers=())

    assert call_count["n"] == 1, "공홈 크롤링이 1번이 아니라 여러 번 호출됨"
    written = mock_update.call_args[0][1]
    assert written["Needs_Check"] is True
    assert "공홈 크롤링 실패" in written["Check_Note"]

  def test_official_scrape_success_updates_msrp_with_single_call(self):
    record = self._glinet_record()
    call_count = {"n": 0}

    def fake_fetch(brand, url):
      call_count["n"] += 1
      return {"price": 150.0, "status": "ok", "detail": ""}

    with patch.object(sync_engine, "fetch_official_price", side_effect=fake_fetch), \
         patch.object(sync_engine.table, "update") as mock_update:
      sync_engine.process_single_record(record, 1300, retailers=())

    assert call_count["n"] == 1
    written = mock_update.call_args[0][1]
    assert written["MSRP_USD"] == 150.0
    assert written["Needs_Check"] is False


class TestCheckNeededPreservesPreviousStock:
  """check_needed_sources가 있으면(사이트 접속/파싱 실패) 품절로 확정하지 않고
  이전 재고 상태를 그대로 유지한다."""

  def test_partial_check_needed_keeps_previous_stock(self):
    record = _record(In_Stock=True)  # 이전엔 재고 있음
    with patch.object(sync_engine, "fetch_adorama_info", return_value={"price": 0.0, "in_stock": False, "status": "check_needed", "detail": "blocked"}), \
         patch.object(sync_engine, "fetch_amazon_info", return_value={"price": 0.0, "in_stock": False, "status": "oos", "detail": ""}), \
         patch.object(sync_engine, "fetch_bh_info", return_value={"price": 0.0, "in_stock": False, "weight_kg": None, "status": "oos", "detail": ""}), \
         patch.object(sync_engine.table, "update") as mock_update:
      sync_engine.process_single_record(record, 1300, retailers=("Adorama", "Amazon", "B&H"))

    written = mock_update.call_args[0][1]
    assert written["In_Stock"] is True  # 품절로 잘못 확정되지 않음
    assert written["Needs_Check"] is True


class TestExcludeCloneRows:
  """Product_Page == 'Clone' 로우(색상 옵션 클론)는 대시보드 카운트에서 제외."""

  def test_clone_rows_are_excluded(self):
    records = [
        {"id": "1", "fields": {"SKU": "A", "Product_Page": "Detail"}},
        {"id": "2", "fields": {"SKU": "A Black", "Product_Page": "Clone"}},
        {"id": "3", "fields": {"SKU": "B", "Product_Page": "Simple"}},
    ]
    result = sync_engine.exclude_clone_rows(records)
    assert [r["id"] for r in result] == ["1", "3"]

  def test_no_clone_rows_returns_all(self):
    records = [{"id": "1", "fields": {"SKU": "A", "Product_Page": "Detail"}}]
    assert sync_engine.exclude_clone_rows(records) == records
