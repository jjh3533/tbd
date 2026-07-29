"""16개 WiFi 제품 상세페이지를 Playwright로 PNG export.

각 제품의 .dc.html을 렌더링해 섹션별 PNG로 export → exports/<slug>/ 에 저장.
"""
import subprocess
import os

PAGES_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html"
EXPORT_SCRIPT = "/Users/cheil/tbd/product_pages/scripts/export_sections.py"

# (HTML 파일명, slug)
PRODUCTS = [
    ("Unifi Supply - AC Pro.dc.html", "ac-pro"),
    ("Unifi Supply - Building Bridge XG.dc.html", "building-bridge-xg"),
    ("Unifi Supply - Device Bridge.dc.html", "device-bridge"),
    ("Unifi Supply - Device Bridge Switch.dc.html", "device-bridge-switch"),
    ("Unifi Supply - E7 Campus.dc.html", "e7-campus"),
    ("Unifi Supply - U6 Enterprise.dc.html", "u6-enterprise"),
    ("Unifi Supply - U6 Enterprise In-Wall.dc.html", "u6-enterprise-in-wall"),
    ("Unifi Supply - U6 In-Wall.dc.html", "u6-in-wall"),
    ("Unifi Supply - U6 Mesh.dc.html", "u6-mesh"),
    ("Unifi Supply - U6 Mesh Pro.dc.html", "u6-mesh-pro"),
    ("Unifi Supply - U6+.dc.html", "u6-plus"),
    ("Unifi Supply - U7 Outdoor.dc.html", "u7-outdoor"),
    ("Unifi Supply - U7 Pro Outdoor.dc.html", "u7-pro-outdoor"),
    ("Unifi Supply - U7 Pro Wall.dc.html", "u7-pro-wall"),
    ("Unifi Supply - U7 Pro XG Wall.dc.html", "u7-pro-xg-wall"),
    ("Unifi Supply - U7 Pro XGS.dc.html", "u7-pro-xgs"),
]

for html_file, slug in PRODUCTS:
    print(f"\n=== {slug} ===")
    html_path = os.path.join(PAGES_DIR, html_file)
    out_dir = os.path.join(PAGES_DIR, "exports", slug)

    if not os.path.exists(html_path):
        print(f"  ❌ HTML 없음: {html_path}")
        continue

    os.makedirs(out_dir, exist_ok=True)

    try:
        result = subprocess.run(
            ["python3", EXPORT_SCRIPT, html_path, out_dir],
            capture_output=True, text=True, check=True, timeout=120
        )
        print(result.stdout)
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout (120초 초과)")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Export 실패: {e.stderr}")

print("\n\n=== 완료 ===")
EOPY
