#!/usr/bin/env python3
"""화이트(White)를 기본으로 등록되어 있는 상품 중 실제로 블랙(Black) 옵션이
있는 제품들에 대해, NocoDB에 블랙 전용 로우를 새로 생성한다.

배경: 네이버 스마트스토어에는 "색상"(화이트/블랙) 옵션 하나로 등록돼 있지만,
구매처(Adorama/Amazon/B&H)에서는 화이트와 블랙이 별도 리스팅이고 가격도 종종
다르다. 지금까지는 NocoDB에 화이트 기준 1개 로우만 있어서 옵션별 가격/재고를
따로 추적할 방법이 없었다 - 이 스크립트는 그 블랙 쪽 추적용 로우를 만든다.

생성 규칙 (화이트 로우에서 그대로 복사):
    SKU            = "{화이트 SKU} Black"
    Model Number   = "{화이트 Model Number}-B"
    Category       = 화이트와 동일
    Weight_KG      = 화이트와 동일
    MSRP_USD       = 화이트와 동일
    Naver_Product_No = 화이트와 동일 (같은 네이버 상품의 옵션이므로 channelProductNo 공유)
    ADORAMA_ID/ASIN/BH_ID = 비워둠 (사용자가 직접 조사해서 채워 넣을 예정)
    In_Stock       = False (다음 Sync 전까지는 알 수 없음)

이미 "{화이트 SKU} Black" 로우가 있으면 건너뛴다 (재실행 안전).

사용법:
    python3 create_color_variant_rows.py --dry-run   # 무엇이 만들어질지만 확인
    python3 create_color_variant_rows.py --limit 1   # 1개만 실제 생성
    python3 create_color_variant_rows.py             # 전체 생성
"""
import argparse

import sync_engine as se

# 화이트 기준 SKU 목록 (NocoDB에 존재하는 것만 - 3개는 화이트 자체가 없어 제외:
# UniFi Reader / UniFi G3 Reader Fingerprint / UniFi Retrofit Reader Fingerprint)
WHITE_SKUS = [
    "UniFi AI 360",
    "UniFi AI Dome",
    "UniFi AI Horn Speaker",
    "UniFi AI Multi Sensor 4",
    "UniFi AI PTZ Industrial",
    "UniFi AI PTZ Precision",
    "UniFi AI Pro",
    "UniFi AI Turret",
    "UniFi Access Button",
    "UniFi Doorbells",
    "UniFi G2 Touch",
    "UniFi G2 Touch Max",
    "UniFi G5 Dome Ultra",
    "UniFi G5 PTZ",
    "UniFi G5 Turret Ultra",
    "UniFi G6 180",
    "UniFi G6 Dome",
    "UniFi G6 Mini Dome",
    "UniFi G6 PTZ",
    "UniFi G6 Pro 360",
    "UniFi G6 Pro Bullet",
    "UniFi G6 Pro Dome",
    "UniFi G6 Pro Turret",
    "UniFi G6 Turret",
    "UniFi PoE Audio Port",
    "UniFi PowerAmp",
    "UniFi Reader Flex",
    "UniFi Reader Junction Box",
    "UniFi Reader Pro",
    "UniFi Reader Pro Angle Mount",
    "UniFi Reader Pro Junction Box",
    "UniFi U7 Pro XG",
    "UniFi U7 Pro XGS",
    "UniFi UNAS 2",
    "UniFi UNAS 4",
]


def black_fields_for(white_fields: dict) -> dict:
    white_sku = white_fields["SKU"]
    white_model = white_fields.get("Model Number") or ""
    return {
        "SKU": f"{white_sku} Black",
        "Model Number": f"{white_model}-B",
        "Category": white_fields.get("Category"),
        "Weight_KG": white_fields.get("Weight_KG"),
        "MSRP_USD": white_fields.get("MSRP_USD"),
        "Naver_Product_No": white_fields.get("Naver_Product_No"),
        "In_Stock": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    records = se.table.all()
    by_sku = {r["fields"].get("SKU", "").strip(): r for r in records}

    created = 0
    skipped = 0
    for white_sku in WHITE_SKUS:
        if args.limit is not None and created >= args.limit:
            break

        white_rec = by_sku.get(white_sku)
        if not white_rec:
            print(f"[건너뜀] '{white_sku}' - NocoDB에서 화이트 로우를 찾을 수 없음")
            skipped += 1
            continue

        black_sku = f"{white_sku} Black"
        if black_sku in by_sku:
            print(f"[건너뜀] '{black_sku}' - 이미 존재함")
            skipped += 1
            continue

        fields = black_fields_for(white_rec["fields"])
        print(f"[생성] {black_sku!r} <- Model={fields['Model Number']!r} "
              f"Category={fields['Category']!r} Weight_KG={fields['Weight_KG']} "
              f"MSRP_USD={fields['MSRP_USD']} Naver_Product_No={fields['Naver_Product_No']}")

        if not args.dry_run:
            se.table.create(fields)

        created += 1

    print(f"\n{'(dry-run) ' if args.dry_run else ''}생성 {created}건 / 건너뜀 {skipped}건")


if __name__ == "__main__":
    main()
