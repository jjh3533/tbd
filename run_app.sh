#!/bin/bash
# 새 터미널을 열 때마다 이 스크립트 하나만 실행하면 됩니다:
#   ./run_app.sh
#
# cd + venv activate + streamlit run을 한 번에 처리합니다.
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "venv가 없습니다. 먼저 만들어주세요: python3 -m venv venv && ./run_app.sh"
  exit 1
fi

source venv/bin/activate
python3 -m streamlit run app.py
