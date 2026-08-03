"""네이버 스마트스토어에 등록된 전체 상품의 가격/재고를 NocoDB 데이터로 업데이트.

update_price_stock.py와 달리 TARGET_PRODUCTS(수작업 등록 리스트)에 없어도
Naver_Product_No가 있는 상품이면 전부 대상으로 삼는다 - /smartstore 페이지처럼
"등록된 전체 상품"을 다루는 화면에서 쓰기 위함. 가격/재고를 실제로 반영하는
로직(GET 전체 조회 -> salePrice/stockQuantity만 교체 -> 전체 PUT, 화이트/블랙
옵션 처리)은 update_price_stock.py의 검증된 함수를 그대로 재사용한다.

이 스크립트는 원래 하드코딩된 환율(1446.6)로 USD 필드를 직접 변환하고
필드 2개만 PATCH하는 방식이었는데, NocoDB에 이미 원화로 계산되어 있는
sale_price를 안 쓰고 재고도 실제 수량이 아니라 999/0으로 뭉뚱그리는 등
다른 데이터 수정 스크립트들의 안전 패턴(GET 전체->PUT 전체, dry-run/limit)을
전혀 안 지키고 있어서 --dry-run 없이 라이브 API에 바로 반영되고 있었다.
사고 나기 전에 발견해서 전면 재작성함.
"""
from __future__ import annotations

import time
from typing import Callable

import config
import naver_config
from auth import get_bearer_token
from nocodb_client import NocoDBTable
from update_price_stock import (
    BLACK_LABEL,
    DEFAULT_STOCK_IN,
    DEFAULT_STOCK_OUT,
    WHITE_LABEL,
    apply_price_stock,
    get_channel_product,
    put_channel_product,
)


def sync_naver_price_stock(
    on_log: Callable[[str], None] | None = None,
    dry_run: bool = True,
    limit: int | None = None,
) -> dict:
  """네이버 등록 상품(Naver_Product_No 보유, Black 로우 제외) 전체의 가격/재고를
  NocoDB 값(sale_price/In_Stock) 기준으로 업데이트.

  Args:
      on_log: 로그 메시지 출력 콜백 (없으면 print 사용)
      dry_run: True면 무엇이 바뀔지만 출력하고 실제 API 호출은 하지 않음 (기본값)
      limit: 처리할 최대 상품 수 (None이면 전체)

  Returns:
      {"updated": int, "skipped": int, "errors": int} 통계
  """
  def log(msg: str):
    if on_log:
      on_log(msg)
    else:
      print(msg)

  if not naver_config.CLIENT_ID or not naver_config.CLIENT_SECRET:
    log("❌ 네이버 커머스 API 시크릿이 설정되지 않았습니다 (NAS 환경에서는 정상)")
    return {"updated": 0, "skipped": 0, "errors": 0}

  table = NocoDBTable(config.NOCODB_URL, config.NOCODB_API_TOKEN, config.NOCODB_TABLE_ID)
  all_records = table.all()
  records_by_sku = {r["fields"].get("SKU", "").strip(): r for r in all_records}

  # 화이트 로우만 대상으로 순회 (Black은 화이트 처리 시 옵션으로 함께 반영됨)
  targets = [
      r for r in all_records
      if r["fields"].get("Naver_Product_No")
      and str(r["fields"]["Naver_Product_No"]).strip() not in ("", "-")
      and "Black" not in r["fields"].get("SKU", "")
  ]
  if limit is not None:
    targets = targets[:limit]

  log(f"🔄 네이버 등록 상품 {len(targets)}개 가격/재고 {'미리보기' if dry_run else '업데이트'} 시작...")

  token = None
  if not dry_run:
    token = get_bearer_token(naver_config.CLIENT_ID, naver_config.CLIENT_SECRET)

  updated = 0
  skipped = 0
  errors = 0

  for record in targets:
    fields = record["fields"]
    sku = fields.get("SKU", "Unknown")
    naver_id = str(fields["Naver_Product_No"]).strip()

    new_price = fields.get("sale_price")
    if not new_price:
      log(f"⚠️  {sku} (ID: {naver_id}): NocoDB 'sale_price' 값 없음 - 건너뜀")
      skipped += 1
      continue
    new_price = int(new_price)
    new_stock = DEFAULT_STOCK_IN if fields.get("In_Stock") else DEFAULT_STOCK_OUT

    # 화이트/블랙 색상 옵션 짝 (update_price_stock.py와 동일한 규칙)
    option_overrides = None
    black_rec = records_by_sku.get(f"{sku} Black")
    if black_rec:
      black_fields = black_rec["fields"]
      black_price = black_fields.get("sale_price")
      if black_price:
        black_stock = DEFAULT_STOCK_IN if black_fields.get("In_Stock") else DEFAULT_STOCK_OUT
        option_overrides = {
            WHITE_LABEL: (0, new_stock),
            BLACK_LABEL: (int(black_price) - new_price, black_stock),
        }

    if dry_run:
      log(f"[미리보기] {sku} (ID: {naver_id}): ₩{new_price:,} / 재고 {new_stock}"
          + (" (화이트/블랙 옵션 반영)" if option_overrides else ""))
      updated += 1
      continue

    try:
      current = get_channel_product(token, int(naver_id))
      updated_body = apply_price_stock(current, new_price, new_stock, option_overrides)
      put_channel_product(token, int(naver_id), updated_body)
      log(f"✅ {sku} (ID: {naver_id}): ₩{new_price:,} / 재고 {new_stock}")
      updated += 1
    except Exception as e:  # noqa: BLE001
      log(f"❌ {sku} (ID: {naver_id}): 오류 - {e}")
      errors += 1

    # API rate limit 방지
    time.sleep(0.5)

  log(f"\n📊 {'미리보기' if dry_run else '업데이트'} 완료: {updated}개, 건너뜀 {skipped}개, 오류 {errors}개")

  return {"updated": updated, "skipped": skipped, "errors": errors}


if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument("--dry-run", action="store_true")
  parser.add_argument("--limit", type=int, default=None)
  args = parser.parse_args()

  sync_naver_price_stock(dry_run=args.dry_run, limit=args.limit)
