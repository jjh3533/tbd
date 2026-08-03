"""배송대행지(에코트랜스) 신청서 관련 고정값.

사용자가 제공한 실제 업로드 양식(iecot_sample.xls, "업로드양식" 시트, 37개
컬럼) + 품목분류코드 조회표(iecot_품목분류코드.csv)를 바탕으로 정한 값들이다.
naver_config.py의 ORIGIN_AREA_CODE 등과 동일하게, 한 번 결정하면 거의 안
바뀌는 사업 운영 상수라 여기에 하드코딩한다.
"""
from __future__ import annotations

# 품목분류코드 - iecot_품목분류코드.csv 기준. "네트워크장비/공유기"에 정확히
# 맞는 코드가 없어 "91 (컴퓨터관련 > 컴퓨터 주변기기)"로 확정 - 전 카테고리
# 공통 기본값. 카테고리별로 다른 코드가 필요해지면 아래 dict에 항목을 추가한다.
IECOT_ITEM_CODE_DEFAULT = "91"
IECOT_ITEM_CODE_BY_CATEGORY: dict[str, str] = {}

# 발송 창고 - Delaware.
IECOT_BRANCH_CODE = "DE"

# 거래유형: A=해외 판매자 직구매, B=구매대행, Z=알 수 없음. TBD Seoul은 구매대행.
IECOT_TRANSACTION_TYPE = "B"

# 구매/배송대행 업체 표기.
IECOT_AGENT_NAME = "TBD Seoul"

# 판매 대행업체 표기 - 사용자 확정값.
IECOT_SALES_AGENT_NAME = "TBD Seoul"
IECOT_SALES_AGENT_SITE = "smartstore.naver.com/tbdseoul"

# 전자상거래 컬럼 고정값 (업로드양식 도움말 시트 기준).
IECOT_ECOMMERCE_FLAG = "A"

# 재포장여부: 1=재포장없음, 2=재포장(박스), 3=폴리백포장, 4=포장보완.
IECOT_DEFAULT_REPACKAGING_OPTION = 1


def item_code_for_category(category: str | None) -> str:
  if category and category in IECOT_ITEM_CODE_BY_CATEGORY:
    return IECOT_ITEM_CODE_BY_CATEGORY[category]
  return IECOT_ITEM_CODE_DEFAULT
