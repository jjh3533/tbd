"""네이버 Pay-Order/Claims API 클라이언트.

주문 조회, 클레임 조회, 발송 처리 등 주문 관리 기능을 제공한다.
기존 auth.py의 get_bearer_token()을 재사용해 인증한다.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Optional

import pytz
import requests

from auth import get_bearer_token
from naver_config import CLIENT_ID, CLIENT_SECRET

BASE_URL = "https://api.commerce.naver.com"

_KST = pytz.timezone("Asia/Seoul")


def _get_headers() -> dict:
    """인증 헤더 생성.

    NAS 등 네이버 시크릿이 없는 환경에서 이 모듈의 함수를 호출하면
    get_bearer_token()이 CLIENT_SECRET=None으로 bcrypt 해싱을 시도하다가
    "'NoneType' object has no attribute 'encode'"라는 알아보기 힘든 에러를
    내고 있었다 - 이 함수(모든 호출의 공통 진입점)에서 미리 체크해 명확한
    메시지로 바꾼다."""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError(
            "네이버 커머스 API 시크릿이 설정되지 않았습니다 - 이 기능은 로컬 환경에서만 사용 가능합니다."
        )
    token = get_bearer_token(CLIENT_ID, CLIENT_SECRET)
    return {"Authorization": f"Bearer {token}"}


def _to_kst(dt: datetime) -> datetime:
    """KST aware datetime으로 정규화.

    naive datetime(tzinfo 없음)은 이미 KST 벽시계 값이라고 보고 그대로
    KST로 로컬라이즈합니다(기본값 계산에 쓰는 datetime.now()가 이 경우).
    aware datetime은 실제 시각을 유지한 채 KST로 변환합니다. 예전엔 이
    구분 없이 문자열 끝에 무조건 "+09:00"을 붙여서, aware UTC datetime이
    전달되면 실제 조회 시간이 9시간 어긋날 수 있었습니다."""
    if dt.tzinfo is None:
        return _KST.localize(dt)
    return dt.astimezone(_KST)


def _flatten_order(entry: dict) -> dict:
  """API가 돌려주는 중첩 구조({"productOrderId": ..., "content": {"order": {...},
  "productOrder": {...}}})를 dashboard/pages/orders.py가 기대하는 평평한 필드
  (productOrderId/orderDate/productName/quantity/totalPaymentAmount/ordererName/
  orderStatus)로 펼친다."""
  content = entry.get("content") or {}
  order = content.get("order") or {}
  product_order = content.get("productOrder") or {}
  return {
      "productOrderId": entry.get("productOrderId") or product_order.get("productOrderId", ""),
      "orderDate": order.get("orderDate", ""),
      "productName": product_order.get("productName", ""),
      "quantity": product_order.get("quantity", 0),
      "totalPaymentAmount": product_order.get("totalPaymentAmount", 0),
      "ordererName": order.get("ordererName", ""),
      "orderStatus": product_order.get("productOrderStatus", ""),
  }


def get_product_orders(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    order_type: str = "PAY_DATE",
) -> dict:
    """주문 목록 조회.

    네이버 API는 최대 24시간 범위만 허용함.

    Args:
        from_date: 조회 시작일시 (기본값: 오늘 00:00)
        to_date: 조회 종료일시 (기본값: 오늘 23:59)
        order_type: 변경 유형 (PAY_DATE, ORDER_DATE, DISPATCH_DATE 등)

    Returns:
        dict: {"content": [...]} 형식 - 실제 API 응답은
        {"data": {"contents": [{"productOrderId": ..., "content": {"order": {...},
        "productOrder": {...}}}]}} 처럼 중첩·래핑되어 있어(문서와 다름 - 실제
        주문으로 검증하기 전까진 몰랐음, 이 때문에 항상 0건으로 조회되고 있었음),
        여기서 언래핑 + 평탄화해서 돌려준다.
    """
    if from_date is None:
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if to_date is None:
        to_date = from_date + timedelta(hours=23, minutes=59, seconds=59)

    from_date = _to_kst(from_date)
    to_date = _to_kst(to_date)

    # 24시간 제한 검증
    if (to_date - from_date).total_seconds() > 24 * 3600:
        raise ValueError("from_date와 to_date는 최대 24시간 차이만 허용됩니다.")

    params = {
        "from": from_date.strftime("%Y-%m-%dT%H:%M:%S.000+09:00"),
        "to": to_date.strftime("%Y-%m-%dT%H:%M:%S.999+09:00"),
        "type": order_type,
    }

    # /orders 페이지가 자유 날짜범위를 day_window 단위로 여러 번 순차 호출하면서
    # 실제로 429 Too Many Requests가 간헐적으로 관측됨(30일 범위 연속 조회 테스트
    # 중 재현) - 지수 백오프로 재시도한다.
    max_attempts = 5
    for attempt in range(max_attempts):
        resp = requests.get(
            f"{BASE_URL}/external/v1/pay-order/seller/product-orders",
            headers=_get_headers(),
            params=params,
            timeout=30,
        )
        if resp.status_code == 429 and attempt < max_attempts - 1:
            time.sleep(2**attempt)
            continue
        resp.raise_for_status()
        break
    payload = resp.json()
    contents = ((payload.get("data") or {}).get("contents")) or []
    return {"content": [_flatten_order(e) for e in contents]}


def get_product_order_detail(product_order_id: str) -> dict:
    """주문 상세 조회 (원본 응답 그대로).

    처음엔 GET .../product-orders/{id} 경로를 썼으나 실제로는 404만 났다 -
    올바른 엔드포인트는 POST .../product-orders/query에 productOrderIds
    배열을 넘기는 방식(실제 주문으로 확인함). 배송지 정보는
    data[0].productOrder.shippingAddress에 들어있다.

    Args:
        product_order_id: 상품 주문 번호

    Returns:
        dict: 주문 상세 정보 (data[0] = {"order": {...}, "productOrder": {...}, "delivery": {...}})
    """
    resp = requests.post(
        f"{BASE_URL}/external/v1/pay-order/seller/product-orders/query",
        headers=_get_headers(),
        json={"productOrderIds": [product_order_id]},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json().get("data") or []
    return data[0] if data else {}


def get_recipient_info(product_order_id: str) -> dict:
    """배송대행지 신청서(에코트랜스 xlsx)에 채울 수령인 정보를 조회.

    네이버 Pay-Order API 응답을 직접 확인한 결과, 우편번호/주소/연락처/
    수령인명은 productOrder.shippingAddress에 구조화된 필드로 들어있지만
    **개인통관고유부호는 이 API 어디에도 없다**(order/productOrder 키를
    전부 확인함 - 없음). 사용자 확인: 네이버 스마트스토어센터의 "해외" 상품
    항목이 아직 활성화되지 않아서 그렇다 - 활성화되면 개인통관고유부호를
    수집하는 필드가 주문에 생길 것으로 예상됨(그때 이 함수에 파싱 추가
    필요). 그 전까지 personal_customs_code는 항상 빈 문자열로 돌려준다 -
    수동 입력이 필요하다.

    Returns:
        dict: {recipient_name_kr, recipient_phone, recipient_postal_code,
        recipient_address, personal_customs_code(항상 "")}. 조회 실패 시 전부 빈 값.
    """
    try:
        detail = get_product_order_detail(product_order_id)
        addr = (detail.get("productOrder") or {}).get("shippingAddress") or {}
    except Exception:
        addr = {}

    base = addr.get("baseAddress", "")
    detailed = addr.get("detailedAddress", "")
    full_address = f"{base} {detailed}".strip()

    return {
        "recipient_name_kr": addr.get("name", ""),
        "recipient_phone": addr.get("tel1", ""),
        "recipient_postal_code": addr.get("zipCode", ""),
        "recipient_address": full_address,
        "personal_customs_code": "",
    }


def dispatch_product_order(
    product_order_id: str,
    dispatch_date: str,
    delivery_company: str,
    tracking_number: str,
) -> dict:
    """배송 준비 (발송 처리).

    Args:
        product_order_id: 상품 주문 번호
        dispatch_date: 발송일 (YYYY-MM-DD)
        delivery_company: 택배사 코드 (예: "CJGLS", "EPOST")
        tracking_number: 송장번호

    Returns:
        dict: 처리 결과
    """
    payload = {
        "productOrderId": product_order_id,
        "dispatchDate": dispatch_date,
        "deliveryCompany": delivery_company,
        "trackingNumber": tracking_number,
    }

    resp = requests.post(
        f"{BASE_URL}/external/v1/pay-order/seller/product-orders/dispatch",
        headers=_get_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def get_product_order_claims(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> dict:
    """클레임 목록 조회.

    Args:
        from_date: 조회 시작일시 (기본값: 오늘 00:00)
        to_date: 조회 종료일시 (기본값: 오늘 23:59)

    Returns:
        dict: 클레임 목록
    """
    if from_date is None:
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if to_date is None:
        to_date = from_date + timedelta(hours=23, minutes=59, seconds=59)

    from_date = _to_kst(from_date)
    to_date = _to_kst(to_date)

    # 24시간 제한 검증 (get_product_orders와 동일 - 예전엔 클레임 조회에만 빠져있었음)
    if (to_date - from_date).total_seconds() > 24 * 3600:
        raise ValueError("from_date와 to_date는 최대 24시간 차이만 허용됩니다.")

    params = {
        "from": from_date.strftime("%Y-%m-%dT%H:%M:%S.000+09:00"),
        "to": to_date.strftime("%Y-%m-%dT%H:%M:%S.999+09:00"),
    }

    resp = requests.get(
        f"{BASE_URL}/external/v1/pay-order/seller/product-order-claims",
        headers=_get_headers(),
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def approve_claim(claim_no: str, memo: str = "") -> dict:
    """클레임 승인.

    Args:
        claim_no: 클레임 번호
        memo: 승인 메모 (선택)

    Returns:
        dict: 처리 결과
    """
    payload = {"claimNo": claim_no}
    if memo:
        payload["memo"] = memo

    resp = requests.post(
        f"{BASE_URL}/external/v1/pay-order/seller/product-order-claims/{claim_no}/approve",
        headers=_get_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def reject_claim(claim_no: str, reason: str) -> dict:
    """클레임 거부.

    Args:
        claim_no: 클레임 번호
        reason: 거부 사유 (필수)

    Returns:
        dict: 처리 결과
    """
    if not reason or not reason.strip():
        raise ValueError("거부 사유는 필수입니다.")

    payload = {"claimNo": claim_no, "reason": reason}

    resp = requests.post(
        f"{BASE_URL}/external/v1/pay-order/seller/product-order-claims/{claim_no}/reject",
        headers=_get_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
