"""
공용 설정 로더.

시크릿 값은 절대 이 파일에 하드코딩하지 않습니다.
우선순위: Streamlit Secrets (st.secrets) > OS 환경변수 > .env 파일(로컬 개발용)

- 로컬 개발: 이 파일과 같은 폴더에 `.env` 파일을 만들고 .env.example을 참고해
  실제 값을 채워 넣으세요. `.env`는 .gitignore에 의해 git에 커밋되지 않습니다.
- Streamlit Community Cloud 배포: 앱 Settings > Secrets 에 TOML 형식으로
  아래와 동일한 키 이름으로 값을 등록하세요.
- GitHub Actions로 스케줄 실행하는 경우: 레포 Settings >
  Secrets and variables > Actions 에 등록하고 workflow yml의 `env:`에서
  `${{ secrets.NOCODB_API_TOKEN }}` 형태로 주입하세요.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

# 로컬 개발 시 .env 파일이 있으면 로드. 운영 환경(Streamlit Cloud, GitHub
# Actions)에서는 .env 파일이 없으므로 아무 동작도 하지 않습니다.
load_dotenv()


def _get_secret(name: str, required: bool = True, default: str | None = None) -> str | None:
  """st.secrets -> 환경변수 -> default 순으로 값을 조회합니다."""
  # Streamlit 컨텍스트에서 실행 중이면 st.secrets를 우선 확인합니다.
  # (tbd_tracker.py처럼 Streamlit 없이 실행되는 스크립트에서도 에러 없이
  # 넘어가도록 import 실패를 흡수합니다.)
  try:
    import streamlit as st

    if hasattr(st, "secrets") and name in st.secrets:
      return st.secrets[name]
  except Exception:
    pass

  value = os.environ.get(name, default)

  if required and not value:
    raise RuntimeError(
        f"필수 환경변수 '{name}'가 설정되지 않았습니다.\n"
        "- 로컬: .env 파일에 값을 채워주세요 (.env.example 참고)\n"
        "- Streamlit Cloud: Settings > Secrets 에 등록하세요\n"
        "- GitHub Actions: Settings > Secrets and variables > Actions 에 등록하세요"
    )
  return value


NOCODB_URL = _get_secret("NOCODB_URL")
NOCODB_API_TOKEN = _get_secret("NOCODB_API_TOKEN")
NOCODB_TABLE_ID = _get_secret("NOCODB_TABLE_ID")

SCRAPEDO_TOKEN = _get_secret("SCRAPEDO_TOKEN")

TELEGRAM_TOKEN = _get_secret("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = _get_secret("TELEGRAM_CHAT_ID")
