"""네이버 스마트스토어센터 공식 택배사 코드표 (222개, smartstore/delivery-companies_*.xls 기준).

배송(/shipping) 페이지의 "스마트스토어 등록(발송 처리)" 택배사 선택 드롭다운이 사용.
JSON은 1회성으로 공식 xls에서 뽑아낸 정적 데이터라 NAS엔 xlrd/pandas 없이도 그대로 배포 가능.
"""
from __future__ import annotations

import json
import os

_JSON_PATH = os.path.join(os.path.dirname(__file__), "naver_delivery_companies.json")

DEFAULT_DELIVERY_COMPANY = "ACE"  # ACEexpress - naver_config.DELIVERY_COMPANY와 동일한 기본값


def load_delivery_companies() -> list[dict]:
    """[{"code": "CJGLS", "name": "CJ대한통운"}, ...] 형태로 전체 목록 반환."""
    with open(_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def delivery_company_options() -> dict[str, str]:
    """NiceGUI ui.select용 {code: "이름 (코드)"} 딕셔너리, ACEexpress가 최상단에 오도록 정렬."""
    companies = load_delivery_companies()
    companies.sort(key=lambda c: (c["code"] != DEFAULT_DELIVERY_COMPANY, c["name"]))
    return {c["code"]: f'{c["name"]} ({c["code"]})' for c in companies}
