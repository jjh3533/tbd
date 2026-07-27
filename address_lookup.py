"""
판매자 주소록(배송지/반품지) ID를 조회하는 도우미 스크립트.

config.py의 SHIPPING_ADDRESS_ID / RETURN_ADDRESS_ID를 채우기 위해 필요하다.
스마트스토어센터 > 판매자정보 > 배송지 관리에 주소가 등록되어 있어야 값이 조회된다.

사용법:
    python address_lookup.py
"""
import requests

import naver_config as config
from auth import get_bearer_token

ADDRESS_BOOK_URL = "https://api.commerce.naver.com/external/v1/seller/addressbooks-for-page"


def main():
    token = get_bearer_token(config.CLIENT_ID, config.CLIENT_SECRET)
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(ADDRESS_BOOK_URL, headers=headers, params={"page": 1}, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    items = data if isinstance(data, list) else data.get("addressBooks") or data.get("contents") or [data]
    if not items or items == [{}]:
        print("주소록이 비어 있습니다 (addressBooks: []).")
        print("스마트스토어센터 > 판매자정보 > 배송지/반품지 관리에서 주소를 먼저 등록해주세요.")
        return
    for item in items:
        print(item)


if __name__ == "__main__":
    main()
