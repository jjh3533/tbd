"""
원산지 코드를 이름으로 조회하는 도우미 스크립트.

원산지 이름 형식 (apicenter.commerce.naver.com 문서 기준):
  국산: 광역시도 > 시구군   (예: "서울특별시 > 강남구")
  수입산: 대륙 > 국가명     (예: "아시아 > 중국")
  원양산: 해역명
  기타: 직접 입력

마지막 항목(시구군/국가명/해역명)만 입력해도 LIKE 검색으로 찾아준다.

사용법:
    python origin_lookup.py 중국
    python origin_lookup.py "아시아 > 베트남"
"""
import sys

import requests

import naver_config as config
from auth import get_bearer_token

ORIGIN_QUERY_URL = "https://api.commerce.naver.com/external/v1/product-origin-areas/query"


def search(name: str):
    token = get_bearer_token(config.CLIENT_ID, config.CLIENT_SECRET)
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(ORIGIN_QUERY_URL, headers=headers, params={"name": name}, timeout=30)
    if resp.status_code >= 300:
        print(f"조회 실패: {resp.status_code} {resp.text}")
        return
    data = resp.json()
    items = data.get("originAreaCodeNames", data)
    if not items:
        print("일치하는 원산지가 없습니다. 이름을 다르게 입력해보세요 (예: '아시아 > 중국').")
        return
    for item in items:
        print(f"{item.get('name')}  ->  originAreaCode = {item.get('code')}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python origin_lookup.py <원산지명>")
        sys.exit(1)
    search(sys.argv[1])
