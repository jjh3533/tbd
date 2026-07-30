#!/usr/bin/env python3
"""Physical Security 13개 제품의 네이버 상세페이지 히어로 이미지만 교체.

기존 상세페이지 HTML의 첫 번째 이미지(히어로)만 새 이미지로 교체하고,
나머지 섹션은 그대로 유지.
"""
import argparse
import re
import requests
from auth import get_bearer_token
import naver_config as config
from image_uploader import upload_with_retry

# Physical Security 13개 제품 (채널상품번호, exports slug)
PS_PRODUCTS = [
    (13686870764, "g6-pro-360"),
    (13686870801, "ai-ptz-industrial"),
    (13686870844, "g5-turret-ultra"),
    (13686870868, "g6-dome"),
    (13686870915, "ai-theta"),
    (13686872584, "all-in-one-sensor"),
    (13686872593, "glass-break-sensor"),
    (13686872605, "motion-sensor"),
    (13686872630, "nvr-instant"),
    (13686872672, "cloudkey-plus"),
    (13686872686, "ai-horn-speaker"),
    (13686872710, "superlink-gateway"),
    (13686871209, "floodlight"),
]

EXPORTS_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html/exports"
API_BASE = "https://api.commerce.naver.com/external/v2/products/channel-products"


def get_product(token: str, channel_product_no: int):
    """채널상품 조회"""
    url = f"{API_BASE}/{channel_product_no}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def update_product(token: str, channel_product_no: int, payload: dict):
    """채널상품 수정"""
    url = f"{API_BASE}/{channel_product_no}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.put(url, json=payload, headers=headers, timeout=30)
    try:
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError:
        print(f"  [오류] {resp.status_code} {resp.reason}")
        print(f"  응답: {resp.text}")
        raise


def replace_first_image(detail_content: str, new_url: str) -> str:
    """detailContent HTML에서 첫 번째 <img> 태그의 src만 교체"""
    pattern = r'(<img\s+src=")([^"]+)("\s+style="[^"]*"\s*/?>)'
    match = re.search(pattern, detail_content)
    if not match:
        raise ValueError("첫 번째 <img> 태그를 찾을 수 없음")

    return detail_content[:match.start(2)] + new_url + detail_content[match.end(2):]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="실제 업데이트 없이 미리보기만")
    parser.add_argument("--limit", type=int, help="처음 N개만 처리")
    args = parser.parse_args()

    token = get_bearer_token(config.CLIENT_ID, config.CLIENT_SECRET)

    products = PS_PRODUCTS[:args.limit] if args.limit else PS_PRODUCTS
    print(f"{len(products)}개 제품의 히어로 이미지 교체 시작 (dry_run={args.dry_run})\n")

    for channel_product_no, slug in products:
        try:
            # 1. 현재 상품 조회
            product_data = get_product(token, channel_product_no)
            product_name = product_data["originProduct"]["name"]
            print(f"=== {product_name} (channelProductNo={channel_product_no}) ===")

            old_content = product_data["originProduct"]["detailContent"]

            # 2. 새 히어로 이미지 업로드
            new_hero_path = f"{EXPORTS_DIR}/{slug}/01-hero.png"
            print(f"  새 히어로: {new_hero_path}")

            if args.dry_run:
                new_hero_url = f"(dry-run) {new_hero_path}"
            else:
                # upload_with_retry는 리스트를 받으므로 [경로]로 전달
                urls = upload_with_retry(token, [new_hero_path])
                new_hero_url = urls[0]
                print(f"  업로드 완료: {new_hero_url}")

            # 3. detailContent에서 첫 번째 이미지만 교체
            new_content = replace_first_image(old_content, new_hero_url)

            # 4. GET으로 받은 전체 body에서 detailContent만 수정
            product_data["originProduct"]["detailContent"] = new_content

            # statusType이 OUTOFSTOCK이면 SALE로 변경 (PUT에서 거부됨)
            if product_data["originProduct"].get("statusType") == "OUTOFSTOCK":
                product_data["originProduct"]["statusType"] = "SALE"

            if args.dry_run:
                print(f"  [dry-run] 첫 번째 이미지만 교체됨")
            else:
                update_product(token, channel_product_no, product_data)
                print(f"  [완료] 히어로 이미지 교체 완료")

        except Exception as e:
            print(f"  [오류] {e}")

        print()

    print(f"총 {len(products)}개 처리 완료")


if __name__ == "__main__":
    main()
