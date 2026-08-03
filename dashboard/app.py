"""NiceGUI 대시보드 엔트리포인트.

실행:
    python3 dashboard/app.py

기존 app.py(Streamlit)는 그대로 두고(Streamlit Cloud 배포 유지), 이 대시보드는
로컬/사내망에서 별도 프로세스로 띄운다."""
import sys
from pathlib import Path

# 프로젝트 루트(sync_engine.py, config.py, nocodb_client.py 등)를 import 경로에 추가.
sys.path.insert(0, str(Path(__file__).parent.parent))

from nicegui import app, ui

import sync_engine
from dashboard.auth import AuthMiddleware, DASHBOARD_STORAGE_SECRET

# 각 페이지 모듈을 import해야 @ui.page 데코레이터가 등록된다.
from dashboard.pages import (  # noqa: F401
    login, home, category, brand, register, inventory, needs_check, orders,
    sync, smartstore, detail_page_builder,
)

app.add_middleware(AuthMiddleware)

# 매일 09:00 KST 전체 동기화 + 4시간마다 확인 필요 상품만 재조회하는 백그라운드
# 스케줄러. reload=False라 이 모듈은 프로세스당 한 번만 실행되므로, 중복
# 스케줄러가 뜰 걱정 없이 여기서 바로 시작한다.
sync_engine.start_background_scheduler()

ui.run(
    title="UniFi Supply Center",
    favicon="⚡",
    host="0.0.0.0",  # 컨테이너 밖에서 접속하려면 필수
    port=8080,
    storage_secret=DASHBOARD_STORAGE_SECRET,
    reload=False,
)
