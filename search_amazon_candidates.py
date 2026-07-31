#!/usr/bin/env python3
"""ASIN이 비어있는 NocoDB 상품들에 대해, 상품명+모델명으로 아마존을 검색해
후보 ASIN을 찾아 CSV로 정리한다. NocoDB에는 아무것도 쓰지 않는다 - 사용자가
직접 검토한 뒤 맞는 것만 골라서 ASIN 필드에 채워 넣는 용도.

검색: Scrape.do의 Amazon Search 전용 플러그인(/plugin/amazon/search) 사용,
"Ubiquiti {Model Number}"로 검색해 결과 제목에 모델명이 그대로 들어있는
것만 후보로 인정한다(느슨한 이름 매칭은 엉뚱한 제품을 후보로 올릴 위험이
커서 배제). 상품당 최대 2개 후보까지 기록(예: 같은 모델의 화이트/블랙
리스팅이 둘 다 잡히는 경우 참고용).

사용법:
    python3 search_amazon_candidates.py --dry-run       # 무엇을 검색할지만 확인 (API 호출 없음)
    python3 search_amazon_candidates.py --limit 5        # 5개만 검색 (테스트용)
    python3 search_amazon_candidates.py                  # ASIN 없는 전체 상품 검색
    python3 search_amazon_candidates.py --include-black false  # 화이트(비Clone)만 검색
"""
import argparse
import csv
import re
import time

import requests

import config
import sync_engine as se

SEARCH_URL = "https://api.scrape.do/plugin/amazon/search"
OUTPUT_CSV = "asin_candidates.csv"
MAX_CANDIDATES_PER_PRODUCT = 2


def _title_for_matching(title: str) -> str:
  """하이픈은 그대로 두고(모델명 내부 구분자), 그 외 괄호/파이프 등 구두점은
  전부 공백으로 바꿉니다. "모델명 뒤에 설명 문구가 오는 경우"(공백으로 끊김)
  와 "모델명이 사실 더 긴 다른 모델명의 접두어일 뿐인 경우"(하이픈으로 계속
  이어짐, 예: U5G가 U5G-Max-Outdoor 안에 있는 경우)를 구분하기 위함."""
  return re.sub(r"[^a-z0-9-]", " ", (title or "").lower())


def is_model_match(model_number: str, title: str) -> bool:
  model_n = (model_number or "").lower().strip()
  if not model_n:
    return False
  title_n = _title_for_matching(title)
  pattern = r"(?<![a-z0-9-])" + re.escape(model_n) + r"(?![a-z0-9-])"
  return re.search(pattern, title_n) is not None


def search_candidates(model_number: str):
  """모델명으로 아마존 검색 후, 제목에 모델명이 정확히(다른 모델명의 접두어가
  아니라 독립된 토큰으로) 들어있는 후보만 position 순으로 최대
  MAX_CANDIDATES_PER_PRODUCT개 반환."""
  query = f"Ubiquiti {model_number}"
  with se._AMAZON_SEMAPHORE:
    resp = requests.get(
        SEARCH_URL,
        params={"token": config.SCRAPEDO_TOKEN, "keyword": query, "geocode": "us"},
        timeout=60,
    )
  if resp.status_code != 200:
    return None, f"HTTP {resp.status_code}"

  try:
    data = resp.json()
  except ValueError:
    return None, "JSON 파싱 실패"

  matches = []
  for p in data.get("products", []):
    title = p.get("title", "")
    if is_model_match(model_number, title):
      matches.append({
          "asin": p.get("asin", ""),
          "title": title,
          "price": (p.get("price") or {}).get("amount"),
          "url": p.get("url", ""),
          "position": p.get("position", 999),
      })
  matches.sort(key=lambda m: m["position"])
  return matches[:MAX_CANDIDATES_PER_PRODUCT], None


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--dry-run", action="store_true")
  parser.add_argument("--limit", type=int, default=None)
  parser.add_argument(
      "--include-black", type=str, default="true",
      help="Clone(Black) 로우도 검색할지 (기본 true)",
  )
  args = parser.parse_args()
  include_black = args.include_black.lower() not in ("false", "0", "no")

  records = se.table.all()
  targets = [
      r for r in records
      if not r["fields"].get("ASIN")
      and (include_black or r["fields"].get("Product_Page") != "Clone")
  ]
  targets.sort(key=lambda r: r["fields"].get("SKU", ""))

  if args.limit is not None:
    targets = targets[: args.limit]

  print(f"검색 대상: {len(targets)}개 (Clone 포함={include_black})")

  rows_out = []
  for i, r in enumerate(targets, 1):
    f = r["fields"]
    sku = f.get("SKU", "-")
    model = f.get("Model Number") or ""
    if not model:
      print(f"[{i}/{len(targets)}] [건너뜀] '{sku}' - Model Number 없음")
      continue

    print(f"[{i}/{len(targets)}] {sku} (모델: {model})", end=" ")

    if args.dry_run:
      print("- (dry-run, 검색 안 함)")
      continue

    matches, error = search_candidates(model)
    if error:
      print(f"- [오류] {error}")
      rows_out.append({
          "SKU": sku, "Model_Number": model, "Category": f.get("Category", ""),
          "Match_Found": "오류", "Candidate_ASIN": "", "Candidate_Title": error,
          "Candidate_Price_USD": "", "Candidate_URL": "",
      })
      continue

    if not matches:
      print("- 후보 없음")
      rows_out.append({
          "SKU": sku, "Model_Number": model, "Category": f.get("Category", ""),
          "Match_Found": "없음", "Candidate_ASIN": "", "Candidate_Title": "",
          "Candidate_Price_USD": "", "Candidate_URL": "",
      })
    else:
      print(f"- 후보 {len(matches)}개")
      for m in matches:
        rows_out.append({
            "SKU": sku, "Model_Number": model, "Category": f.get("Category", ""),
            "Match_Found": "발견", "Candidate_ASIN": m["asin"],
            "Candidate_Title": m["title"], "Candidate_Price_USD": m["price"],
            "Candidate_URL": m["url"],
        })

    time.sleep(0.3)

  if args.dry_run:
    return

  with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as fp:
    writer = csv.DictWriter(fp, fieldnames=[
        "SKU", "Model_Number", "Category", "Match_Found",
        "Candidate_ASIN", "Candidate_Title", "Candidate_Price_USD", "Candidate_URL",
    ])
    writer.writeheader()
    writer.writerows(rows_out)

  found = len({row["SKU"] for row in rows_out if row["Match_Found"] == "발견"})
  print(f"\n완료: {OUTPUT_CSV}에 {len(rows_out)}행 저장 (후보 찾은 상품 {found}개)")


if __name__ == "__main__":
  main()
