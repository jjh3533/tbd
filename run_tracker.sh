#!/bin/bash
# UI 없이 tbd_tracker.py만 한 번 돌리고 싶을 때:
#   ./run_tracker.sh
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "venv가 없습니다. 먼저 만들어주세요: python3 -m venv venv && ./run_tracker.sh"
  exit 1
fi

source venv/bin/activate
python3 tbd_tracker.py
