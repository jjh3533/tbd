"""네이버 스마트스토어 판매 상태를 NocoDB에 동기화.

네이버 커머스 API에서 각 상품의 saleStatus를 조회하여 NocoDB의 SalesStatus 필드를
업데이트합니다. sync_engine의 자동 스케줄러에서 주기적으로 실행됩니다.

SalesStatus 값:
- SALE: 판매중
- OUTOFSTOCK: 품절
- SUSPENSION: 판매중지
"""
from __future__ import annotations

import time
from typing import Callable

from nocodb_client import NocoDBTable
from config import NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID
from auth import get_bearer_token
from naver_config import CLIENT_ID, CLIENT_SECRET

import requests


def sync_naver_sales_status(on_log: Callable[[str], None] | None = None) -> dict:
  """네이버 상품 판매 상태를 NocoDB에 동기화.

  Args:
      on_log: 로그 메시지 출력 콜백 (없으면 print 사용)

  Returns:
      {"updated": int, "skipped": int, "errors": int} 통계
  """
  def log(msg: str):
    if on_log:
      on_log(msg)
    else:
      print(msg)

  # 네이버 API 인증 토큰
  if not CLIENT_ID or not CLIENT_SECRET:
    log("❌ 네이버 커머스 API 시크릿이 설정되지 않았습니다 (NAS 환경에서는 정상)")
    return {"updated": 0, "skipped": 0, "errors": 0}

  try:
    bearer_token = get_bearer_token(CLIENT_ID, CLIENT_SECRET)
  except Exception as e:
    log(f"❌ 네이버 API 인증 실패: {e}")
    return {"updated": 0, "skipped": 0, "errors": 0}

  table = NocoDBTable(NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID)

  # NocoDB에서 Naver_Product_No가 있는 상품들만 조회
  all_records = table.all()
  naver_products = [
      r for r in all_records
      if r["fields"].get("Naver_Product_No") and str(r["fields"]["Naver_Product_No"]).strip() not in ("", "-")
  ]

  log(f"🔄 네이버 등록 상품 {len(naver_products)}개 상태 동기화 시작...")

  updated = 0
  skipped = 0
  errors = 0

  headers = {
      "Authorization": f"Bearer {bearer_token}",
      "Content-Type": "application/json",
  }

  for record in naver_products:
    fields = record["fields"]
    rec_id = record["id"]
    sku = fields.get("SKU", "Unknown")
    naver_id = str(fields["Naver_Product_No"]).strip()

    try:
      # 네이버 커머스 API로 상품 상세 조회
      url = f"https://api.commerce.naver.com/external/v2/products/channel-products/{naver_id}"
      response = requests.get(url, headers=headers, timeout=10)

      if response.status_code != 200:
        log(f"⚠️  {sku} (ID: {naver_id}): API 조회 실패 ({response.status_code})")
        errors += 1
        continue

      data = response.json()

      # statusType은 originProduct 안에 있음
      origin_product = data.get("originProduct", {})
      status_type = origin_product.get("statusType")

      if not status_type:
        log(f"⚠️  {sku} (ID: {naver_id}): statusType 필드 없음")
        errors += 1
        continue

      # 현재 NocoDB 값과 비교
      current_status = fields.get("SalesStatus")
      if current_status == status_type:
        skipped += 1
        continue

      # NocoDB 업데이트
      table.update(rec_id, {"SalesStatus": status_type})
      log(f"✅ {sku} (ID: {naver_id}): {current_status or 'None'} → {status_type}")
      updated += 1

      # API rate limit 방지 (네이버 API는 초당 2-3 요청 제한)
      time.sleep(0.5)

    except Exception as e:
      log(f"❌ {sku} (ID: {naver_id}): 오류 - {e}")
      errors += 1
      continue

  log(f"\n📊 동기화 완료: 업데이트 {updated}개, 변경없음 {skipped}개, 오류 {errors}개")

  return {"updated": updated, "skipped": skipped, "errors": errors}


if __name__ == "__main__":
  # 직접 실행 시 동기화 수행
  sync_naver_sales_status()
