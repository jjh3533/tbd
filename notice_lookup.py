"""
상품정보제공고시(공정거래위원회 표시사항) 유형과 필수 입력 필드를 조회하는 도우미 스크립트.

사용법:
    python notice_lookup.py 50003150
        -> 해당 카테고리에 네이버가 추천하는 productInfoProvidedNoticeType과
           그 유형에서 입력해야 하는 필드 목록(fieldName/fieldDescription/fieldMaxLength)을 출력.

    python notice_lookup.py --type OFFICE_APPLIANCES
        -> 특정 유형을 직접 지정해서 필드 목록만 조회.
"""
import sys

import requests

import naver_config as config
from auth import get_bearer_token

RECOMMEND_URL = "https://api.commerce.naver.com/external/v1/products-for-provided-notice"
DETAIL_URL = "https://api.commerce.naver.com/external/v1/products-for-provided-notice/{}"


def print_fields(entry: dict):
    notice_type = entry.get("productInfoProvidedNoticeType")
    notice_type_name = entry.get("productInfoProvidedNoticeTypeName")
    print(f"\n=== {notice_type} ({notice_type_name}) ===")
    for field in entry.get("productInfoProvidedNoticeContents", []):
        print(
            f"  - {field.get('fieldName')} (fieldType={field.get('fieldType')}, "
            f"maxLength={field.get('fieldMaxLength')})"
        )
        if field.get("fieldDescription"):
            print(f"      설명: {field['fieldDescription']}")


def main():
    token = get_bearer_token(config.CLIENT_ID, config.CLIENT_SECRET)
    headers = {"Authorization": f"Bearer {token}"}

    if len(sys.argv) < 2:
        print("사용법: python notice_lookup.py <categoryId>  또는  python notice_lookup.py --type <TYPE>")
        sys.exit(1)

    if sys.argv[1] == "--type":
        notice_type = sys.argv[2]
        resp = requests.get(DETAIL_URL.format(notice_type), headers=headers, timeout=30)
        if resp.status_code >= 300:
            print(f"조회 실패: {resp.status_code} {resp.text}")
            return
        print_fields(resp.json())
        return

    category_id = sys.argv[1]
    resp = requests.get(RECOMMEND_URL, headers=headers, params={"categoryId": category_id}, timeout=30)
    if resp.status_code >= 300:
        print(f"조회 실패: {resp.status_code} {resp.text}")
        return
    data = resp.json()
    entries = data if isinstance(data, list) else [data]
    if not entries or not entries[0]:
        print("이 카테고리에 대한 추천 유형이 없습니다. --type 옵션으로 직접 유형을 지정해서 확인해보세요.")
        return
    for entry in entries:
        print_fields(entry)


if __name__ == "__main__":
    main()
