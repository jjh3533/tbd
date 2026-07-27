"""
네이버 커머스API OAuth2 인증 토큰 발급.

커머스API는 일반적인 client_secret 대신, client_id + timestamp를
client_secret을 salt로 bcrypt 해싱한 "전자서명(client_secret_sign)"을 사용한다.
"""
import base64
import time

import bcrypt
import requests

TOKEN_URL = "https://api.commerce.naver.com/external/v1/oauth2/token"


def _make_signature(client_id: str, client_secret: str, timestamp_ms: str) -> str:
    password = f"{client_id}_{timestamp_ms}"
    hashed = bcrypt.hashpw(password.encode("utf-8"), client_secret.encode("utf-8"))
    return base64.standard_b64encode(hashed).decode("utf-8")


def get_bearer_token(client_id: str, client_secret: str, account_type: str = "SELF") -> str:
    """
    account_type:
      - "SELF": 판매자 본인이 자기 스토어를 관리할 때 (일반적인 경우, 기본값)
      - "SELLER": 대행사가 특정 판매자 계정을 대신 관리할 때 (account_id 파라미터 필요, 커머스API센터 문의 필요)
    """
    # API 문서 권장대로 3초 전 timestamp 사용 (서버 시간 오차 대비)
    timestamp = str(int((time.time() - 3) * 1000))
    signature = _make_signature(client_id, client_secret, timestamp)

    data = {
        "client_id": client_id,
        "timestamp": timestamp,
        "client_secret_sign": signature,
        "grant_type": "client_credentials",
        "type": account_type,
    }
    headers = {"content-type": "application/x-www-form-urlencoded"}

    resp = requests.post(TOKEN_URL, data=data, headers=headers, timeout=15)
    body = resp.json()

    if "access_token" not in body:
        raise RuntimeError(f"토큰 발급 실패: {resp.status_code} {body}")

    return body["access_token"]


def auth_headers(client_id: str, client_secret: str) -> dict:
    token = get_bearer_token(client_id, client_secret)
    return {"Authorization": f"Bearer {token}"}
