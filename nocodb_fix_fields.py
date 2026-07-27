#!/usr/bin/env python3
"""NocoDB Products 테이블: Shopping_KRW -> Shipping_KRW 오타 수정 + 나머지 수식 필드 생성.

사용법 (본인 Mac 터미널에서):
    NOCODB_URL="https://nocodb.jayjeon.net" NOCODB_TOKEN="토큰" python3 nocodb_fix_fields.py

재실행해도 안전합니다 (이미 존재하는 필드는 건너뜁니다).
"""
import json
import os
import sys
import urllib.request
import urllib.error

NOCODB_URL = os.environ.get("NOCODB_URL", "").rstrip("/")
NOCODB_TOKEN = os.environ.get("NOCODB_TOKEN", "")
BASE_ID = "pqlruah70l8clo1"
TABLE_ID = "mo6797mk38fuelu"

if not NOCODB_URL or not NOCODB_TOKEN:
    print("NOCODB_URL / NOCODB_TOKEN 환경변수를 설정해주세요.")
    sys.exit(1)

HEADERS = {"xc-token": NOCODB_TOKEN, "Content-Type": "application/json"}


def request(method, path, body=None):
    url = f"{NOCODB_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} 에러 ({method} {path}):")
        print(e.read().decode("utf-8"))
        sys.exit(1)


def get_columns():
    detail = request("GET", f"/api/v2/meta/tables/{TABLE_ID}")
    return detail["columns"]


def find_column(columns, title):
    return next((c for c in columns if c["title"] == title), None)


def rename_column(col_id, new_title):
    request("PATCH", f"/api/v2/meta/columns/{col_id}", {"title": new_title})
    print(f"  -> '{new_title}' 로 이름 변경 완료")


def create_formula(title, formula_raw):
    request("POST", f"/api/v2/meta/tables/{TABLE_ID}/columns", {
        "title": title,
        "uidt": "Formula",
        "formula_raw": formula_raw,
    })
    print(f"  -> '{title}' 필드 생성 완료")


def main():
    columns = get_columns()

    print("=== 1. 체크박스 필드 확인 ===")
    expected_checkboxes = ["In_Stock", "Needs_Check", "Adorama_In_Stock", "Amazon_In_Stock", "BH_In_Stock"]
    for name in expected_checkboxes:
        col = find_column(columns, name)
        status = "OK" if col and col["uidt"] == "Checkbox" else "누락/타입 이상"
        print(f"  {name}: {status}")

    print("\n=== 2. Shopping_KRW -> Shipping_KRW 오타 수정 ===")
    typo_col = find_column(columns, "Shopping_KRW")
    correct_col = find_column(columns, "Shipping_KRW")
    if correct_col:
        print("  이미 Shipping_KRW 존재함, 건너뜀")
    elif typo_col:
        print(f"  기존 수식: {typo_col.get('colOptions', {}).get('formula_raw')}")
        rename_column(typo_col["id"], "Shipping_KRW")
    else:
        print("  Shopping_KRW/Shipping_KRW 필드가 없음 -> 새로 생성")
        create_formula("Shipping_KRW", (
            "IF({Weight_KG} > 0, "
            "IF({Weight_KG} <= 1.5, 10800 + (({Weight_KG} - 0.5) * 4500), "
            "15300 + (({Weight_KG} - 1.5) * 5400)), 10800)"
        ))

    columns = get_columns()

    print("\n=== 3. Best_USD 생성 ===")
    if find_column(columns, "Best_USD"):
        print("  이미 존재함, 건너뜀")
    else:
        create_formula("Best_USD", (
            "IF(MIN("
            "IF(AND({Adorama_USD} > 0, {Adorama_In_Stock}), {Adorama_USD}, 999999), "
            "IF(AND({Amazon_USD} > 0, {Amazon_In_Stock}), {Amazon_USD}, 999999), "
            "IF(AND({BH_USD} > 0, {BH_In_Stock}), {BH_USD}, 999999)"
            ") == 999999, 0, MIN("
            "IF(AND({Adorama_USD} > 0, {Adorama_In_Stock}), {Adorama_USD}, 999999), "
            "IF(AND({Amazon_USD} > 0, {Amazon_In_Stock}), {Amazon_USD}, 999999), "
            "IF(AND({BH_USD} > 0, {BH_In_Stock}), {BH_USD}, 999999)"
            "))"
        ))

    columns = get_columns()

    print("\n=== 4. 판매금액 생성 ===")
    if find_column(columns, "판매금액"):
        print("  이미 존재함, 건너뜀")
    else:
        create_formula("판매금액", (
            "ROUNDUP(("
            "({MSRP_USD} * 1.0158 * {Exchange_Rate}) "
            "+ IF({MSRP_USD} > 200, ({MSRP_USD} * 1.0158 * {Exchange_Rate}) * 0.188, 0) "
            "+ (({MSRP_USD} * 1.0158 * {Exchange_Rate}) * 0.057) "
            "+ {Shipping_KRW}) * 1.10, -2)"
        ))

    columns = get_columns()

    print("\n=== 5. 최종가격 생성 ===")
    if find_column(columns, "최종가격"):
        print("  이미 존재함, 건너뜀")
    else:
        create_formula("최종가격", (
            "IF({In_Stock}, ROUNDUP("
            "({Best_USD} * 1.0158 * {Exchange_Rate}) "
            "+ IF({Best_USD} > 200, ({Best_USD} * 1.0158 * {Exchange_Rate}) * 0.188, 0) "
            "+ (({Best_USD} * 1.0158 * {Exchange_Rate}) * 0.057) "
            "+ {Shipping_KRW}, -2), 0)"
        ))

    columns = get_columns()

    print("\n=== 6. 수익 생성 ===")
    if find_column(columns, "수익"):
        print("  이미 존재함, 건너뜀")
    else:
        create_formula("수익", "IF({In_Stock}, {판매금액} - {최종가격}, 0)")

    print("\n완료! NocoDB에서 새로고침해서 확인해보세요.")


if __name__ == "__main__":
    main()
