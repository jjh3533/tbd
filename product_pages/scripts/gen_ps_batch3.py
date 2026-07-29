"""Physical Security Batch 3: 녹화/컨트롤 2개
NVR Instant / CloudKey+
"""
import sys
sys.path.insert(0, "/Users/cheil/tbd/product_pages/scripts")
from build_pages import (
    HEAD, TRUST_TO_FOOTER, tech_specs_section,
    hero, why_section, design_section,
)

OUT_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html"


def assemble(hero_html, why_html, design_html, tech_specs_html):
    return HEAD + hero_html + why_html + design_html + tech_specs_html + TRUST_TO_FOOTER


pages = {}

# ============================================================
# 1) UniFi Network Video Recorder Instant
# ============================================================
pages["Unifi Supply - Network Video Recorder Instant.dc.html"] = assemble(
    hero(
        "Network Video Recorder Instant",
        "소규모 Protect 시스템 — 6개 PoE 포트로 카메라에 전원을<br>공급하고 영상을 로컬 HDD에 저장합니다.",
        "assets/unvr-instant/unvr-instant_01-hero-front.png",
        "Network Video Recorder Instant",
    ),
    why_section(
        "Why Network Video Recorder Instant",
        "6 PoE 포트,<br>1 HDD 베이,<br>간편한 설치",
        "6개의 PoE 포트로 카메라에 전원과 네트워크를 동시 공급하고, 1개의 HDD 베이에 영상을 로컬 저장합니다.",
        [
            ("6개 PoE 포트,<br>카메라 직접 연결",
             "6개의 PoE 포트(802.3af/at)로 UniFi Protect 카메라에 전원과 네트워크를 동시 공급하며, 별도 스위치 없이 카메라를 직접 연결할 수 있습니다."),
            ("1 HDD 베이,<br>최대 5TB 저장소",
             "3.5\" SATA HDD 베이 1개로 최대 5TB의 영상을 로컬 저장할 수 있으며, 약 15대의 1080p 카메라 영상을 30일간 저장 가능합니다."),
            ("UniFi Protect 사전 설치,<br>간편한 설정",
             "UniFi Protect 소프트웨어가 사전 설치되어 있어 카메라를 연결하고 바로 사용할 수 있으며, UniFi 앱으로 원격 관리가 가능합니다."),
        ],
    ),
    design_section(
        "assets/unvr-instant/unvr-instant_02-diagram.png",
        "Network Video Recorder Instant 구성",
        "컴팩트한 데스크탑 디자인,<br>1 GbE WAN 포트,<br>저소음 팬리스",
        "컴팩트한 데스크탑 디자인으로 책상이나 선반에 설치할 수 있으며, 1개의 기가비트 이더넷 WAN 포트로 네트워크에 연결됩니다.<br>팬리스 설계로 무소음 동작하며, LED로 시스템 상태를 표시합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "196 x 196 x 44 mm (7.7 x 7.7 x 1.7\")"),
        ("Weight", "700 g (1.5 lb) excluding HDD"),
        ("Processor", "Quad-core ARM Cortex-A53"),
        ("Memory", "2 GB DDR4"),
        ("Storage", "1x 3.5\" SATA HDD bay (최대 5TB, HDD 별도 구매)"),
        ("Ports", "(6) GbE PoE RJ45 ports (802.3af/at), (1) GbE RJ45 WAN port"),
        ("PoE Budget", "최대 46W (전체 6 포트)"),
        ("Camera Support", "최대 15x 1080p 카메라 (30일 저장 기준)"),
        ("Software", "UniFi Protect (사전 설치)"),
        ("Power Method", "AC 어댑터 (포함, 60W)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Mounting", "Desktop, Rack (선택 사항)"),
    ]),
)

# ============================================================
# 2) UniFi CloudKey+
# ============================================================
pages["Unifi Supply - CloudKey+.dc.html"] = assemble(
    hero(
        "CloudKey+",
        "올인원 컨트롤러 — UniFi Network 컨트롤러와 Protect를<br>1TB SSD에 통합한 컴팩트한 관리 허브.",
        "assets/uck-g2-ssd/uck-g2-ssd_01-hero-front.png",
        "CloudKey+",
    ),
    why_section(
        "Why CloudKey+",
        "Network + Protect<br>올인원 컨트롤러,<br>1TB SSD 내장",
        "UniFi Network 컨트롤러와 Protect 영상 관리를 하나의 컴팩트한 기기로 통합하고, 1TB SSD에 영상을 저장합니다.",
        [
            ("Network + Protect<br>올인원 관리",
             "UniFi Network 컨트롤러와 Protect 영상 관리를 하나의 기기로 통합해, 네트워크와 보안 시스템을 중앙에서 관리할 수 있습니다."),
            ("1TB SSD 내장,<br>20+ 카메라 지원",
             "1TB SSD가 내장되어 있어 약 20대의 카메라 영상을 저장할 수 있으며(해상도·프레임레이트에 따라 다름), 5대 1080p 카메라 기준 약 30일 저장 가능합니다."),
            ("배터리 백업,<br>1.3\" 터치스크린",
             "내장 배터리로 정전 시에도 안전하게 종료되며, 1.3인치 터치스크린으로 시스템 상태를 직접 확인할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/uck-g2-ssd/uck-g2-ssd_02-diagram.png",
        "CloudKey+ 구성",
        "Quad-core CPU,<br>3GB RAM,<br>컴팩트한 디자인",
        "Quad-core ARM Cortex-A53 프로세서와 3GB DDR4 RAM으로 네트워크 관리와 영상 처리를 동시에 수행하며, 기가비트 이더넷 포트와 USB 3.0 포트를 갖추고 있습니다.<br>컴팩트한 디자인으로 책상이나 랙에 설치할 수 있습니다.",
    ),
    tech_specs_section([
        ("Dimensions", "145 x 145 x 28 mm (5.7 x 5.7 x 1.1\")"),
        ("Weight", "450 g (15.9 oz)"),
        ("Processor", "Quad-core ARM Cortex-A53 @ 1.5GHz"),
        ("Memory", "3 GB DDR4"),
        ("Storage", "1TB 2.5\" SATA SSD (내장)"),
        ("Expansion", "USB 3.0 port (외장 드라이브 지원)"),
        ("Display", "1.3\" LCD 터치스크린"),
        ("Battery", "내장 충전식 배터리 (정전 시 안전 종료)"),
        ("Ports", "(1) GbE RJ45 port, (1) USB 3.0 port"),
        ("Camera Support", "최대 20+ 카메라 (해상도·프레임레이트에 따라 다름)"),
        ("Software", "UniFi Network Controller, UniFi Protect (사전 설치)"),
        ("Power Method", "PoE+ (802.3at, 최대 13W)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Mounting", "Desktop, Rack (선택 사항)"),
    ]),
)

# ============================================================

if __name__ == "__main__":
    for filename, content in pages.items():
        path = f"{OUT_DIR}/{filename}"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ {filename}")
    print(f"\n총 {len(pages)}개 페이지 생성 완료")
