"""네이버 Pay-Order/Claims API 클라이언트.

주문 조회, 클레임 조회, 발송 처리 등 주문 관리 기능을 제공한다.
기존 auth.py의 get_bearer_token()을 재사용해 인증한다.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pytz
import requests

from auth import get_bearer_token
from naver_config import CLIENT_ID, CLIENT_SECRET

BASE_URL = "https://api.commerce.naver.com"

_KST = pytz.timezone("Asia/Seoul")


def _get_headers() -> dict:
    """인증 헤더 생성."""
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

    resp = requests.get(
        f"{BASE_URL}/external/v1/pay-order/seller/product-orders",
        headers=_get_headers(),
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    contents = ((payload.get("data") or {}).get("contents")) or []
    return {"content": [_flatten_order(e) for e in contents]}


def get_product_order_detail(product_order_id: str) -> dict:
    """주문 상세 조회.

    Args:
        product_order_id: 상품 주문 번호

    Returns:
        dict: 주문 상세 정보
    """
    resp = requests.get(
        f"{BASE_URL}/external/v1/pay-order/seller/product-orders/{product_order_id}",
        headers=_get_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


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


# 택배사 코드 매핑 (주요 업체만)
DELIVERY_COMPANIES = {
    "CJ대한통운": "CJGLS",
    "우체국택배": "EPOST",
    "로젠택배": "LOGEN",
    "한진택배": "HANJIN",
    "롯데택배": "LOTTE",
    "경동택배": "KDEXP",
    "대신택배": "DAESIN",
    "일양로지스": "ILYANG",
    "합동택배": "HDEXP",
    "CVSnet": "CVSNET",
}
