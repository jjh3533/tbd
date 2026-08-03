"""주문 이행(발주→현지배송→배송대행지→국제배송→네이버발송) 상태 관리 - "주문판
sync_engine". orders.py/purchase_orders.py/shipping.py가 공유하는 로직을
여기 모아둔다 (날짜창 조회 헬퍼, 상품명↔NocoDB 매칭, Order_Fulfillment
NocoDB 테이블 접근).

NOCODB_ORDER_TABLE_ID가 아직 설정되지 않은 환경(테이블 생성 전)에서도
대시보드가 죽지 않도록 order_table은 None일 수 있다 - sync_engine.py의
history_table과 동일한 가드 패턴.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import config
from nocodb_client import NocoDBTable

order_table = (
    NocoDBTable(config.NOCODB_URL, config.NOCODB_API_TOKEN, config.NOCODB_ORDER_TABLE_ID)
    if config.NOCODB_ORDER_TABLE_ID else None
)

_BRAND_WORDS = ("unifi", "gl.inet", "glinet", "gl-inet")


# ---------------------------------------------------------------------------
# 네이버 주문 API 날짜창 조회 헬퍼 (원래 dashboard/pages/orders.py에 있었으나
# purchase_orders.py도 동일한 "최근 N일을 하루 단위로 나눠 조회" 로직이
# 필요해서 여기로 승격)
# ---------------------------------------------------------------------------

def day_window(dt: datetime) -> tuple[datetime, datetime]:
  """dt가 속한 하루(00:00~23:59:59)의 (시작, 끝) 튜플. 네이버 API가 최대
  24시간 범위만 허용하므로, 여러 날짜를 조회할 땐 이 단위로 나눠 호출한다."""
  start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
  return start, start + timedelta(hours=23, minutes=59, seconds=59)


def merge_orders_by_id(order_lists: list[list[dict]]) -> dict[str, dict]:
  """여러 날짜 구간에서 받은 주문 목록을 productOrderId 기준으로 병합한다
  (같은 주문이 여러 구간에 걸쳐 겹쳐 나올 수 있어 중복 제거 필요)."""
  merged: dict[str, dict] = {}
  for orders in order_lists:
    for o in orders:
      order_id = o.get("productOrderId")
      if order_id:
        merged[order_id] = o
  return merged


# ---------------------------------------------------------------------------
# 상품명 <-> NocoDB 레코드 매칭 (orders.py의 가격 링크, purchase_orders.py의
# 발주 폼 자동채움 둘 다 필요)
# ---------------------------------------------------------------------------

def _normalize_for_match(text: str) -> str:
  text = text.lower()
  for word in _BRAND_WORDS:
    text = text.replace(word, "")
  return " ".join(text.split())


def match_sku_for_order(product_name: str, records: list[dict]) -> dict | None:
  """Naver 주문의 productName으로 NocoDB 레코드를 best-effort 매칭 - 브랜드
  단어를 지우고 정규화해서 Model_Number/SKU가 상품명 안에 포함되는지 본다.
  이름이 항상 정확히 일치하지 않아 매칭에 실패할 수도 있다."""
  name_norm = _normalize_for_match(product_name)
  if not name_norm:
    return None
  best = None
  for r in records:
    f = r["fields"]
    for cand in (f.get("Model_Number") or "", f.get("SKU") or ""):
      cand_norm = _normalize_for_match(cand)
      if cand_norm and cand_norm in name_norm:
        if best is None or len(cand_norm) > len(best[1]):
          best = (r, cand_norm)
  return best[0] if best else None


# ---------------------------------------------------------------------------
# Order_Fulfillment NocoDB 로우 조회/생성/갱신
# ---------------------------------------------------------------------------

def get_all() -> list[dict]:
  if order_table is None:
    return []
  return order_table.all()


def find_by_order_id(product_order_id: str, rows: list[dict] | None = None) -> dict | None:
  rows = rows if rows is not None else get_all()
  return next(
      (r for r in rows if r["fields"].get("naver_product_order_id") == product_order_id), None
  )


def find_or_create(product_order_id: str, defaults: dict, rows: list[dict] | None = None) -> dict:
  """이 주문번호의 Order_Fulfillment 로우가 있으면 그대로, 없으면 defaults로
  새로 만들어 돌려준다. order_table이 없으면(테이블 미생성) RuntimeError."""
  if order_table is None:
    raise RuntimeError("NOCODB_ORDER_TABLE_ID가 설정되지 않았습니다 - create_order_fulfillment_table.py를 먼저 실행하세요.")
  existing = find_by_order_id(product_order_id, rows)
  if existing:
    return existing
  fields = {"naver_product_order_id": product_order_id, **defaults}
  created = order_table.create(fields)
  return created


def update_fields(record_id: str, fields: dict) -> dict:
  if order_table is None:
    raise RuntimeError("NOCODB_ORDER_TABLE_ID가 설정되지 않았습니다.")
  return order_table.update(record_id, fields)


def derive_fulfillment_status(fields: dict) -> str:
  """저장된 필드가 아니라 매번 계산 - status_counts()와 동일한 철학."""
  if fields.get("naver_dispatched_at"):
    return "발송완료"
  if fields.get("intl_tracking_number"):
    return "국제배송중"
  if fields.get("iecot_applied_at"):
    return "배송대행지 신청완료"
  if fields.get("local_tracking_number"):
    return "현지배송중"
  if fields.get("local_order_number"):
    return "발주완료"
  return "발주대기"
