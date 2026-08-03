"""ACE Express(acedp.co.kr) 송장 조회 - 로그인 없이 공개된 조회 페이지를 크롤링.

/orders 페이지의 "새로고침"이 국제배송 송장(intl_tracking_number)이 있는 주문에
대해 이 모듈로 실제 배송 이벤트를 조회해 통관/국내배송 단계를 판정한다.

조회 URL은 사이트 메인 페이지의 송장번호 검색창이 호출하는 JS 함수
Trackit()에서 확인함: GET /welcome/Track/hno/{invoice_no} (iframe으로 열리는
결과 페이지, 로그인 불필요 - 홈페이지에 "It's free!"로 안내된 공개 조회 기능).
"""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup

_TRACK_URL = "http://www.acedp.co.kr/welcome/Track/hno/{invoice_no}"

# 통관/국내배송 단계 판정 기준 (사용자 확정):
# 국제배송 시작 = "항공기 출발" 이벤트, 통관 시작 = "항공기 도착" 이벤트,
# 국내배송 시작 = "반출" 이벤트 + 비고 "KOR". 비고 코드(ICN/INC 등 공항 표기)는
# 실제 데이터에서 표기가 갈려("항공기 도착" 비고가 ICN 또는 INC로 관측됨) 이벤트
# 텍스트만으로 판정하고 비고는 참고 정보로만 취급한다.
_EVENT_INTL_SHIPPED = "항공기 출발"
_EVENT_CUSTOMS_STARTED = "항공기 도착"
_EVENT_DOMESTIC_STARTED = "반출"
_NOTE_DOMESTIC_STARTED = "KOR"


def get_tracking_events(invoice_no: str) -> list[dict] | None:
    """송장번호로 조회한 이동 이력. 조회 결과 없으면(No Data/네트워크 실패) None."""
    if not invoice_no:
        return None
    try:
        resp = requests.get(
            _TRACK_URL.format(invoice_no=invoice_no),
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"ACE Express 조회 실패 ({invoice_no}): {e}")
        return None

    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.select_one("#subcontents table")
    if table is None:
        return None

    events = []
    for tr in table.select("tbody tr"):
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cols) == 3:
            events.append({"datetime": cols[0], "event": cols[1], "note": cols[2]})
    return events


def derive_ace_stage(events: list[dict] | None) -> dict:
    """이벤트 목록에서 통관/국내배송 단계 진입 시각을 판정.

    한 번 진입한 단계는 되돌아가지 않는 사실이라 처음 발생한 이벤트의
    시각을 그대로 반환 - 호출측(orders.py)이 NocoDB에 저장해두면 다음
    새로고침부터는 이미 확정된 주문을 다시 조회하지 않아도 된다.
    """
    result = {"customs_started_at": None, "domestic_started_at": None, "delivered": False}
    if not events:
        return result
    for e in events:
        if e["event"] == _EVENT_CUSTOMS_STARTED and result["customs_started_at"] is None:
            result["customs_started_at"] = e["datetime"]
        elif (
            e["event"] == _EVENT_DOMESTIC_STARTED
            and e["note"] == _NOTE_DOMESTIC_STARTED
            and result["domestic_started_at"] is None
        ):
            result["domestic_started_at"] = e["datetime"]
        elif "배달완료" in e["event"] or "배송완료" in e["event"]:
            result["delivered"] = True
    return result
