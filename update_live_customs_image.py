"""이미 등록된 상품들의 라이브 상세페이지에서 "통관 안내" 섹션 이미지만 교체한다.

배경: build_pages.py의 TRUST_TO_FOOTER에 있던 관/부가세 안내 문구가 부정확해서
고쳤는데, 이미 네이버에 등록된 20개 상품은 그 문구가 박힌 예전 이미지가 이미
detailContent에 올라가 있다. 이 스크립트는:
    1) 로컬 .dc.html에서 (이미 문구가 고쳐진 상태로) "통관 안내" 섹션만 다시
       export한 새 PNG를 업로드
    2) 라이브 상품의 detailContent를 파싱해 각 <img> URL을 순서대로 나열
    3) 로컬 export 폴더의 섹션 순서(파일명 앞자리 번호)에서 "customs"가 몇 번째인지
       세어, 라이브 detailContent에서 같은 인덱스의 이미지 개수가 일치하는지
       검증한 뒤(다르면 안전하게 건너뜀) 그 인덱스의 URL만 새 URL로 교체
    4) 나머지는 전부 그대로 PUT

사용법:
    python3 update_live_customs_image.py --dry-run       # 무엇이 바뀔지만 확인
    python3 update_live_customs_image.py --limit 1        # 실제로 1개만 반영
    python3 update_live_customs_image.py                  # 전체 반영
"""
import argparse
import json
import os
import re

import requests

import naver_config as config
from auth import get_bearer_token
from image_uploader import upload_with_retry

API_BASE = "https://api.commerce.naver.com/external/v2/products/channel-products"
GD = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html"
EXPORTS_DIR = f"{GD}/exports"
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registered_log.json")

# registered_log.json의 상품명 -> exports/<slug> 폴더명
NAME_TO_SLUG = {
    "UniFi Cloud Gateway Ultra UCG-Ultra": "ucg-ultra",
    "UniFi U7 Pro XG": "u7-pro-xg",
    "UniFi Dream Router 7": "dream-router-7",
    "UniFi Dream Router 5G Max": "dream-router-5g-max",
    "UniFi U7 Lite": "u7-lite",
    "UniFi U7 Long Range": "u7-long-range",
    "UniFi U7 Pro": "u7-pro",
    "UniFi U7 Pro Max": "u7-pro-max",
    "UniFi UCG Fiber": "ucg-fiber",
    "UniFi UCG Max": "ucg-max",
    "UniFi UX7": "ux7",
    "UniFi Switch Flex 2.5G": "usw-flex-2-5g",
    "UniFi Switch Flex 2.5G PoE": "usw-flex-2-5g-poe",
    "UniFi Switch Flex mini": "usw-flex-mini",
    "UniFi Switch Flex mini 2.5G": "usw-flex-mini-2-5g",
    "UniFi Switch Lite 16 PoE": "usw-lite-16-poe",
    "UniFi Switch Lite 8 PoE": "usw-lite-8-poe",
    "UniFi Switch Ultra 210W": "usw-ultra-210w",
    "UniFi Switch Ultra 60W": "usw-ultra-60w",
    "UniFi Cloud Gateway Industrial UCG-Industrial": "ucg-industrial",
}


def get_channel_product(token, channel_no):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/{channel_no}", headers=headers, timeout=30)
    if resp.status_code >= 300:
        raise RuntimeError(f"조회 실패 {resp.status_code}: {resp.text}")
    return resp.json()


def put_channel_product(token, channel_no, body):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.put(f"{API_BASE}/{channel_no}", headers=headers, json=body, timeout=60)
    if resp.status_code >= 300:
        raise RuntimeError(f"수정 실패 {resp.status_code}: {resp.text}")
    return resp.json() if resp.text else {}


def local_customs_index(slug):
    """로컬 export 폴더에서 파일명 앞자리 번호로 정렬했을 때, "customs"가 몇 번째(0-index)인지."""
    folder = os.path.join(EXPORTS_DIR, slug)
    files = sorted(f for f in os.listdir(folder) if f.endswith(".png"))
    total = len(files)
    for i, f in enumerate(files):
        if "customs" in f:
            return i, total, os.path.join(folder, f)
    return None, total, None


def live_image_urls(detail_content_html):
    return re.findall(r'<img src="([^"]+)"', detail_content_html)


def rebuild_detail_content(urls):
    return "".join(f'<img src="{u}" style="width:860px;display:block;" />' for u in urls)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    with open(LOG_PATH) as f:
        log = json.load(f)

    token = None
    if not args.dry_run:
        token = get_bearer_token(config.CLIENT_ID, config.CLIENT_SECRET)

    processed = 0
    for name, slug in NAME_TO_SLUG.items():
        if args.limit is not None and processed >= args.limit:
            break

        entry = log.get(name)
        if not entry:
            print(f"[건너뜀] '{name}' - registered_log.json에 없음")
            continue
        channel_no = entry.get("smartstoreChannelProductNo")

        print(f"\n=== {name} (channelProductNo={channel_no}) ===")

        local_idx, local_total, customs_png = local_customs_index(slug)
        if local_idx is None:
            print("  [오류] 로컬 export에서 customs 이미지를 못 찾음 - 건너뜀")
            continue

        try:
            if args.dry_run:
                current = entry
            else:
                current = get_channel_product(token, int(channel_no))

            origin = current["originProduct"]
            urls = live_image_urls(origin.get("detailContent", ""))

            if len(urls) != local_total:
                print(f"  [오류] 라이브 이미지 개수({len(urls)}) != 로컬 섹션 개수({local_total})"
                      " - 순서 매칭 신뢰 불가, 안전하게 건너뜀")
                continue

            old_url = urls[local_idx]
            print(f"  통관 이미지 인덱스: {local_idx}/{local_total}")
            print(f"  기존 URL: {old_url}")

            if args.dry_run:
                print(f"  (dry-run) 새 이미지 업로드 후 이 인덱스만 교체 예정: {customs_png}")
                processed += 1
                continue

            new_urls_result = upload_with_retry(token, [customs_png])
            new_url = new_urls_result[0]
            print(f"  새 URL: {new_url}")

            urls[local_idx] = new_url
            origin["detailContent"] = rebuild_detail_content(urls)

            if origin.get("statusType") == "OUTOFSTOCK":
                origin["statusType"] = "SALE"

            put_channel_product(token, int(channel_no), current)
            print("  [완료]")
        except Exception as e:  # noqa: BLE001
            print(f"  [오류] {e}")

        processed += 1

    print(f"\n총 {processed}개 처리")


if __name__ == "__main__":
    main()
