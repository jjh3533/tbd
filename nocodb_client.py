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
"""
from __future__ import annotations

import requests

# NocoDB가 레코드에 자동으로 붙이는 내부 메타 컬럼들 - fields에서는 제외합니다.
_META_KEYS = (
    "CreatedAt", "UpdatedAt", "nc_created_by", "nc_updated_by",
    "nc_order", "__nc_deleted", "ncRecordId", "ncRecordHash",
)


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
  def _wrap(raw: dict) -> dict:
    """NocoDB의 평평한 레코드를 pyairtable 스타일({"id":..,"fields":{..}})로 변환."""
    raw = dict(raw)
    rec_id = raw.pop("Id", None)
    if rec_id is None:
      rec_id = raw.pop("id", None)
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
