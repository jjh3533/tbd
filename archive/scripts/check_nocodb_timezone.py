"""NocoDB 서버 시간대 확인 스크립트."""

from datetime import datetime
import pytz
from config import NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID
from nocodb_client import NocoDBTable

def check_timezone():
    """NocoDB 서버의 타임스탬프를 확인하여 시간대를 추론합니다."""

    table = NocoDBTable(NOCODB_URL, NOCODB_API_TOKEN, NOCODB_TABLE_ID)

    print(f"NocoDB URL: {NOCODB_URL}")
    print(f"Table ID: {NOCODB_TABLE_ID}")
    print("-" * 60)

    # 레코드 1개만 가져오기
    records = table.all()

    if not records:
        print("레코드가 없습니다.")
        return

    # 첫 번째 레코드의 원본 데이터 확인 (메타 필드 포함)
    import requests
    session = requests.Session()
    session.headers.update({
        "xc-token": NOCODB_API_TOKEN,
        "Content-Type": "application/json",
    })

    url = f"{NOCODB_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records"
    resp = session.get(url, params={"limit": 1}, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("list"):
        print("레코드가 없습니다.")
        return

    record = data["list"][0]

    print("\n첫 번째 레코드의 타임스탬프 필드:")
    print("-" * 60)

    timestamp_fields = ["CreatedAt", "UpdatedAt", "created_at", "updated_at"]

    for field in timestamp_fields:
        if field in record:
            value = record[field]
            print(f"\n{field}: {value}")

            # ISO 8601 형식 파싱 시도
            try:
                if isinstance(value, str):
                    # 여러 형식 시도
                    for fmt in [
                        "%Y-%m-%dT%H:%M:%S.%fZ",
                        "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%dT%H:%M:%S%z",
                        "%Y-%m-%dT%H:%M:%S.%f%z",
                    ]:
                        try:
                            dt = datetime.strptime(value, fmt)
                            print(f"  파싱 성공 (형식: {fmt})")
                            if dt.tzinfo:
                                print(f"  시간대: {dt.tzinfo}")
                            else:
                                print(f"  시간대 정보 없음 (naive datetime)")
                            break
                        except ValueError:
                            continue
            except Exception as e:
                print(f"  파싱 실패: {e}")

    # 현재 로컬 시간과 비교
    print("\n" + "=" * 60)
    print("참고: 현재 시간 정보")
    print("-" * 60)
    now_local = datetime.now()
    now_utc = datetime.now(pytz.UTC)
    now_seoul = datetime.now(pytz.timezone('Asia/Seoul'))

    print(f"로컬 시간: {now_local.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"UTC 시간: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"서울 시간: {now_seoul.strftime('%Y-%m-%d %H:%M:%S %Z')}")

if __name__ == "__main__":
    check_timezone()
