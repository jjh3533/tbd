"""Physical Security Batch 2: 센서 3개
All-In-One Sensor / Glass Break Sensor / Motion Sensor
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
# 1) UniFi All-In-One Sensor
# ============================================================
pages["Unifi Supply - All-In-One Sensor.dc.html"] = assemble(
    hero(
        "All-In-One Sensor",
        "5가지 센서 통합 — 온도, 습도, 조도, 모션, 도어 감지를<br>하나의 컴팩트한 센서로 통합합니다.",
        "assets/up-sense/up-sense_01-hero-front.png",
        "All-In-One Sensor",
    ),
    why_section(
        "Why All-In-One Sensor",
        "5가지 센서를<br>하나의 기기로<br>통합",
        "온도, 습도, 조도, 모션, 도어 감지를 하나의 센서로 통합해 스마트 빌딩 자동화와 보안을 간편하게 구현합니다.",
        [
            ("온도·습도·조도<br>환경 센서",
             "온도, 습도, 조도를 실시간으로 측정해 HVAC 제어, 조명 자동화 등 스마트 빌딩 시나리오에 활용할 수 있습니다."),
            ("모션·도어 센서<br>보안 감지",
             "PIR 모션 센서와 도어 자석 센서(별도 포함)로 침입 감지, 출입 모니터링 등 보안 시나리오를 구현합니다."),
            ("10년 배터리 수명,<br>Bluetooth LE",
             "CR123A 배터리 하나로 최대 10년 동작하며, Bluetooth Low Energy로 UniFi Access나 Protect 시스템과 연동됩니다."),
        ],
    ),
    design_section(
        "assets/up-sense/up-sense_02-diagram.png",
        "All-In-One Sensor 구성",
        "도어 센서 마그넷 포함,<br>벽면 마운트,<br>컴팩트 디자인",
        "도어/창문 감지용 마그넷 센서가 포함되어 있으며, 양면테이프나 나사로 벽면에 간편하게 설치할 수 있습니다.<br>컴팩트한 디자인으로 눈에 띄지 않게 설치 가능합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "50 x 50 x 18 mm (2.0 x 2.0 x 0.7\")"),
        ("Weight", "35 g (1.2 oz)"),
        ("Sensors", "온도, 습도, 조도, PIR 모션, 도어 자석 (5-in-1)"),
        ("Temperature Range", "-10°C to 60°C (14°F to 140°F) 측정"),
        ("Humidity Range", "0-100% RH 측정"),
        ("Motion Detection", "PIR 센서, 최대 5 m (16 ft) 범위"),
        ("Door Sensor", "자석 센서 포함 (최대 20 mm 간격)"),
        ("Connectivity", "Bluetooth Low Energy (BLE)"),
        ("Battery", "CR123A, 최대 10년 수명"),
        ("Mounting", "Wall (양면테이프 또는 나사, 포함)"),
        ("Operating Temperature", "-10 to 60°C (14 to 140°F)"),
    ]),
)

# ============================================================
# 2) UniFi Glass Break Sensor
# ============================================================
pages["Unifi Supply - Glass Break Sensor.dc.html"] = assemble(
    hero(
        "Glass Break Sensor",
        "유리 파손 감지 센서 — 창문이나 유리문의 파손 소리를<br>감지해 즉시 알림을 보냅니다.",
        "assets/usl-glassbreak/usl-glassbreak_01-hero-front.png",
        "Glass Break Sensor",
    ),
    why_section(
        "Why Glass Break Sensor",
        "유리 파손을<br>음향으로 감지,<br>10년 배터리",
        "100Hz~15kHz 범위의 유리 파손 주파수를 음향으로 감지해 침입 시도를 실시간으로 알립니다.",
        [
            ("유리 파손 주파수<br>음향 감지",
             "100Hz~15,000Hz 범위의 유리 파손 특유의 음향 패턴을 감지해, 창문이나 유리문 파손 시 즉시 알림을 보냅니다."),
            ("최대 7.6m 감지 범위,<br>실내용",
             "최대 7.6m(25ft) 범위 내의 유리 파손을 감지할 수 있으며, 실내 벽면이나 천장에 설치합니다."),
            ("10년 배터리 수명,<br>무선 연결",
             "CR123A 배터리 하나로 최대 10년 동작하며, 무선으로 UniFi Access 시스템과 연동됩니다."),
        ],
    ),
    design_section(
        "assets/usl-glassbreak/usl-glassbreak_02-diagram.png",
        "Glass Break Sensor 구성",
        "벽면·천장 마운트,<br>LED 상태 표시,<br>컴팩트 디자인",
        "벽면이나 천장에 간편하게 설치할 수 있으며, LED로 센서 상태와 감지 이벤트를 시각적으로 표시합니다.<br>컴팩트한 화이트 디자인으로 인테리어와 조화를 이룹니다.",
    ),
    tech_specs_section([
        ("Dimensions", "76 x 76 x 25 mm (3.0 x 3.0 x 1.0\")"),
        ("Weight", "80 g (2.8 oz)"),
        ("Detection Type", "음향 감지 (유리 파손 주파수)"),
        ("Frequency Range", "100 Hz ~ 15,000 Hz"),
        ("Detection Range", "최대 7.6 m (25 ft)"),
        ("Connectivity", "무선 (UniFi Access 시스템)"),
        ("Battery", "CR123A, 최대 10년 수명"),
        ("LED Indicator", "상태 및 이벤트 표시"),
        ("Mounting", "Wall, Ceiling (마운트 하드웨어 포함)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Environment", "실내 전용"),
    ]),
)

# ============================================================
# 3) UniFi Motion Sensor
# ============================================================
pages["Unifi Supply - Motion Sensor.dc.html"] = assemble(
    hero(
        "Motion Sensor",
        "PIR 모션 센서 — 7m 범위, 110° 시야각으로 움직임을<br>감지해 조명이나 카메라를 자동으로 트리거합니다.",
        "assets/usl-motion/usl-motion_01-hero-front.png",
        "Motion Sensor",
    ),
    why_section(
        "Why Motion Sensor",
        "7m 범위,<br>110° 시야각,<br>10년 배터리",
        "PIR 센서로 최대 7m 범위의 움직임을 감지하고, UniFi Protect나 Access 시스템과 연동해 자동화를 구현합니다.",
        [
            ("PIR 센서,<br>7m 감지 범위",
             "PIR(Passive Infrared) 센서가 사람의 체온을 감지해 최대 7m(23ft) 범위 내 움직임을 포착합니다."),
            ("110° 시야각,<br>실내 최적화",
             "110도 시야각으로 넓은 실내 공간을 커버하며, 출입구나 복도에 설치해 출입 감지 및 조명 자동화에 활용할 수 있습니다."),
            ("10년 배터리 수명,<br>Bluetooth LE",
             "CR123A 배터리 2개로 최대 10년 동작하며, Bluetooth Low Energy로 UniFi 시스템과 무선 연동됩니다."),
        ],
    ),
    design_section(
        "assets/usl-motion/usl-motion_02-diagram.png",
        "Motion Sensor 구성",
        "벽면·코너 마운트,<br>LED 상태 표시,<br>컴팩트 디자인",
        "벽면이나 코너에 간편하게 설치할 수 있으며, LED로 센서 상태와 감지 이벤트를 시각적으로 표시합니다.<br>컴팩트한 화이트 디자인으로 눈에 띄지 않게 설치 가능합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "41.5 x 41.5 x 24 mm (1.6 x 1.6 x 0.9\")"),
        ("Weight", "40 g (1.4 oz)"),
        ("Detection Type", "PIR (Passive Infrared)"),
        ("Detection Range", "최대 7 m (23 ft)"),
        ("Field of View", "110° 시야각"),
        ("Connectivity", "Bluetooth Low Energy (BLE)"),
        ("Battery", "2x CR123A, 최대 10년 수명"),
        ("LED Indicator", "상태 및 이벤트 표시"),
        ("Mounting", "Wall, Corner (마운트 하드웨어 포함)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Environment", "실내 전용"),
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
