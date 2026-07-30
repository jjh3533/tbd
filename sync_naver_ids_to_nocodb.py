"""
registered_log.json(네이버 상품등록 스크립트가 남긴 등록 결과)을 읽어서,
각 상품의 smartstoreChannelProductNo를 NocoDB의 Naver_Product_No 필드에 채워넣는다.

왜 smartstoreChannelProductNo인가:
    app.py의 _naver_url()이 만드는 스토어 링크
    (https://smartstore.naver.com/tbdseoul/products/{id}) 는
    "채널상품번호"를 쓴다. originProductNo는 원상품번호로, 스토어 URL에는 안 맞는다.

사용법:
    python sync_naver_ids_to_nocodb.py             # registered_log.json 전체 반영
    python sync_naver_ids_to_nocodb.py --dry-run    # 실제로 NocoDB에 쓰지 않고 무엇을 쓸지만 출력
"""
import argparse
import json
from pathlib import Path

import config
from nocodb_client import NocoDBTable

LOG_PATH = Path(__file__).parent / "registered_log.json"

# naver_상품등록_템플릿.xlsx의 영문상품명 -> NocoDB "SKU"(실제로는 상품명) 필드에서 찾을 검색어
# export_prices_for_naver.py와 동일한 매핑을 사용한다.
TARGET_PRODUCTS = {
    "UniFi Cloud Gateway Ultra UCG-Ultra": "Cloud Gateway Ultra",
    "UniFi U7 Pro XG": "U7 Pro XG",
    "UniFi Dream Router 7": "Dream Router 7",
    "UniFi Dream Router 5G Max": "Dream Router 5G Max",
    "UniFi U7 Lite": "U7 Lite",
    "UniFi U7 Long Range": "U7 Long-Range",
    "UniFi U7 Pro": "U7 Pro",
    "UniFi U7 Pro Max": "U7 Pro Max",
    "UniFi UCG Fiber": "Cloud Gateway Fiber",
    "UniFi UCG Max": "Cloud Gateway Max",
    "UniFi UX7": "Express 7",
    "UniFi Switch Flex 2.5G": "Flex 2.5G",
    "UniFi Switch Flex 2.5G PoE": "Flex 2.5G PoE",
    "UniFi Switch Flex mini": "Flex Mini",
    "UniFi Switch Flex mini 2.5G": "Flex Mini 2.5G",
    "UniFi Switch Lite 16 PoE": "Lite 16 PoE",
    "UniFi Switch Lite 8 PoE": "Lite 8 PoE",
    "UniFi Switch Ultra 210W": "Ultra 210W",
    "UniFi Switch Ultra 60W": "Ultra 60W",
    "UniFi Switch Enterprise 8 PoE": "Enterprise 8 PoE (Vintage)",
    "UniFi Switch Flex": "UniFi Flex",  # 짧은 "Flex"만 쓰면 "UniFi G5 Flex"와 혼동됨(find()가 순서에 따라 잘못된 레코드를 반환)
    "UniFi Flex Utility": "Flex Utility",
    "UniFi Flex Utility Pro": "Flex Utility Pro",
    "UniFi Switch Pro 8 PoE": "Pro 8 PoE",
    "UniFi Switch Pro XG 8 PoE": "Pro XG 8 PoE",
    "UniFi Switch Pro Max 16": "Pro Max 16",
    "UniFi Switch Pro Max 16 PoE": "Pro Max 16 PoE",
    "UniFi Switch Flex XG": "Flex 10 GbE",
    "UniFi Cloud Gateway Industrial UCG-Industrial": "Cloud Gateway Industrial",
    "UniFi U7 In-Wall": "U7 In-Wall",
    # WiFi 신규 16개 제품 (2026-07-29 추가)
    "UniFi AC Pro": "AC Pro",
    "UniFi Building Bridge XG": "Building Bridge XG",
    "UniFi Device Bridge": "Device Bridge",
    "UniFi Device Bridge Switch": "Device Bridge Switch",
    "UniFi E7 Campus": "E7 Campus",
    "UniFi U6 Enterprise": "U6 Enterprise",
    "UniFi U6 Enterprise In-Wall": "U6 Enterprise In-Wall",
    "UniFi U6 In-Wall": "U6 In-Wall",
    "UniFi U6 Mesh": "U6 Mesh",
    "UniFi U6 Mesh Pro": "U6 Mesh Pro",
    "UniFi U6+": "U6+",
    "UniFi U7 Outdoor": "U7 Outdoor",
    "UniFi U7 Pro Outdoor": "U7 Pro Outdoor",
    "UniFi U7 Pro Wall": "U7 Pro Wall",
    "UniFi U7 Pro XG Wall": "U7 Pro XG Wall",
    "UniFi U7 Pro XGS": "U7 Pro XGS",
    # Physical Security 신규 13개 제품 (2026-07-29 추가)
    "UniFi G6 Pro 360": "G6 Pro 360",
    "UniFi AI PTZ Industrial": "AI PTZ Industrial",
    "UniFi G5 Turret Ultra": "G5 Turret Ultra",
    "UniFi G6 Dome": "G6 Dome",
    "UniFi AI Theta": "AI Theta",
    "UniFi All-In-One Sensor": "All-In-One Sensor",
    "UniFi Glass Break Sensor": "Glass Break Sensor",
    "UniFi Motion Sensor": "Motion Sensor",
    "UniFi Network Video Recorder Instant": "Network Video Recorder Instant",
    "UniFi CloudKey+": "CloudKey+",
    "UniFi AI Horn Speaker": "AI Horn Speaker",
    "UniFi SuperLink Gateway": "SuperLink Gateway",
    "UniFi Floodlight": "Floodlight",
    # Door Access 신규 31개 제품 (2026-07-29 추가)
    "UniFi Reader Pro": "UniFi Reader Pro",
    "UniFi Reader Flex": "UniFi Reader Flex",
    "UniFi Access Ultra": "UniFi Access Ultra",
    "UniFi Door Hub": "UniFi Door Hub",
    "UniFi Door Hub Mini": "UniFi Door Hub Mini",
    "UniFi Enterprise Access Hub": "UniFi Enterprise Access Hub",
    "UniFi Intercom Viewer": "UniFi Intercom Viewer",
    "UniFi G6 Entry": "UniFi G6 Entry",
    "UniFi Magnetic Lock": "UniFi Magnetic Lock",
    "UniFi Access Button": "UniFi Access Button",
    "UniFi Reader Junction Box": "UniFi Reader Junction Box",
    "UniFi Reader Pro Junction Box": "UniFi Reader Pro Junction Box",
    "UniFi Reader Pro Angle Mount": "UniFi Reader Pro Angle Mount",
    "UniFi Intercom Viewer Table Stand": "UniFi Intercom Viewer Table Stand",
    "UniFi Intercom Flush Mount": "UniFi Intercom Flush Mount",
    "UniFi Intercom Surface Angle Mount": "UniFi Intercom Surface Angle Mount",
    "UniFi Intercom Wedge Mount": "UniFi Intercom Wedge Mount",
    "UniFi Intercom Sunshield": "UniFi Intercom Sunshield",
    "UniFi Gate Hub": "UniFi Gate Hub",
    "UniFi Junction Utility": "UniFi Junction Utility",
    "UniFi Door Lock Relay Cable": "UniFi Door Lock Relay Cable",
    "UniFi Door Closer": "UniFi Door Closer",
    "UniFi PoE Over 2-Wire Retrofit Extender": "UniFi PoE Over 2-Wire Retrofit Extender",
    "UniFi Retrofit Hub": "UniFi Retrofit Hub",
    "UniFi Retrofit PSU 12V": "UniFi Retrofit PSU 12V",
    "UniFi Panic Bar": "UniFi Panic Bar",
    "UniFi Access Rescue KeySwitch": "UniFi Access Rescue KeySwitch",
    "UniFi Access Card (10-Pack)": "UniFi Access Card (10-Pack)",
    "UniFi Pocket Keyfob, 10-Pack": "UniFi Pocket Keyfob, 10-Pack",
    "UniFi Gate Starter Kit": "UniFi Gate Starter Kit",
    "UniFi G3 Elevator Starter Kit": "UniFi G3 Elevator Starter Kit",
    # Integrations 신규 6개 제품 (2026-07-29 추가)
    "U5G-Max": "UniFi 5G Max",
    "U-LTE-Backup Pro": "UniFi LTE Backup Pro",
    "UMR": "UniFi Mobile Router",
    "UMR-Ultra": "UniFi Mobile Router Ultra",
    "UPL-Port": "UniFi PoE Audio Port",
    "UNAS-2": "UniFi UNAS 2",
}


