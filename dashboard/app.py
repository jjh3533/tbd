"""NiceGUI 대시보드 엔트리포인트.

실행:
    python3 dashboard/app.py

기존 app.py(Streamlit)는 그대로 두고(Streamlit Cloud 배포 유지), 이 대시보드는
로컬/사내망에서 별도 프로세스로 띄운다."""
import sys
from pathlib import Path

# 프로젝트 루트(sync_engine.py, config.py, nocodb_client.py 등)를 import 경로에 추가.
sys.path.insert(0, str(Path(__file__).parent.parent))

from nicegui import ui

# 각 페이지 모듈을 import해야 @ui.page 데코레이터가 등록된다.
from dashboard.pages import home, category, register  # noqa: F401

ui.run(
    title="UniFi Supply Center",
    favicon="⚡",
    host="0.0.0.0",  # 컨테이너 밖에서 접속하려면 필수
    port=8080,
    storage_secret="tbd-dashboard-local-dev-secret",
    reload=False,
)
