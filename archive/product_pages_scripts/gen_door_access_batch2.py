"""Door Access Batch 2: Enterprise Access Hub / Intercom Viewer / G6 Entry / Magnetic Lock / Access Button

엔터프라이즈 허브, 인터콤, 카메라, 락, 버튼 5개.
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
# 1) UniFi Enterprise Access Hub
# ============================================================
pages["Unifi Supply - Enterprise Access Hub.dc.html"] = assemble(
    hero(
        "Enterprise Access Hub",
        "32도어 엔터프라이즈 컨트롤러 — 최대 32개 Reader와<br>32개 도어 락을 중앙 관리하는 대규모 액세스 솔루션.",
        "assets/ua-enterprise-hub/ua-enterprise-hub_01-hero-front.png",
        "Enterprise Access Hub",
    ),
    why_section(
        "Why Enterprise Access Hub",
        "32도어 동시 관리,<br>대규모 빌딩,<br>PoE++ 전원",
        "대형 빌딩, 캠퍼스, 산업 시설에 최적화된 32도어 컨트롤러로, 최대 32개의 UniFi Reader를 연결해 중앙에서 통합 관리합니다.",
        [
            ("32개 리더 연결,<br>32개 도어 관리",
             "최대 32개의 UniFi Reader를 연결해 각각 독립적인 액세스 정책으로 32개 도어를 제어할 수 있습니다."),
            ("32개 릴레이 출력,<br>센서 입력 32개",
             "각 도어마다 NO/NC 릴레이 출력과 도어 센서(DPS) 입력을 제공해 락 제어와 문 상태 모니터링을 동시에 처리합니다."),
            ("PoE++ 전원,<br>백업 24V DC",
             "PoE++(802.3bt) 케이블로 고전력을 공급하며, 별도 24V DC 입력으로 백업 전원을 연결할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/ua-enterprise-hub/ua-enterprise-hub_02-diagram.png",
        "Enterprise Access Hub 구성",
        "32x Reader 포트,<br>32x 릴레이 출력,<br>19\" 랙마운트",
        "32개의 Reader 포트(RJ12)와 32개의 릴레이 출력 터미널 블록을 갖추고 있으며, 각 포트는 최대 100m 거리의 Reader를 지원합니다.<br>19인치 랙마운트(1U) 또는 벽면 마운트로 설치 가능하며, 금속 인클로저로 내구성을 보장합니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "440 x 305 x 44 mm (17.3 x 12.0 x 1.7\") — 1U rack"),
        ("Weight", "3.2 kg (7.1 lb)"),
        ("Reader Ports", "32x RJ12 ports (최대 100m per reader)"),
        ("Relay Outputs", "32x NO/NC (12-24V DC, 2A max per relay)"),
        ("Sensor Inputs", "32x Door Position Sensor (DPS)"),
        ("Ethernet", "2x GbE RJ45 (network uplink, redundant)"),
        ("Power Method", "PoE++ (802.3bt, 최대 60W) + 24V DC backup input"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Mounting", "19\" rack (1U), Wall"),
        ("Material", "Metal enclosure"),
    ]),
)

# ============================================================
# 2) UniFi Intercom Viewer
# ============================================================
pages["Unifi Supply - Intercom Viewer.dc.html"] = assemble(
    hero(
        "Intercom Viewer",
        "7인치 터치 인터콤 — 영상 통화, 원격 도어 오픈,<br>방문자 기록을 하나로 통합한 실내 모니터.",
        "assets/ua-intercom-viewer/ua-intercom-viewer_01-hero-front.png",
        "Intercom Viewer",
    ),
    why_section(
        "Why Intercom Viewer",
        "7\" 터치스크린,<br>영상 통화,<br>원격 도어 오픈",
        "7인치 터치스크린으로 방문자와 영상 통화를 하고, 원격으로 도어를 열거나 방문자 기록을 확인할 수 있는 실내 모니터입니다.",
        [
            ("7인치 터치스크린,<br>1024x600 해상도",
             "7인치 IPS 터치스크린(1024x600)으로 방문자의 얼굴을 선명하게 보고, 직관적인 터치 인터페이스로 조작합니다."),
            ("영상 통화,<br>양방향 오디오",
             "G6 Entry나 다른 UniFi Intercom 기기와 양방향 오디오/비디오 통화를 지원하며, 원격에서도 모바일 앱으로 응답할 수 있습니다."),
            ("원격 도어 오픈,<br>방문자 기록",
             "터치 한 번으로 도어 락을 원격 해제하고, 방문자 기록(스냅샷, 시간)을 UniFi Access와 통합 관리합니다."),
        ],
    ),
    design_section(
        "assets/ua-intercom-viewer/ua-intercom-viewer_02-diagram.png",
        "Intercom Viewer 설치",
        "PoE 전원,<br>벽면/테이블 마운트,<br>알루미늄 합금",
        "PoE(802.3af) 케이블로 전원과 네트워크를 동시 공급하며, 벽면 또는 테이블 스탠드(별도 구매)로 설치할 수 있습니다.<br>알루미늄 합금 인클로저로 내구성을 보장하며, -10~40°C 실내 환경에서 작동합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "185 x 120 x 15 mm (7.3 x 4.7 x 0.6\")"),
        ("Weight", "350 g (12.3 oz)"),
        ("Display", "7\" IPS touchscreen, 1024x600 resolution"),
        ("Camera", "2 MP, 1080p video"),
        ("Audio", "Built-in speaker & microphone (양방향)"),
        ("Connectivity", "1x GbE RJ45 (PoE)"),
        ("Power Method", "PoE (802.3af, 최대 8W)"),
        ("Operating Temperature", "-10 to 40°C (14 to 104°F)"),
        ("Mounting", "Wall (포함), Table stand (별도 구매)"),
        ("Material", "Aluminum alloy, Glass"),
    ]),
)

# ============================================================
# 3) UniFi G6 Entry
# ============================================================
pages["Unifi Supply - G6 Entry.dc.html"] = assemble(
    hero(
        "G6 Entry",
        "비디오 인터콤 — 5MP 카메라, 양방향 오디오, IP65 방수,<br>NFC/Bluetooth 리더를 통합한 출입구 인터콤.",
        "assets/g6-entry/g6-entry_01-hero-front.png",
        "G6 Entry",
    ),
    why_section(
        "Why G6 Entry",
        "5MP 카메라,<br>NFC/BLE 리더,<br>IP65 방수",
        "출입구에 필요한 모든 기능을 하나로 통합 — 5MP 카메라로 방문자를 촬영하고, NFC/Bluetooth로 인증하며, 양방향 오디오로 대화합니다.",
        [
            ("5MP 카메라,<br>나이트 비전",
             "5MP 해상도(2688x1520)와 적외선 LED로 낮과 밤 모두 선명한 영상을 제공하며, 120° 시야각으로 출입구를 넓게 커버합니다."),
            ("NFC + Bluetooth<br>리더 통합",
             "13.56MHz NFC 카드와 Bluetooth 모바일 키를 인식해 방문자와 거주자 모두를 인증하며, UniFi Access와 통합 관리됩니다."),
            ("양방향 오디오,<br>IP65 방수",
             "내장 스피커와 마이크로 방문자와 실시간 대화가 가능하며, IP65 방수/방진 등급으로 옥외 설치에 적합합니다."),
        ],
    ),
    design_section(
        "assets/g6-entry/g6-entry_02-diagram.png",
        "G6 Entry 구성",
        "PoE 전원,<br>릴레이 출력,<br>벽면 마운트",
        "PoE(802.3af) 케이블로 전원과 네트워크를 동시 공급하며, 내장 릴레이 출력으로 도어 락을 직접 제어할 수 있습니다.<br>벽면 또는 표면 마운트(별도 액세서리)로 설치 가능하며, 알루미늄 합금 인클로저로 내구성을 보장합니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "135 x 88 x 28 mm (5.3 x 3.5 x 1.1\")"),
        ("Weight", "380 g (13.4 oz)"),
        ("Camera", "5 MP (2688x1520), 120° FOV, IR night vision"),
        ("Audio", "Built-in speaker & microphone (양방향)"),
        ("Access Methods", "NFC (13.56 MHz ISO/IEC 14443 Type A/B), Bluetooth Low Energy (BLE 5.0)"),
        ("Relay Output", "1x NO/NC (12-24V DC, 2A max)"),
        ("LED & Feedback", "Multi-color LED ring, Touch feedback"),
        ("Power Method", "PoE (802.3af, 최대 12W)"),
        ("Weatherproofing", "IP65"),
        ("Operating Temperature", "-20 to 50°C (-4 to 122°F)"),
        ("Mounting", "Wall, Surface (별도 마운트 사용 가능)"),
        ("Material", "Aluminum alloy, Polycarbonate"),
    ]),
)

# ============================================================
# 4) UniFi Magnetic Lock
# ============================================================
pages["Unifi Supply - Magnetic Lock.dc.html"] = assemble(
    hero(
        "Magnetic Lock",
        "전자식 마그네틱 락 — 12V/24V 듀얼 전압, 600lbs(272kg)<br>보유력을 갖춘 UniFi Access 전용 도어 락.",
        "assets/ua-magnetic-lock/ua-magnetic-lock_01-hero-front.png",
        "Magnetic Lock",
    ),
    why_section(
        "Why Magnetic Lock",
        "600lbs 보유력,<br>12V/24V 듀얼,<br>실내외 설치",
        "UniFi Door Hub 또는 Access Ultra의 릴레이 출력에 직접 연결해 도어를 잠그고 여는 전자식 마그네틱 락입니다.",
        [
            ("600lbs (272kg)<br>보유력",
             "600파운드(272kg)의 보유력으로 일반 사무실 도어부터 중형 출입문까지 안전하게 잠급니다."),
            ("12V/24V<br>듀얼 전압 지원",
             "12V 또는 24V DC 전원을 모두 지원해 다양한 UniFi Door Hub 설정과 호환됩니다."),
            ("알루미늄 합금,<br>실내외 설치",
             "알루미늄 합금 인클로저로 내구성을 보장하며, -40~55°C 작동 온도 범위로 실내외 모두 설치 가능합니다."),
        ],
    ),
    design_section(
        "assets/ua-magnetic-lock/ua-magnetic-lock_02-diagram.png",
        "Magnetic Lock 구성",
        "NO/NC 릴레이 연결,<br>도어 센서 통합,<br>LED 상태 표시",
        "UniFi Door Hub의 릴레이 출력에 직접 연결하며, 도어 센서(DPS)와 LED 상태 표시등을 내장해 문 열림/잠김 상태를 실시간으로 확인할 수 있습니다.<br>프레임 마운트 하드웨어가 포함되어 있습니다.",
    ),
    tech_specs_section([
        ("Dimensions", "203 x 38 x 25 mm (8.0 x 1.5 x 1.0\")"),
        ("Weight", "1.2 kg (2.6 lb)"),
        ("Holding Force", "600 lbs (272 kg)"),
        ("Power Input", "12V DC or 24V DC (최대 500mA @ 12V, 250mA @ 24V)"),
        ("Relay Type", "NO (Normally Open) — 전원 공급 시 잠김"),
        ("Sensor Integration", "Door Position Sensor (DPS) compatible"),
        ("LED Indicator", "Lock status LED"),
        ("Operating Temperature", "-40 to 55°C (-40 to 131°F)"),
        ("Mounting", "Frame mount (하드웨어 포함)"),
        ("Material", "Aluminum alloy"),
    ]),
)

# ============================================================
# 5) UniFi Access Button
# ============================================================
pages["Unifi Supply - Access Button.dc.html"] = assemble(
    hero(
        "Access Button",
        "원터치 출구 버튼 — 실내에서 카드 없이 도어를 열 수 있는<br>Request-to-Exit(REX) 버튼.",
        "assets/ua-button/ua-button_01-hero-front.png",
        "Access Button",
    ),
    why_section(
        "Why Access Button",
        "원터치 출구,<br>카드 인증 불필요,<br>NO/NC 출력",
        "실내에서 카드 인증 없이 버튼 한 번으로 도어를 열 수 있는 Request-to-Exit(REX) 버튼으로, UniFi Door Hub의 센서 입력에 연결합니다.",
        [
            ("원터치 출구,<br>카드 불필요",
             "실내에서 나갈 때 NFC 카드나 모바일 키 없이 버튼 한 번으로 도어를 열 수 있습니다."),
            ("NO/NC 출력,<br>Door Hub 연결",
             "NO(Normally Open) 또는 NC(Normally Closed) 출력을 지원해 UniFi Door Hub의 센서 입력에 직접 연결합니다."),
            ("LED 피드백,<br>컴팩트한 디자인",
             "버튼 누름 시 LED 피드백을 제공하며, 벽면 마운트로 출입구 근처에 설치합니다."),
        ],
    ),
    design_section(
        "assets/ua-button/ua-button_02-diagram.png",
        "Access Button 구성",
        "12-24V DC 전원,<br>NO/NC 출력,<br>벽면 마운트",
        "12-24V DC 전원을 공급하며(Door Hub의 보조 전원 출력 활용 가능), NO/NC 출력으로 Door Hub의 센서 입력에 연결합니다.<br>벽면 마운트 하드웨어가 포함되어 있으며, 폴리카보네이트 인클로저로 제작됩니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "86 x 86 x 20 mm (3.4 x 3.4 x 0.8\")"),
        ("Weight", "80 g (2.8 oz)"),
        ("Button Type", "Push button, LED feedback"),
        ("Output", "NO/NC contact (dry contact)"),
        ("Power Input", "12-24V DC (최대 100mA)"),
        ("Operating Temperature", "-10 to 40°C (14 to 104°F)"),
        ("Mounting", "Wall (하드웨어 포함)"),
        ("Material", "Polycarbonate"),
    ]),
)

for filename, content in pages.items():
    with open(f"{OUT_DIR}/{filename}", "w") as f:
        f.write(content)

print("✅ Door Access Batch 2 완료: Enterprise Access Hub, Intercom Viewer, G6 Entry, Magnetic Lock, Access Button")