def normalize(s: str) -> str:
    return (s or "").lower().replace("-", " ").replace("_", " ").strip()


def build_finder(records):
    norm_index = {}
    for r in records:
        name = r["fields"].get("SKU") or ""
        norm_index[normalize(name)] = r  # 레코드 전체(= id 포함) 보관

    def find(search_key: str):
        nk = normalize(search_key)
        for full_norm, rec in norm_index.items():
            if full_norm == nk or full_norm.endswith(" " + nk) or full_norm == "unifi " + nk:
                return rec
        candidates = [rec for full_norm, rec in norm_index.items() if nk in full_norm]
        if len(candidates) == 1:
            return candidates[0]
        return None

    return find


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not LOG_PATH.exists():
        print(f"{LOG_PATH} 가 없습니다. main.py로 먼저 상품을 등록하세요.")
        return

    with open(LOG_PATH, encoding="utf-8") as f:
        log = json.load(f)

    if not log:
        print("registered_log.json 이 비어있습니다. 등록된 상품이 없습니다.")
        return

    table = NocoDBTable(config.NOCODB_URL, config.NOCODB_API_TOKEN, config.NOCODB_TABLE_ID)
    records = table.all()
    find = build_finder(records)

    updated, skipped = 0, 0
    for product_name, result in log.items():
        channel_no = result.get("smartstoreChannelProductNo")
        if not channel_no:
            print(f"[건너뜀] '{product_name}' - smartstoreChannelProductNo 없음")
            skipped += 1
            continue

        search_key = TARGET_PRODUCTS.get(product_name)
        if not search_key:
            print(f"[건너뜀] '{product_name}' - TARGET_PRODUCTS에 매핑이 없음 (스크립트에 추가 필요)")
            skipped += 1
            continue

        rec = find(search_key)
        if not rec:
            print(f"[건너뜀] '{product_name}' - NocoDB에서 '{search_key}' 매칭 실패")
            skipped += 1
            continue

        nocodb_name = rec["fields"].get("SKU")
        if args.dry_run:
            print(f"[dry-run] '{nocodb_name}' (id={rec['id']})  Naver_Product_No <- {channel_no}")
        else:
            table.update(rec["id"], {"Naver_Product_No": str(channel_no)})
            print(f"[완료] '{nocodb_name}' (id={rec['id']})  Naver_Product_No = {channel_no}")
        updated += 1

    print(f"\n총 {updated}개 반영, {skipped}개 건너뜀")


if __name__ == "__main__":
    main()
