"""Door Access 상세페이지 PNG export 스크립트

Playwright로 31개 HTML 파일을 섹션별로 PNG 이미지로 export합니다.
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.insert(0, "/Users/cheil/tbd/product_pages/scripts")

from playwright.async_api import async_playwright

PAGES_DIR = Path("/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html")
EXPORTS_BASE = PAGES_DIR / "exports"

# Door Access 제품 HTML 파일명 -> export 폴더명
DOOR_ACCESS_PAGES = {
    # Batch 1: 핵심 제품
    "Unifi Supply - Reader Pro.dc.html": "reader-pro",
    "Unifi Supply - Reader Flex.dc.html": "reader-flex",
    "Unifi Supply - Access Ultra.dc.html": "access-ultra",
    "Unifi Supply - Door Hub.dc.html": "door-hub",
    "Unifi Supply - Door Hub Mini.dc.html": "door-hub-mini",

    # Batch 2: 엔터프라이즈/인터콤
    "Unifi Supply - Enterprise Access Hub.dc.html": "enterprise-access-hub",
    "Unifi Supply - Intercom Viewer.dc.html": "intercom-viewer",
    "Unifi Supply - G6 Entry.dc.html": "g6-entry",
    "Unifi Supply - Magnetic Lock.dc.html": "magnetic-lock",
    "Unifi Supply - Access Button.dc.html": "access-button",

    # Batch 3: Simple 액세서리
    "Unifi Supply - Reader Junction Box.dc.html": "reader-junction-box",
    "Unifi Supply - Reader Pro Junction Box.dc.html": "reader-pro-junction-box",
    "Unifi Supply - Reader Pro Angle Mount.dc.html": "reader-pro-angle-mount",
    "Unifi Supply - Intercom Viewer Table Stand.dc.html": "intercom-viewer-table-stand",
    "Unifi Supply - Intercom Flush Mount.dc.html": "intercom-flush-mount",
    "Unifi Supply - Intercom Surface Angle Mount.dc.html": "intercom-surface-angle-mount",
    "Unifi Supply - Intercom Wedge Mount.dc.html": "intercom-wedge-mount",
    "Unifi Supply - Intercom Sunshield.dc.html": "intercom-sunshield",
    "Unifi Supply - Gate Hub.dc.html": "gate-hub",
    "Unifi Supply - Junction Utility.dc.html": "junction-utility",
    "Unifi Supply - Door Lock Relay Cable.dc.html": "door-lock-relay-cable",
    "Unifi Supply - Door Closer.dc.html": "door-closer",
    "Unifi Supply - PoE Over 2-Wire Retrofit Extender.dc.html": "poe-over-2wire-retrofit-extender",
    "Unifi Supply - Retrofit Hub.dc.html": "retrofit-hub",
    "Unifi Supply - Retrofit PSU 12V.dc.html": "retrofit-psu-12v",
    "Unifi Supply - Panic Bar.dc.html": "panic-bar",
    "Unifi Supply - Access Rescue KeySwitch.dc.html": "access-rescue-keyswitch",
    "Unifi Supply - Access Card 10-Pack.dc.html": "access-card-10pack",
    "Unifi Supply - Pocket Keyfob 10-Pack.dc.html": "pocket-keyfob-10pack",
    "Unifi Supply - Gate Starter Kit.dc.html": "gate-starter-kit",
    "Unifi Supply - G3 Elevator Starter Kit.dc.html": "g3-elevator-starter-kit",
}


async def export_page(page, html_file, export_dir):
    """단일 페이지를 섹션별로 PNG로 export합니다."""
    file_path = PAGES_DIR / html_file
    if not file_path.exists():
        print(f"  ⚠️  파일 없음: {html_file}")
        return False

    # export 디렉토리 생성
    export_dir.mkdir(parents=True, exist_ok=True)

    # HTML 파일 로드
    await page.goto(f"file://{file_path}")
    await page.wait_for_timeout(1000)  # 폰트 로딩 대기

    # 모든 섹션 찾기
    sections = await page.query_selector_all('[data-screen-label]')

    if not sections:
        print(f"  ⚠️  섹션 없음: {html_file}")
        return False

    # 각 섹션을 PNG로 export
    for idx, section in enumerate(sections, start=1):
        label = await section.get_attribute('data-screen-label')
        filename = f"{idx:02d}-{label.lower().replace(' ', '-').replace('/', '-')}.png"
        output_path = export_dir / filename

        await section.screenshot(path=str(output_path))
        print(f"    ✓ {filename}")

    return True


async def export_all_pages():
    """모든 Door Access 페이지를 export합니다."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 860, "height": 600})

        processed = 0
        failed = 0

        for html_file, slug in DOOR_ACCESS_PAGES.items():
            print(f"\n처리 중: {html_file}")
            export_dir = EXPORTS_BASE / slug

            success = await export_page(page, html_file, export_dir)
            if success:
                processed += 1
            else:
                failed += 1

        await browser.close()

        print(f"\n{'='*60}")
        print(f"✅ 처리 완료: {processed}개 페이지")
        print(f"⚠️  실패: {failed}개 페이지")
        print(f"{'='*60}")


if __name__ == "__main__":
    print("Door Access 상세페이지 PNG export 시작...\n")
    asyncio.run(export_all_pages())
