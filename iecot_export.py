"""배송대행지(에코트랜스) 신청서 xlsx 생성.

사용자가 제공한 iecot_sample.xls("업로드양식" 시트, 37개 컬럼)의 컬럼 구성을
그대로 재현한 새 .xlsx를 openpyxl로 생성한다 (원본은 레거시 OLE2 .xls라
openpyxl로 열 수는 없지만, 컬럼 구조만 참고해 처음부터 새로 만들면 됨 -
에코트랜스 업로드 포털이 .xlsx를 받아주는지는 실제 신청 시 확인 필요).

각 컬럼은 Order_Fulfillment 레코드 필드에서 채우거나, iecot_config.py의
고정값을 쓴다. "AC열이 B형일 경우 해외 판매자/구매대행업체/판매대행업체를
전부 입력하라"는 원본 양식의 안내에 따라 거래유형은 항상 "B"(구매대행)로
고정하고 관련 필드를 채운다.
"""
from __future__ import annotations

import os
import tempfile
from datetime import datetime

from openpyxl import Workbook

import iecot_config

IECOT_COLUMNS = [
    "구매번호(오더번호)", "상품명(영문)", "제품URL", "이미지URL", "상품단가", "수량",
    "색상", "사이즈", "품목", "상품브랜드", "재포장여부", "사업자통관", "미국내요청사항",
    "미국내 트레킹", "신청인(아이디)", "우편번호", "수령인주소", "수령인(한글)", "연락처",
    "개인통관고유부호", "국내택배요청사항", "전자상거래", "내부주문번호", "통합옵션",
    "출고보류", "지사", "정밀검수", "FTA통관", "거래유형(A,B,Z)", "해외 판매자 부호",
    "해외 판매자 상호", "구매/배송대행 업체 부호", "구매/배송대행 업체 상호",
    "판매 대행업체 부호", "판매 대행업체 상호", "판매 대행업체 사이트", "소형 재포장",
]

assert len(IECOT_COLUMNS) == 37, f"에코트랜스 양식은 37개 컬럼이어야 하는데 {len(IECOT_COLUMNS)}개임"


def _row_values(fields: dict) -> list:
  recipient_name = fields.get("recipient_name_kr") or fields.get("orderer_name", "")
  row = [
      fields.get("local_order_number", ""),
      fields.get("naver_product_name", ""),
      "",  # 제품URL - Order_Fulfillment에 미보관
      "",  # 이미지URL - Order_Fulfillment에 미보관
      fields.get("local_unit_price_usd", ""),
      fields.get("quantity", ""),
      "",  # 색상 - 미보관
      "",  # 사이즈 - 해당 없음
      fields.get("iecot_item_code") or iecot_config.IECOT_ITEM_CODE_DEFAULT,
      "",  # 상품브랜드 - 미보관
      fields.get("repackaging_option") or iecot_config.IECOT_DEFAULT_REPACKAGING_OPTION,
      "Y" if fields.get("business_customs") else "",
      fields.get("us_side_notes", ""),
      fields.get("local_tracking_number", ""),
      recipient_name,
      fields.get("recipient_postal_code", ""),
      fields.get("recipient_address", ""),
      recipient_name,
      fields.get("recipient_phone", ""),
      fields.get("personal_customs_code", ""),
      fields.get("domestic_courier_notes", ""),
      iecot_config.IECOT_ECOMMERCE_FLAG,
      fields.get("naver_product_order_id", ""),
      fields.get("iecot_group_key", ""),
      "",  # 출고보류
      iecot_config.IECOT_BRANCH_CODE,
      "",  # 정밀검수
      "",  # FTA통관
      iecot_config.IECOT_TRANSACTION_TYPE,
      "",  # 해외 판매자 부호
      fields.get("purchase_site", ""),
      "",  # 구매/배송대행 업체 부호
      iecot_config.IECOT_AGENT_NAME,
      "",  # 판매 대행업체 부호
      iecot_config.IECOT_SALES_AGENT_NAME,
      iecot_config.IECOT_SALES_AGENT_SITE,
      "",  # 소형 재포장
  ]
  assert len(row) == 37, f"행 데이터가 37개 컬럼이 아님: {len(row)}개"
  return row


def build_iecot_xlsx(rows: list[dict]) -> str:
  """Order_Fulfillment 레코드 목록(pyairtable 스타일 {"fields": {...}})으로
  신청서 xlsx를 만들어 임시 파일 경로를 돌려준다."""
  wb = Workbook()
  ws = wb.active
  ws.title = "업로드양식"
  ws.append(IECOT_COLUMNS)
  for row in rows:
    ws.append(_row_values(row["fields"]))

  filename = f"iecot_신청서_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
  tmp_path = os.path.join(tempfile.gettempdir(), filename)
  wb.save(tmp_path)
  return tmp_path
