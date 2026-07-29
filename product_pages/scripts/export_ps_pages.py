"""13개 Physical Security 제품 상세페이지를 Playwright로 PNG export.

각 제품의 .dc.html을 렌더링해 섹션별 PNG로 export → exports/<slug>/ 에 저장.
"""
import subprocess
import os

PAGES_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html"
EXPORT_SCRIPT = "/Users/cheil/tbd/product_pages/scripts/export_sections.py"

# (HTML 파일명, slug)
PRODUCTS = [
    # Batch 1: 카메라 5개
    ("Unifi Supply - G6 Pro 360.dc.html", "g6-pro-360"),
    ("Unifi Supply - AI PTZ Industrial.dc.html", "ai-ptz-industrial"),
    ("Unifi Supply - G5 Turret Ultra.dc.html", "g5-turret-ultra"),
    ("Unifi Supply - G6 Dome.dc.html", "g6-dome"),
    ("Unifi Supply - AI Theta.dc.html", "ai-theta"),

    # Batch 2: 센서 3개
    ("Unifi Supply - All-In-One Sensor.dc.html", "all-in-one-sensor"),
    ("Unifi Supply - Glass Break Sensor.dc.html", "glass-break-sensor"),
    ("Unifi Supply - Motion Sensor.dc.html", "motion-sensor"),

    # Batch 3: 녹화/컨트롤 2개
    ("Unifi Supply - Network Video Recorder Instant.dc.html", "nvr-instant"),
    ("Unifi Supply - CloudKey+.dc.html", "cloudkey-plus"),

    # Batch 4: 기타 3개
    ("Unifi Supply - AI Horn Speaker.dc.html", "ai-horn-speaker"),
    ("Unifi Supply - SuperLink Gateway.dc.html", "superlink-gateway"),
    ("Unifi Supply - Floodlight.dc.html", "floodlight"),
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
print(f"{len(PRODUCTS)}개 제품 PNG export 완료")
