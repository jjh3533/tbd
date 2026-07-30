"""Integrations 제품 8개의 HTML을 Playwright로 PNG export합니다."""
import sys
from pathlib import Path

# export_sections.py의 함수를 재사용
sys.path.insert(0, str(Path(__file__).parent))
from export_sections import export_sections

PAGES_DIR = Path("/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html")

# Export할 HTML 파일 목록
HTML_FILES = [
    "Unifi Supply - Mobile Router Industrial.dc.html",
    "Unifi Supply - UNAS 2.dc.html",
    "Unifi Supply - Display Cast Lite.dc.html",
    "Unifi Supply - Mobile Router.dc.html",
    "Unifi Supply - 5G Max.dc.html",
    "Unifi Supply - Mobile Router Ultra.dc.html",
    "Unifi Supply - PoE Audio Port.dc.html",
    "Unifi Supply - LTE Backup Pro.dc.html",
]


def main():
    print("Integrations 제품 HTML → PNG export 시작\n")

    for html_file in HTML_FILES:
        html_path = PAGES_DIR / html_file
        if not html_path.exists():
            print(f"⚠️  파일 없음: {html_file}")
            continue

        # 파일명에서 슬러그 추출 (예: "mobile-router-industrial")
        slug = html_file.replace("Unifi Supply - ", "").replace(".dc.html", "")
        slug = slug.lower().replace(" ", "-")
        export_dir = PAGES_DIR / "exports" / slug

        print(f"Export 중: {html_file}")
        print(f"  → {export_dir}/")

        try:
            export_sections(str(html_path), str(export_dir))
            print(f"  ✓ 완료\n")
        except Exception as e:
            print(f"  ⚠️  오류: {e}\n")

    print("="*60)
    print("PNG export 완료.")


if __name__ == "__main__":
    main()
