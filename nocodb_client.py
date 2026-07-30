"""pyairtable.Table 호환 어댑터 (NocoDB REST API v2 기반).

app.py의 나머지 코드는 레코드를 pyairtable 방식(
    {"id": "<rec_id>", "fields": {...}}
)으로 다루고 있습니다. NocoDB의 데이터 API는 각 레코드가 평평한 JSON
객체(필드가 최상위 키)로 오기 때문에, 이 어댑터가 응답을 pyairtable과
동일한 모양으로 감싸줍니다. 덕분에 app.py에서 `table.all()`,
`table.get(id)`, `table.update(id, fields)`, `table.create(fields)`
호출부는 그대로 두고, Table 생성 부분만 교체하면 됩니다.

NocoDB API v2 참고:
    GET    /api/v2/tables/{tableId}/records            -> 목록 (페이지네이션)
    GET    /api/v2/tables/{tableId}/records/{recordId}  -> 단건 조회
    POST   /api/v2/tables/{tableId}/records             -> 생성
    PATCH  /api/v2/tables/{tableId}/records             -> 수정 (body에 Id 포함, path에는 안 넣음)
    인증 헤더: xc-token: <Personal API Token>

타임스탬프 처리:
    NocoDB는 모든 타임스탬프를 UTC로 저장합니다. 이 어댑터는 CreatedAt/UpdatedAt을
    자동으로 KST(Asia/Seoul)로 변환하여 반환합니다.
"""
from __future__ import annotations

from datetime import datetime
import pytz
import requests

# NocoDB가 레코드에 자동으로 붙이는 내부 메타 컬럼들 - fields에서는 제외합니다.
_META_KEYS = (
    "nc_created_by", "nc_updated_by",
    "nc_order", "__nc_deleted", "ncRecordId", "ncRecordHash",
)

# UTC → KST 변환이 필요한 타임스탬프 필드들
_TIMESTAMP_KEYS = ("CreatedAt", "UpdatedAt")

# KST 타임존
_KST = pytz.timezone('Asia/Seoul')


class NocoDBTable:
  """pyairtable.Table과 동일한 인터페이스(all/get/update/create)를 제공합니다."""

  def __init__(self, base_url: str, api_token: str, table_id: str, page_size: int = 200):
    self.base_url = base_url.rstrip("/")
    self.table_id = table_id
    self.page_size = page_size
    self.session = requests.Session()
    self.session.headers.update({
        "xc-token": api_token,
        "Content-Type": "application/json",
    })

  # -- 내부 유틸 ------------------------------------------------------
  def _records_url(self, suffix: str = "") -> str:
    return f"{self.base_url}/api/v2/tables/{self.table_id}/records{suffix}"

  @staticmethod
  def _convert_timestamp_to_kst(timestamp_str: str) -> str:
    """UTC 타임스탬프를 KST로 변환합니다.

    Args:
        timestamp_str: ISO 8601 형식의 UTC 타임스탬프 (예: "2026-07-30 09:36:27+00:00")

    Returns:
        KST로 변환된 타임스탬프 문자열 (예: "2026-07-30 18:36:27 KST")
    """
    if not timestamp_str:
      return timestamp_str

    try:
      # ISO 8601 형식 파싱
      dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

      # UTC가 아닌 경우 UTC로 변환
      if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
      elif dt.tzinfo != pytz.UTC:
        dt = dt.astimezone(pytz.UTC)

      # KST로 변환
      dt_kst = dt.astimezone(_KST)

      # 포맷팅 (KST 표시 포함)
      return dt_kst.strftime('%Y-%m-%d %H:%M:%S KST')
    except (ValueError, AttributeError):
      # 파싱 실패 시 원본 반환
      return timestamp_str

  @staticmethod
  def _wrap(raw: dict) -> dict:
    """NocoDB의 평평한 레코드를 pyairtable 스타일({"id":..,"fields":{..}})로 변환.

    타임스탬프 필드(CreatedAt, UpdatedAt)는 UTC → KST로 자동 변환됩니다.
    """
    raw = dict(raw)
    rec_id = raw.pop("Id", None)
    if rec_id is None:
      rec_id = raw.pop("id", None)

    # 타임스탬프 필드를 KST로 변환
    for ts_key in _TIMESTAMP_KEYS:
      if ts_key in raw:
        raw[ts_key] = NocoDBTable._convert_timestamp_to_kst(raw[ts_key])

    # 메타 필드 제거
    for meta_key in _META_KEYS:
      raw.pop(meta_key, None)

    return {"id": str(rec_id), "fields": raw}

  # -- pyairtable 호환 메서드 ------------------------------------------
  def all(self) -> list[dict]:
    """전체 레코드를 pyairtable 스타일 리스트로 반환합니다."""
    records = []
    offset = 0
    while True:
      resp = self.session.get(
          self._records_url(),
          params={"limit": self.page_size, "offset": offset},
          timeout=30,
      )
      resp.raise_for_status()
      data = resp.json()
      page = data.get("list", [])
      records.extend(self._wrap(r) for r in page)
      page_info = data.get("pageInfo", {}) or {}
      if page_info.get("isLastPage", True) or not page:
        break
      offset += self.page_size
    return records

  def get(self, record_id) -> dict:
    resp = self.session.get(self._records_url(f"/{record_id}"), timeout=30)
    resp.raise_for_status()
    return self._wrap(resp.json())

  def update(self, record_id, fields: dict) -> dict:
    body = dict(fields)
    body["Id"] = int(record_id)
    resp = self.session.patch(self._records_url(), json=body, timeout=30)
    resp.raise_for_status()
    # PATCH 응답은 보통 {"Id": ...}만 돌아올 수 있어, 호출부가 최신 값이
    # 필요하면 별도로 get()을 다시 부릅니다(app.py도 그렇게 하고 있음).
    try:
      result = resp.json()
    except ValueError:
      result = {}
    if isinstance(result, list):
      result = result[0] if result else {}
    merged = {**fields, **result, "Id": record_id}
    return self._wrap(merged)

  def create(self, fields: dict) -> dict:
    resp = self.session.post(self._records_url(), json=fields, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    if isinstance(result, list):
      result = result[0] if result else {}
    rec_id = result.get("Id") if isinstance(result, dict) else None
    if rec_id is not None:
      try:
        return self.get(rec_id)
      except requests.exceptions.HTTPError:
        pass
    return self._wrap({**fields, **(result if isinstance(result, dict) else {})})
