"""
공용 설정 로더.

시크릿 값은 절대 이 파일에 하드코딩하지 않습니다.
우선순위: OS 환경변수 > .env 파일(로컬 개발용)

- 로컬 개발: 이 파일과 같은 폴더에 `.env` 파일을 만들고 .env.example을 참고해
  실제 값을 채워 넣으세요. `.env`는 .gitignore에 의해 git에 커밋되지 않습니다.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

# 로컬 개발 시 .env 파일이 있으면 로드. 운영 환경(Streamlit Cloud, GitHub
# Actions)에서는 .env 파일이 없으므로 아무 동작도 하지 않습니다.
load_dotenv()


def _get_secret(name: str, required: bool = True, default: str | None = None) -> str | None:
  """환경변수 -> default 순으로 값을 조회합니다."""
  value = os.environ.get(name, default)

  if required and not value:
    raise RuntimeError(
        f"필수 환경변수 '{name}'가 설정되지 않았습니다.\n"
        "- 로컬: .env 파일에 값을 채워주세요 (.env.example 참고)"
    )
  return value


NOCODB_URL = _get_secret("NOCODB_URL")
NOCODB_API_TOKEN = _get_secret("NOCODB_API_TOKEN")
NOCODB_TABLE_ID = _get_secret("NOCODB_TABLE_ID")
NOCODB_HISTORY_TABLE_ID = _get_secret("NOCODB_HISTORY_TABLE_ID", required=False)

SCRAPEDO_TOKEN = _get_secret("SCRAPEDO_TOKEN")

TELEGRAM_TOKEN = _get_secret("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = _get_secret("TELEGRAM_CHAT_ID")
