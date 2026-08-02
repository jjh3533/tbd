"""대시보드 접근 제어.

URL만 알면 누구나 /register(실제 네이버 API 실행)나 /orders(고객 주문정보)에
접근할 수 있었던 문제를 막기 위한 단일 비밀번호 로그인. `app.storage.user`
세션(브라우저 쿠키, `storage_secret`으로 서명됨)에 인증 여부를 저장하고,
미들웨어가 /login과 정적 자원을 제외한 모든 요청을 이 상태로 게이팅한다.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import RedirectResponse

from nicegui import app

from config import _get_secret

DASHBOARD_PASSWORD = _get_secret("DASHBOARD_PASSWORD")
DASHBOARD_STORAGE_SECRET = _get_secret("DASHBOARD_STORAGE_SECRET")

# 로그인 없이 접근 가능해야 하는 경로 (로그인 페이지 자체, NiceGUI 내부 자원).
_UNRESTRICTED_PREFIXES = ("/login", "/_nicegui")


class AuthMiddleware(BaseHTTPMiddleware):
  """미인증 요청을 /login으로 리다이렉트한다."""

  async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
    if request.url.path.startswith(_UNRESTRICTED_PREFIXES):
      return await call_next(request)

    if not app.storage.user.get("authenticated", False):
      redirect_to = request.url.path
      if request.url.query:
        redirect_to += f"?{request.url.query}"
      return RedirectResponse(f"/login?redirect_to={redirect_to}")

    return await call_next(request)
