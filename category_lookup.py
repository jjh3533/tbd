"""
카테고리 이름으로 leafCategoryId를 찾는 도우미 스크립트.

사용법:
    python category_lookup.py "공유기"
    python category_lookup.py "AP"

전체 카테고리 목록을 받아와서 이름에 검색어가 포함된 항목을 출력한다.
리프 카테고리(하위 카테고리가 없는 마지막 단계)만 상품 등록에 사용할 수 있다.
"""
import sys

import requests

import naver_config as config
from auth import get_bearer_token


def fetch_all_categories(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(config.CATEGORY_API_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def search(keyword: str):
    token = get_bearer_token(config.CLIENT_ID, config.CLIENT_SECRET)
    categories = fetch_all_categories(token)

    # 응답 구조는 커머스API 버전에 따라 다를 수 있어 방어적으로 순회한다.
    def walk(node, path):
        name = node.get("name") or node.get("categoryName") or ""
        cur_path = path + [name] if name else path
        children = node.get("children") or node.get("childCategories") or []
        is_leaf = node.get("leaf", not bool(children))

        if keyword.lower() in name.lower() and is_leaf:
            cid = node.get("id") or node.get("categoryId") or node.get("wholeCategoryName")
            print(f"{' > '.join(cur_path)}  ->  leafCategoryId = {cid}")

        for child in children:
            walk(child, cur_path)

    if isinstance(categories, list):
        for node in categories:
            walk(node, [])
    else:
        walk(categories, [])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python category_lookup.py <검색어>")
        sys.exit(1)
    search(sys.argv[1])
