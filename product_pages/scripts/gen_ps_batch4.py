"""Physical Security Batch 4: 기타 3개
AI Horn Speaker / SuperLink Gateway / Floodlight
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
# 1) UniFi AI Horn Speaker
# ============================================================
pages["Unifi Supply - AI Horn Speaker.dc.html"] = assemble(
    hero(
        "AI Horn Speaker",
        "AI 혼 스피커 — 120dB 출력과 AI 이벤트 감지로<br>긴급 방송과 스마트 알림을 동시에 제공합니다.",
        "assets/up-ai-horn-speaker/up-ai-horn-speaker_01-hero-front.png",
        "AI Horn Speaker",
    ),
    why_section(
        "Why AI Horn Speaker",
        "120dB 출력,<br>AI 이벤트 감지,<br>양방향 오디오",
        "120dB 고출력 스피커로 넓은 공간에 긴급 방송을 전달하고, AI가 사람과 차량을 감지해 스마트 알림을 보냅니다.",
        [
            ("120dB 고출력,<br>넓은 커버리지",
             "120dB 출력으로 넓은 주차장, 창고, 야외 시설 등에 긴급 방송이나 안내 메시지를 명확하게 전달할 수 있습니다."),
            ("AI 이벤트 감지<br>(사람·차량)",
             "온디바이스 AI가 사람과 차량을 실시간으로 감지하고, 특정 이벤트 발생 시 사전 녹음된 메시지나 사이렌을 자동 재생할 수 있습니다."),
            ("양방향 오디오,<br>PoE 전원",
             "마이크가 내장되어 있어 UniFi Protect 앱을 통해 양방향 오디오 통신이 가능하며, PoE 케이블 하나로 전원과 네트워크를 동시 공급받습니다."),
        ],
    ),
    design_section(
        "assets/up-ai-horn-speaker/up-ai-horn-speaker_02-diagram.png",
        "AI Horn Speaker 구성",
        "IPX4 방수 등급,<br>벽면·폴 마운트,<br>내구성 있는 설계",
        "IPX4 방수 등급으로 옥내외 설치가 가능하며, 벽면이나 폴에 마운트할 수 있습니다.<br>내구성 있는 폴리카보네이트 인클로저로 제작되어 옥외 환경에 적합합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "⌀174 x 144 mm (⌀6.9 x 5.7\")"),
        ("Weight", "950 g (2.1 lb)"),
        ("Speaker Output", "120 dB @ 1m"),
        ("Frequency Response", "400 Hz ~ 8,000 Hz"),
        ("AI Detection", "사람, 차량 온디바이스 감지"),
        ("Audio", "마이크 내장 (양방향 오디오)"),
        ("Power Method", "PoE+ (802.3at, 최대 25W)"),
        ("Mounting", "Wall, Pole (마운트 하드웨어 포함)"),
        ("Weatherproofing", "IPX4 (옥내외 설치 가능)"),
        ("Operating Temperature", "-10 to 50°C (14 to 122°F)"),
    ]),
)

# ============================================================
# 2) UniFi SuperLink Gateway
# ============================================================
pages["Unifi Supply - SuperLink Gateway.dc.html"] = assemble(
    hero(
        "SuperLink Gateway",
        "장거리 무선 센서 허브 — 최대 96개 센서를 2km 범위에서<br>연결하는 SubGHz 무선 게이트웨이.",
        "assets/usl-gateway/usl-gateway_01-hero-front.png",
        "SuperLink Gateway",
    ),
    why_section(
        "Why SuperLink Gateway",
        "96개 센서 연결,<br>2km 범위,<br>SubGHz 무선",
        "SubGHz 무선 기술로 최대 2km 범위에서 96개의 UniFi Access 센서를 연결하고, PoE로 간편하게 전원을 공급받습니다.",
        [
            ("96개 센서,<br>2km 범위",
             "SubGHz 무선 기술로 최대 96개의 UniFi Access 센서(도어, 모션, 유리 파손 등)를 최대 2km 범위에서 연결할 수 있습니다."),
            ("벽 관통 우수,<br>장거리 통신",
             "SubGHz 대역(900MHz)은 2.4GHz나 5GHz보다 벽 관통력이 우수하고 장거리 통신에 유리해, 넓은 건물이나 캠퍼스 환경에 적합합니다."),
            ("PoE 전원,<br>컴팩트한 디자인",
             "PoE 케이블 하나로 전원과 네트워크를 동시 공급받으며, 컴팩트한 디자인으로 벽면이나 선반에 간편하게 설치할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/usl-gateway/usl-gateway_02-diagram.png",
        "SuperLink Gateway 구성",
        "외장 안테나 포함,<br>LED 상태 표시,<br>실내 설치",
        "외장 안테나가 포함되어 있어 신호 범위를 최적화할 수 있으며, LED로 게이트웨이 상태와 센서 연결 상태를 표시합니다.<br>실내 설치를 권장하며, UniFi Access 시스템과 연동됩니다.",
    ),
    tech_specs_section([
        ("Dimensions", "97 x 97 x 25 mm (3.8 x 3.8 x 1.0\")"),
        ("Weight", "120 g (4.2 oz)"),
        ("Wireless", "SubGHz (900MHz ISM band)"),
        ("Max. Sensors", "96개 센서 연결"),
        ("Range", "최대 2 km (1.2 mi) 야외 직선, 실내는 환경에 따라 다름"),
        ("Antenna", "외장 안테나 포함 (RP-SMA)"),
        ("Ports", "(1) GbE RJ45 port"),
        ("Power Method", "PoE (802.3af, 최대 7W)"),
        ("LED Indicator", "상태 및 센서 연결 표시"),
        ("Mounting", "Wall, Desktop (마운트 하드웨어 포함)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Environment", "실내 설치 권장"),
    ]),
)

# ============================================================
# 3) UniFi Floodlight
# ============================================================
pages["Unifi Supply - Floodlight.dc.html"] = assemble(
    hero(
        "Floodlight",
        "스마트 투광등 카메라 — 2800 루멘 조명과 1080p 카메라,<br>양방향 오디오를 하나의 기기로 통합합니다.",
        "assets/up-floodlight/up-floodlight_01-hero-front.png",
        "Floodlight",
    ),
    why_section(
        "Why Floodlight",
        "2800 루멘 조명,<br>1080p 카메라,<br>모션 감지",
        "2800 루멘 LED 조명과 1080p 카메라를 하나의 기기로 통합해, 현관, 주차장, 정원을 밝히고 동시에 감시합니다.",
        [
            ("2800 루멘 LED,<br>3000K 웜화이트",
             "30W LED가 2800 루멘 밝기로 넓은 영역을 비추며, 3000K 웜화이트 색온도로 편안한 조명을 제공합니다. 110도 빔 각도로 골고루 확산됩니다."),
            ("1080p 카메라,<br>113° 시야각",
             "1080p Full HD 카메라가 113도 시야각으로 넓은 영역을 촬영하며, 적외선 야간 촬영과 모션 감지를 지원합니다."),
            ("양방향 오디오,<br>PoE 전원",
             "마이크와 스피커가 내장되어 있어 UniFi Protect 앱을 통해 양방향 오디오 통신이 가능하며, PoE 케이블 하나로 전원과 네트워크를 동시 공급받습니다."),
        ],
    ),
    design_section(
        "assets/up-floodlight/up-floodlight_02-diagram.png",
        "Floodlight 구성",
        "모션 감지 자동 점등,<br>일정 제어,<br>옥외 방수",
        "모션 감지 시 자동으로 조명이 켜지며, UniFi Protect 앱에서 조명 일정과 밝기를 제어할 수 있습니다.<br>옥외 방수 등급으로 현관, 주차장, 정원 등에 설치할 수 있습니다.",
    ),
    tech_specs_section([
        ("Dimensions", "276 x 147 x 221 mm (10.9 x 5.8 x 8.7\")"),
        ("Weight", "1.36 kg (3.0 lb)"),
        ("LED Output", "2800 lumens, 30W"),
        ("Color Temperature", "3000K (웜화이트)"),
        ("Beam Angle", "110°"),
        ("LED Lifespan", "50,000+ hours"),
        ("Camera Resolution", "1080p Full HD @ 24 FPS"),
        ("Field of View", "113° (카메라)"),
        ("Night Vision", "적외선 LED"),
        ("Audio", "마이크 + 스피커 (양방향 오디오)"),
        ("Motion Detection", "PIR 센서 내장"),
        ("Power Method", "PoE (802.3af, 최대 15.4W)"),
        ("Mounting", "Wall, Eave (마운트 하드웨어 포함)"),
        ("Weatherproofing", "옥외 방수 (등급 미공개)"),
        ("Operating Temperature", "-20 to 50°C (-4 to 122°F)"),
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
