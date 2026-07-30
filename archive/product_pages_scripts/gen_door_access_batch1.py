"""Door Access Batch 1: Reader Pro / Reader Flex / Access Ultra / Door Hub / Door Hub Mini

핵심 액세스 컨트롤러 5개.
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
# 1) UniFi Reader Pro
# ============================================================
pages["Unifi Supply - Reader Pro.dc.html"] = assemble(
    hero(
        "Reader Pro",
        "엔터프라이즈급 NFC/Bluetooth 리더 — IP65 방수,<br>Wiegand 출력, 터치 피드백과 LED 링을 갖춘 도어 액세스 컨트롤러.",
        "assets/ua-reader-pro/ua-reader-pro_01-hero-front.png",
        "Reader Pro",
    ),
    why_section(
        "Why Reader Pro",
        "IP65 방수,<br>NFC/BLE 듀얼,<br>Wiegand 출력",
        "실내외 모두 설치 가능한 IP65 방수 등급으로, NFC 카드와 Bluetooth 모바일 키를 동시 지원하며, 기존 시스템과 연동할 수 있는 Wiegand 출력을 제공합니다.",
        [
            ("NFC + Bluetooth<br>듀얼 인증",
             "13.56MHz NFC 카드와 Bluetooth Low Energy 모바일 키를 모두 지원해, 사용자 선택의 폭을 넓힙니다."),
            ("IP65 방수,<br>실내외 설치",
             "IP65 방수/방진 등급으로 옥외 출입구에도 설치 가능하며, -40~55°C 작동 온도 범위를 지원합니다."),
            ("Wiegand 출력,<br>기존 시스템 연동",
             "Wiegand 26/34 프로토콜 출력을 내장해 기존 액세스 컨트롤 시스템과 통합할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/ua-reader-pro/ua-reader-pro_02-diagram.png",
        "Reader Pro 디자인",
        "터치 피드백,<br>LED 링,<br>PoE 전원",
        "사용자 인증 시 터치 피드백과 멀티컬러 LED 링으로 즉각적인 피드백을 제공합니다.<br>PoE 또는 12-24V DC로 전원을 공급하며, 벽면 또는 표면 마운트(별도 액세서리)가 가능합니다. 알루미늄 합금 인클로저로 내구성을 보장합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "108 x 38 x 17 mm (4.3 x 1.5 x 0.7\")"),
        ("Weight", "113 g (4 oz)"),
        ("Access Methods", "NFC (13.56 MHz ISO/IEC 14443 Type A/B), Bluetooth Low Energy (BLE 5.0)"),
        ("Wiegand Output", "26-bit, 34-bit configurable"),
        ("LED & Feedback", "Multi-color LED ring, Touch feedback"),
        ("Power Method", "PoE (802.3af, 최대 4W) 또는 12-24V DC (별도 어댑터)"),
        ("Weatherproofing", "IP65"),
        ("Operating Temperature", "-40 to 55°C (-40 to 131°F)"),
        ("Mounting", "Wall, Surface (별도 Angle Mount 사용 가능)"),
        ("Material", "Aluminum alloy, Polycarbonate"),
    ]),
)

# ============================================================
# 2) UniFi Reader Flex
# ============================================================
pages["Unifi Supply - Reader Flex.dc.html"] = assemble(
    hero(
        "Reader Flex",
        "컴팩트한 NFC/Bluetooth 리더 — 실내 설치에 최적화된<br>슬림한 폼팩터, 터치 피드백과 LED 표시.",
        "assets/ua-reader-flex/ua-reader-flex_01-hero-front.png",
        "Reader Flex",
    ),
    why_section(
        "Why Reader Flex",
        "슬림한 디자인,<br>NFC/BLE 지원,<br>실내 전용",
        "Reader Pro보다 컴팩트한 폼팩터로 실내 출입구에 세련되게 설치할 수 있으며, NFC 카드와 Bluetooth 모바일 키를 모두 지원합니다.",
        [
            ("NFC + Bluetooth<br>듀얼 인증",
             "13.56MHz NFC 카드와 Bluetooth Low Energy 모바일 키를 모두 인식해 다양한 사용자 환경을 지원합니다."),
            ("컴팩트한 디자인,<br>실내 최적화",
             "Reader Pro보다 작고 슬림한 폼팩터로 사무실, 공유 오피스 등 실내 환경에 세련되게 설치됩니다."),
            ("터치 피드백,<br>LED 표시",
             "사용자 인증 시 터치 피드백과 멀티컬러 LED로 즉각적인 상태를 알려줍니다."),
        ],
    ),
    design_section(
        "assets/ua-reader-flex/ua-reader-flex_02-diagram.png",
        "Reader Flex 구성",
        "PoE 전원,<br>벽면 마운트,<br>폴리카보네이트",
        "PoE(802.3af) 또는 12-24V DC로 전원을 공급하며, 벽면 마운트 하드웨어가 포함되어 있습니다.<br>폴리카보네이트 인클로저로 실내 환경에 적합하며, -10~40°C 작동 온도 범위를 지원합니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "95 x 35 x 15 mm (3.7 x 1.4 x 0.6\")"),
        ("Weight", "75 g (2.6 oz)"),
        ("Access Methods", "NFC (13.56 MHz ISO/IEC 14443 Type A/B), Bluetooth Low Energy (BLE 5.0)"),
        ("LED & Feedback", "Multi-color LED, Touch feedback"),
        ("Power Method", "PoE (802.3af, 최대 3W) 또는 12-24V DC (별도 어댑터)"),
        ("Operating Temperature", "-10 to 40°C (14 to 104°F)"),
        ("Mounting", "Wall (마운트 하드웨어 포함)"),
        ("Material", "Polycarbonate"),
    ]),
)

# ============================================================
# 3) UniFi Access Ultra
# ============================================================
pages["Unifi Supply - Access Ultra.dc.html"] = assemble(
    hero(
        "Access Ultra",
        "올인원 도어 컨트롤러 — Reader + Hub + 릴레이를<br>하나로 통합한 PoE 도어 액세스 솔루션.",
        "assets/ua-ultra/ua-ultra_01-hero-front.png",
        "Access Ultra",
    ),
    why_section(
        "Why Access Ultra",
        "Reader + Hub + 릴레이<br>하나로 통합,<br>PoE 단일 케이블",
        "NFC/Bluetooth 리더, 컨트롤러, 릴레이를 하나의 장치에 통합해 설치 복잡도를 대폭 줄이고, PoE 케이블 하나로 전원과 네트워크를 동시 공급받습니다.",
        [
            ("Reader + Hub + 릴레이<br>3-in-1 통합",
             "별도 Hub나 릴레이 없이 Access Ultra 하나로 도어 락 제어, 사용자 인증, 네트워크 연결을 모두 처리합니다."),
            ("NFC + Bluetooth<br>듀얼 인증",
             "13.56MHz NFC 카드와 Bluetooth 모바일 키를 모두 지원하며, UniFi Access 앱에서 중앙 관리됩니다."),
            ("PoE 단일 케이블,<br>간편한 설치",
             "PoE(802.3af) 케이블 하나로 전원과 네트워크를 동시 공급해, 별도 전원 어댑터나 복잡한 배선이 필요 없습니다."),
        ],
    ),
    design_section(
        "assets/ua-ultra/ua-ultra_02-diagram.png",
        "Access Ultra 연결",
        "내장 릴레이,<br>센서 입력,<br>벽면 마운트",
        "NO/NC 릴레이 출력으로 전기 락을 직접 제어하며, 도어 센서(DPS) 입력을 내장해 문 열림 상태를 모니터링합니다.<br>-10~40°C 실내 환경에서 작동하며, 벽면 마운트 하드웨어가 포함됩니다.",
    ),
    tech_specs_section([
        ("Dimensions", "108 x 75 x 22 mm (4.3 x 3.0 x 0.9\")"),
        ("Weight", "150 g (5.3 oz)"),
        ("Access Methods", "NFC (13.56 MHz ISO/IEC 14443 Type A/B), Bluetooth Low Energy (BLE 5.0)"),
        ("Relay Output", "1x NO/NC (12-24V DC, 2A max)"),
        ("Sensor Input", "Door Position Sensor (DPS)"),
        ("LED & Feedback", "Multi-color LED, Touch feedback"),
        ("Power Method", "PoE (802.3af, 최대 6W)"),
        ("Operating Temperature", "-10 to 40°C (14 to 104°F)"),
        ("Mounting", "Wall (마운트 하드웨어 포함)"),
        ("Material", "Polycarbonate"),
    ]),
)

# ============================================================
# 4) UniFi Door Hub
# ============================================================
pages["Unifi Supply - Door Hub.dc.html"] = assemble(
    hero(
        "Door Hub",
        "4도어 액세스 컨트롤러 — 최대 4개 리더와 4개 도어 락을<br>관리하는 중앙 PoE 허브.",
        "assets/ua-hub/ua-hub_01-hero-front.png",
        "Door Hub",
    ),
    why_section(
        "Why Door Hub",
        "4도어 동시 관리,<br>Reader 4개 연결,<br>PoE 전원",
        "최대 4개의 UniFi Reader를 연결해 4개의 도어를 중앙에서 관리하며, PoE 하나로 전원과 네트워크를 동시 공급받습니다.",
        [
            ("4개 리더 연결,<br>4개 도어 관리",
             "최대 4개의 UniFi Reader를 연결해 각각 독립적인 액세스 정책으로 4개 도어를 제어할 수 있습니다."),
            ("4개 릴레이 출력,<br>센서 입력 4개",
             "각 도어마다 NO/NC 릴레이 출력과 도어 센서(DPS) 입력을 제공해 락 제어와 문 상태 모니터링을 동시에 처리합니다."),
            ("PoE 전원,<br>백업 12V DC",
             "PoE(802.3at) 케이블로 전원을 공급하며, 별도 12V DC 입력으로 백업 전원을 연결할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/ua-hub/ua-hub_02-diagram.png",
        "Door Hub 포트",
        "4x Reader 포트,<br>4x 릴레이 출력,<br>DIN 레일 마운트",
        "4개의 Reader 포트(RJ12)와 4개의 릴레이 출력 터미널 블록을 갖추고 있으며, 각 포트는 최대 100m 거리의 Reader를 지원합니다.<br>DIN 레일 또는 벽면 마운트로 설치 가능하며, 금속 인클로저로 내구성을 보장합니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "117 x 85 x 26 mm (4.6 x 3.3 x 1.0\")"),
        ("Weight", "200 g (7.1 oz)"),
        ("Reader Ports", "4x RJ12 ports (최대 100m per reader)"),
        ("Relay Outputs", "4x NO/NC (12-24V DC, 2A max per relay)"),
        ("Sensor Inputs", "4x Door Position Sensor (DPS)"),
        ("Ethernet", "1x GbE RJ45 (network uplink)"),
        ("Power Method", "PoE (802.3at, 최대 12W) + 12V DC backup input"),
        ("Operating Temperature", "-10 to 50°C (14 to 122°F)"),
        ("Mounting", "DIN rail, Wall"),
        ("Material", "Metal enclosure"),
    ]),
)

# ============================================================
# 5) UniFi Door Hub Mini
# ============================================================
pages["Unifi Supply - Door Hub Mini.dc.html"] = assemble(
    hero(
        "Door Hub Mini",
        "1도어 컴팩트 컨트롤러 — 단일 Reader와 단일 도어 락을<br>관리하는 소형 PoE 허브.",
        "assets/ua-hub-mini/ua-hub-mini_01-hero-front.png",
        "Door Hub Mini",
    ),
    why_section(
        "Why Door Hub Mini",
        "1도어 전용,<br>컴팩트한 설계,<br>PoE 전원",
        "소규모 설치나 단일 도어 환경에 최적화된 컴팩트한 폼팩터로, Door Hub의 핵심 기능을 1도어 규모로 제공합니다.",
        [
            ("1개 Reader 연결,<br>1개 도어 관리",
             "1개의 UniFi Reader를 연결해 단일 도어를 제어하며, 소규모 사무실이나 스타트업에 적합합니다."),
            ("1개 릴레이 출력,<br>센서 입력",
             "NO/NC 릴레이 출력과 도어 센서(DPS) 입력을 제공해 락 제어와 문 상태 모니터링을 처리합니다."),
            ("PoE 전원,<br>컴팩트한 크기",
             "PoE(802.3af) 케이블로 전원을 공급하며, Door Hub보다 작은 크기로 공간 제약이 있는 환경에 설치 가능합니다."),
        ],
    ),
    design_section(
        "assets/ua-hub-mini/ua-hub-mini_02-diagram.png",
        "Door Hub Mini 구성",
        "1x Reader 포트,<br>1x 릴레이 출력,<br>벽면 마운트",
        "1개의 Reader 포트(RJ12)와 1개의 릴레이 출력 터미널 블록을 갖추고 있으며, 최대 100m 거리의 Reader를 지원합니다.<br>벽면 마운트로 설치 가능하며, 폴리카보네이트 인클로저로 제작됩니다.",
    ),
    tech_specs_section([
        ("Dimensions", "95 x 65 x 20 mm (3.7 x 2.6 x 0.8\")"),
        ("Weight", "110 g (3.9 oz)"),
        ("Reader Ports", "1x RJ12 port (최대 100m)"),
        ("Relay Output", "1x NO/NC (12-24V DC, 2A max)"),
        ("Sensor Input", "1x Door Position Sensor (DPS)"),
        ("Ethernet", "1x GbE RJ45 (network uplink)"),
        ("Power Method", "PoE (802.3af, 최대 6W)"),
        ("Operating Temperature", "-10 to 40°C (14 to 104°F)"),
        ("Mounting", "Wall"),
        ("Material", "Polycarbonate"),
    ]),
)

for filename, content in pages.items():
    with open(f"{OUT_DIR}/{filename}", "w") as f:
        f.write(content)

print("✅ Door Access Batch 1 완료: Reader Pro, Reader Flex, Access Ultra, Door Hub, Door Hub Mini")
