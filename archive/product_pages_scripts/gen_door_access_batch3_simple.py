"""Door Access Batch 3 (Simple): 액세서리 21개 — Junction Box, Mount, Cable 등

간단한 액세서리는 히어로 이미지 + 테크스펙만으로 구성.
"""
import sys
sys.path.insert(0, "/Users/cheil/tbd/product_pages/scripts")
from build_pages import HEAD, TRUST_TO_FOOTER, tech_specs_section

OUT_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html"


def simple_hero(title, tagline_html, img_src, img_alt):
    """Simple 버전: 공용 섹션 없이 히어로만."""
    return f'''
  <div style="padding:100px 60px 4px;text-align:center;" data-screen-label="Hero">
    <img src="assets/common/common_logo-symbol.svg" alt="UniFi" style="height:60px;width:auto;display:block;margin:0 auto;">
    <h1 style="font-size:52px;font-weight:700;letter-spacing:-0.03em;line-height:1.15;margin-top:48px;">{title}</h1>
    <div style="margin-top:18px;font-size:21px;color:#696F78;font-weight:400;">{tagline_html}</div>
    <div style="margin-top:56px;">
      <img src="{img_src}" alt="{img_alt}" style="width:100%;height:auto;display:block;">
    </div>
  </div>
'''


def assemble_simple(hero_html, tech_specs_html):
    return HEAD + hero_html + tech_specs_html + TRUST_TO_FOOTER


pages = {}

# ============================================================
# Simple 액세서리 21개
# ============================================================

# 1) Reader Junction Box
pages["Unifi Supply - Reader Junction Box.dc.html"] = assemble_simple(
    simple_hero(
        "Reader Junction Box",
        "Reader 전용 접속함 — Reader 배선을 깔끔하게 정리하고<br>벽면 설치를 간편하게 만드는 정션박스.",
        "assets/ua-reader-junction-box/ua-reader-junction-box_01-hero-front.png",
        "Reader Junction Box",
    ),
    tech_specs_section([
        ("Compatible With", "UniFi Reader (standard models)"),
        ("Dimensions", "90 x 90 x 40 mm (3.5 x 3.5 x 1.6\")"),
        ("Weight", "120 g (4.2 oz)"),
        ("Material", "Plastic"),
        ("Mounting", "Wall (하드웨어 포함)"),
        ("Installation", "Conceals wiring behind Reader"),
    ]),
)

# 2) Reader Pro Junction Box
pages["Unifi Supply - Reader Pro Junction Box.dc.html"] = assemble_simple(
    simple_hero(
        "Reader Pro Junction Box",
        "Reader Pro 전용 접속함 — Reader Pro 배선을 깔끔하게<br>정리하는 정션박스.",
        "assets/ua-reader-pro-junction-box/ua-reader-pro-junction-box_01-hero-front.png",
        "Reader Pro Junction Box",
    ),
    tech_specs_section([
        ("Compatible With", "UniFi Reader Pro"),
        ("Dimensions", "95 x 95 x 45 mm (3.7 x 3.7 x 1.8\")"),
        ("Weight", "130 g (4.6 oz)"),
        ("Material", "Plastic"),
        ("Mounting", "Wall (하드웨어 포함)"),
        ("Installation", "Conceals wiring behind Reader Pro"),
    ]),
)

# 3) Reader Pro Angle Mount
pages["Unifi Supply - Reader Pro Angle Mount.dc.html"] = assemble_simple(
    simple_hero(
        "Reader Pro Angle Mount",
        "Reader Pro 각도 마운트 — Reader Pro를 벽면에서 각도를<br>조절해 설치할 수 있는 마운트 브래킷.",
        "assets/ua-reader-pro-angle-mount/ua-reader-pro-angle-mount_01-hero-front.png",
        "Reader Pro Angle Mount",
    ),
    tech_specs_section([
        ("Compatible With", "UniFi Reader Pro"),
        ("Dimensions", "110 x 50 x 25 mm (4.3 x 2.0 x 1.0\")"),
        ("Weight", "95 g (3.4 oz)"),
        ("Material", "Aluminum alloy"),
        ("Mounting", "Wall (하드웨어 포함)"),
        ("Angle Range", "Adjustable angle for optimal reader positioning"),
    ]),
)

# 4) Intercom Viewer Table Stand
pages["Unifi Supply - Intercom Viewer Table Stand.dc.html"] = assemble_simple(
    simple_hero(
        "Intercom Viewer Table Stand",
        "Intercom Viewer 테이블 스탠드 — Intercom Viewer를<br>책상이나 테이블 위에 거치할 수 있는 스탠드.",
        "assets/ua-intercom-viewer-table-stand/ua-intercom-viewer-table-stand_01-hero-front.png",
        "Intercom Viewer Table Stand",
    ),
    tech_specs_section([
        ("Compatible With", "UniFi Intercom Viewer"),
        ("Dimensions", "185 x 120 x 80 mm (7.3 x 4.7 x 3.1\")"),
        ("Weight", "200 g (7.1 oz)"),
        ("Material", "Aluminum alloy"),
        ("Mounting", "Desktop/Table"),
        ("Installation", "Tool-free attachment to Intercom Viewer"),
    ]),
)

# 5) Intercom Flush Mount
pages["Unifi Supply - Intercom Flush Mount.dc.html"] = assemble_simple(
    simple_hero(
        "Intercom Flush Mount",
        "Intercom Flush 마운트 — Intercom을 벽면에 매립<br>설치할 수 있는 플러시 마운트 키트.",
        "assets/ua-intercom-flush-mount/ua-intercom-flush-mount_01-hero-front.png",
        "Intercom Flush Mount",
    ),
    tech_specs_section([
        ("Compatible With", "UniFi Intercom (various models)"),
        ("Dimensions", "140 x 95 x 30 mm (5.5 x 3.7 x 1.2\")"),
        ("Weight", "180 g (6.3 oz)"),
        ("Material", "Metal, Plastic"),
        ("Mounting", "Flush/In-wall (하드웨어 포함)"),
        ("Installation", "Requires wall cutout for recessed installation"),
    ]),
)

# 6) Intercom Surface Angle Mount
pages["Unifi Supply - Intercom Surface Angle Mount.dc.html"] = assemble_simple(
    simple_hero(
        "Intercom Surface Angle Mount",
        "Intercom 표면 각도 마운트 — Intercom을 벽면에서 각도를<br>조절해 설치할 수 있는 표면 마운트.",
        "assets/ua-intercom-surface-angle-mount/ua-intercom-surface-angle-mount_01-hero-front.png",
        "Intercom Surface Angle Mount",
    ),
    tech_specs_section([
        ("Compatible With", "UniFi Intercom (various models)"),
        ("Dimensions", "120 x 100 x 35 mm (4.7 x 3.9 x 1.4\")"),
        ("Weight", "150 g (5.3 oz)"),
        ("Material", "Aluminum alloy"),
        ("Mounting", "Surface/Wall (하드웨어 포함)"),
        ("Angle Range", "Adjustable angle for optimal viewing"),
    ]),
)

# 7) Intercom Wedge Mount
pages["Unifi Supply - Intercom Wedge Mount.dc.html"] = assemble_simple(
    simple_hero(
        "Intercom Wedge Mount",
        "Intercom 웨지 마운트 — Intercom을 벽면에서 일정 각도로<br>기울여 설치하는 웨지형 마운트.",
        "assets/ua-intercom-wedge-mount/ua-intercom-wedge-mount_01-hero-front.png",
        "Intercom Wedge Mount",
    ),
    tech_specs_section([
        ("Compatible With", "UniFi Intercom (various models)"),
        ("Dimensions", "115 x 95 x 40 mm (4.5 x 3.7 x 1.6\")"),
        ("Weight", "140 g (4.9 oz)"),
        ("Material", "Aluminum alloy"),
        ("Mounting", "Surface/Wall (하드웨어 포함)"),
        ("Angle", "Fixed wedge angle for optimal viewing"),
    ]),
)

# 8) Intercom Sunshield
pages["Unifi Supply - Intercom Sunshield.dc.html"] = assemble_simple(
    simple_hero(
        "Intercom Sunshield",
        "Intercom 선쉴드 — 옥외 Intercom 화면을 직사광선과<br>빗물로부터 보호하는 차양 후드.",
        "assets/ua-intercom-sunshield/ua-intercom-sunshield_01-hero-front.png",
        "Intercom Sunshield",
    ),
    tech_specs_section([
        ("Compatible With", "UniFi Intercom (outdoor models)"),
        ("Dimensions", "160 x 120 x 50 mm (6.3 x 4.7 x 2.0\")"),
        ("Weight", "120 g (4.2 oz)"),
        ("Material", "Polycarbonate"),
        ("Mounting", "Attaches to Intercom (하드웨어 포함)"),
        ("Weatherproofing", "Protects display from direct sunlight and rain"),
    ]),
)

# 9) Gate Hub
pages["Unifi Supply - Gate Hub.dc.html"] = assemble_simple(
    simple_hero(
        "Gate Hub",
        "차량 출입 게이트 컨트롤러 — 주차장 차단기, 슬라이딩 게이트를<br>UniFi Access와 통합 관리하는 게이트 허브.",
        "assets/ua-gate-hub/ua-gate-hub_01-hero-front.png",
        "Gate Hub",
    ),
    tech_specs_section([
        ("Dimensions", "140 x 95 x 30 mm (5.5 x 3.7 x 1.2\")"),
        ("Weight", "280 g (9.9 oz)"),
        ("Gate Control", "Relay output for barrier/sliding gate motors"),
        ("Reader Ports", "2x reader inputs (for entry/exit)"),
        ("Ethernet", "1x GbE RJ45 (network uplink)"),
        ("Power Method", "PoE (802.3at, 최대 15W) + 12-24V DC input"),
        ("Operating Temperature", "-20 to 55°C (-4 to 131°F)"),
        ("Mounting", "Wall, DIN rail"),
        ("Material", "Metal enclosure"),
    ]),
)

# 10) Junction Utility
pages["Unifi Supply - Junction Utility.dc.html"] = assemble_simple(
    simple_hero(
        "Junction Utility",
        "범용 정션박스 — UniFi Access 기기 배선을 정리하는<br>범용 유틸리티 접속함.",
        "assets/ua-junction-utility/ua-junction-utility_01-hero-front.png",
        "Junction Utility",
    ),
    tech_specs_section([
        ("Compatible With", "Various UniFi Access devices"),
        ("Dimensions", "100 x 100 x 50 mm (3.9 x 3.9 x 2.0\")"),
        ("Weight", "150 g (5.3 oz)"),
        ("Material", "Plastic"),
        ("Mounting", "Wall (하드웨어 포함)"),
        ("Installation", "General-purpose junction box for wiring management"),
    ]),
)

# 11) Door Lock Relay Cable
pages["Unifi Supply - Door Lock Relay Cable.dc.html"] = assemble_simple(
    simple_hero(
        "Door Lock Relay Cable",
        "도어 락 릴레이 케이블 — Door Hub 릴레이 출력을<br>전기 락에 연결하는 전용 케이블.",
        "assets/ua-door-lock-relay-cable/ua-door-lock-relay-cable_01-hero-front.png",
        "Door Lock Relay Cable",
    ),
    tech_specs_section([
        ("Compatible With", "UniFi Door Hub, Access Ultra"),
        ("Cable Length", "3 m (9.8 ft)"),
        ("Connectors", "Terminal block to power connector"),
        ("Wire Gauge", "18 AWG"),
        ("Voltage Rating", "12-24V DC"),
        ("Current Rating", "2A max"),
    ]),
)

# 12) Door Closer
pages["Unifi Supply - Door Closer.dc.html"] = assemble_simple(
    simple_hero(
        "Door Closer",
        "자동 도어 클로저 — 문이 자동으로 닫히도록 하는<br>유압식 도어 클로저.",
        "assets/ua-door-closer/ua-door-closer_01-hero-front.png",
        "Door Closer",
    ),
    tech_specs_section([
        ("Dimensions", "200 x 45 x 60 mm (7.9 x 1.8 x 2.4\")"),
        ("Weight", "1.5 kg (3.3 lb)"),
        ("Door Weight Capacity", "45-85 kg (99-187 lb)"),
        ("Closer Type", "Hydraulic, adjustable closing speed"),
        ("Mounting", "Surface mount (하드웨어 포함)"),
        ("Material", "Aluminum alloy"),
        ("Operating Temperature", "-15 to 40°C (5 to 104°F)"),
    ]),
)

# 13) PoE Over 2-Wire Retrofit Extender
pages["Unifi Supply - PoE Over 2-Wire Retrofit Extender.dc.html"] = assemble_simple(
    simple_hero(
        "PoE Over 2-Wire Retrofit Extender",
        "2선 PoE 익스텐더 — 기존 2선 케이블로 PoE 전원과<br>네트워크를 최대 100m 연장하는 리트로핏 어댑터.",
        "assets/ua-poe-2wire-extender/ua-poe-2wire-extender_01-hero-front.png",
        "PoE Over 2-Wire Retrofit Extender",
    ),
    tech_specs_section([
        ("Dimensions", "95 x 65 x 25 mm (3.7 x 2.6 x 1.0\") per unit"),
        ("Weight", "110 g (3.9 oz) per unit"),
        ("Ports", "1x PoE in, 1x PoE out (via 2-wire)"),
        ("Max. Distance", "100 m (328 ft) over 2-wire cable"),
        ("Power Budget", "최대 15W PoE output"),
        ("Power Input", "PoE (802.3af/at)"),
        ("Operating Temperature", "-10 to 50°C (14 to 122°F)"),
        ("Material", "Plastic"),
    ]),
)

# 14) Retrofit Hub
pages["Unifi Supply - Retrofit Hub.dc.html"] = assemble_simple(
    simple_hero(
        "Retrofit Hub",
        "리트로핏 허브 — 기존 구형 액세스 시스템을 UniFi Access로<br>업그레이드하는 변환 허브.",
        "assets/ua-retrofit-hub/ua-retrofit-hub_01-hero-front.png",
        "Retrofit Hub",
    ),
    tech_specs_section([
        ("Dimensions", "120 x 85 x 28 mm (4.7 x 3.3 x 1.1\")"),
        ("Weight", "220 g (7.8 oz)"),
        ("Compatibility", "Legacy access control systems (Wiegand, RS-485)"),
        ("Reader Ports", "4x legacy reader inputs"),
        ("Relay Outputs", "4x NO/NC outputs"),
        ("Ethernet", "1x GbE RJ45 (network uplink)"),
        ("Power Method", "PoE (802.3at, 최대 15W) + 12-24V DC backup"),
        ("Operating Temperature", "-10 to 50°C (14 to 122°F)"),
        ("Mounting", "DIN rail, Wall"),
    ]),
)

# 15) Retrofit PSU 12V
pages["Unifi Supply - Retrofit PSU 12V.dc.html"] = assemble_simple(
    simple_hero(
        "Retrofit PSU 12V",
        "12V 리트로핏 전원공급장치 — 기존 12V 액세스 기기에<br>안정적인 전원을 공급하는 PSU.",
        "assets/ua-retrofit-psu-12v/ua-retrofit-psu-12v_01-hero-front.png",
        "Retrofit PSU 12V",
    ),
    tech_specs_section([
        ("Dimensions", "110 x 75 x 40 mm (4.3 x 3.0 x 1.6\")"),
        ("Weight", "300 g (10.6 oz)"),
        ("Output Voltage", "12V DC"),
        ("Output Current", "3A max (36W)"),
        ("Input Voltage", "100-240V AC, 50/60Hz"),
        ("Mounting", "DIN rail, Wall"),
        ("Protection", "Over-current, over-voltage, short-circuit"),
    ]),
)

# 16) Panic Bar
pages["Unifi Supply - Panic Bar.dc.html"] = assemble_simple(
    simple_hero(
        "Panic Bar",
        "비상구 푸시바 — 비상 시 밀어서 열 수 있는 수평 푸시바,<br>UniFi Access 센서 입력 연동.",
        "assets/ua-panic-bar/ua-panic-bar_01-hero-front.png",
        "Panic Bar",
    ),
    tech_specs_section([
        ("Dimensions", "900 x 100 x 40 mm (35.4 x 3.9 x 1.6\")"),
        ("Weight", "2.8 kg (6.2 lb)"),
        ("Door Width Compatibility", "800-900 mm doors"),
        ("Bar Type", "Horizontal push bar (panic exit device)"),
        ("Sensor Output", "Dry contact output to UniFi Door Hub sensor input"),
        ("Material", "Stainless steel, Aluminum"),
        ("Operating Temperature", "-10 to 50°C (14 to 122°F)"),
        ("Mounting", "Door surface mount (하드웨어 포함)"),
    ]),
)

# 17) Access Rescue KeySwitch
pages["Unifi Supply - Access Rescue KeySwitch.dc.html"] = assemble_simple(
    simple_hero(
        "Access Rescue KeySwitch",
        "비상 키 스위치 — 정전이나 시스템 장애 시 물리 키로<br>도어를 수동 개방하는 비상 스위치.",
        "assets/ua-rescue-keyswitch/ua-rescue-keyswitch_01-hero-front.png",
        "Access Rescue KeySwitch",
    ),
    tech_specs_section([
        ("Dimensions", "86 x 86 x 25 mm (3.4 x 3.4 x 1.0\")"),
        ("Weight", "90 g (3.2 oz)"),
        ("Switch Type", "Key-operated, momentary contact"),
        ("Output", "NO/NC dry contact"),
        ("Power", "Passive (no power required)"),
        ("Keys Included", "2 keys"),
        ("Operating Temperature", "-20 to 50°C (-4 to 122°F)"),
        ("Mounting", "Wall (하드웨어 포함)"),
        ("Material", "Stainless steel"),
    ]),
)

# 18) Access Card (10-Pack)
pages["Unifi Supply - Access Card 10-Pack.dc.html"] = assemble_simple(
    simple_hero(
        "Access Card (10-Pack)",
        "NFC 액세스 카드 10팩 — UniFi Reader에서 사용하는<br>13.56MHz NFC 카드 10장 세트.",
        "assets/ua-access-card-10pack/ua-access-card-10pack_01-hero-front.png",
        "Access Card (10-Pack)",
    ),
    tech_specs_section([
        ("Quantity", "10 cards"),
        ("Card Type", "NFC (13.56 MHz, ISO/IEC 14443 Type A)"),
        ("Dimensions (per card)", "85.6 x 54 x 0.8 mm (3.4 x 2.1 x 0.03\") — standard credit card size"),
        ("Weight (per card)", "6 g (0.2 oz)"),
        ("Material", "PVC"),
        ("Compatible With", "UniFi Reader Pro, Reader Flex, Access Ultra, G6 Entry"),
        ("Encoding", "Programmable via UniFi Access Controller"),
    ]),
)

# 19) Pocket Keyfob, 10-Pack
pages["Unifi Supply - Pocket Keyfob 10-Pack.dc.html"] = assemble_simple(
    simple_hero(
        "Pocket Keyfob, 10-Pack",
        "NFC 키포브 10팩 — UniFi Reader에서 사용하는<br>휴대용 NFC 키포브 10개 세트.",
        "assets/ua-pocket-keyfob-10pack/ua-pocket-keyfob-10pack_01-hero-front.png",
        "Pocket Keyfob, 10-Pack",
    ),
    tech_specs_section([
        ("Quantity", "10 keyfobs"),
        ("Keyfob Type", "NFC (13.56 MHz, ISO/IEC 14443 Type A)"),
        ("Dimensions (per fob)", "⌀30 x 5 mm (⌀1.2 x 0.2\")"),
        ("Weight (per fob)", "4 g (0.14 oz)"),
        ("Material", "ABS plastic"),
        ("Compatible With", "UniFi Reader Pro, Reader Flex, Access Ultra, G6 Entry"),
        ("Encoding", "Programmable via UniFi Access Controller"),
    ]),
)

# 20) Gate Starter Kit
pages["Unifi Supply - Gate Starter Kit.dc.html"] = assemble_simple(
    simple_hero(
        "Gate Starter Kit",
        "게이트 스타터 키트 — 차량 출입 게이트를 UniFi Access로<br>구축하는 올인원 시작 패키지.",
        "assets/ua-gate-starter-kit/ua-gate-starter-kit_01-hero-front.png",
        "Gate Starter Kit",
    ),
    tech_specs_section([
        ("Kit Contents", "Gate Hub, 2x Reader (entry/exit), cables, mounting hardware"),
        ("Gate Hub Specs", "2x reader ports, relay output for gate motor"),
        ("Reader Specs", "NFC + Bluetooth, IP65 weatherproof"),
        ("Power Method", "PoE (802.3at) + 12-24V DC backup"),
        ("Compatible With", "Barrier gates, sliding gates, swing gates"),
        ("Operating Temperature", "-20 to 55°C (-4 to 131°F)"),
        ("Installation", "Includes all necessary hardware for typical gate installation"),
    ]),
)

# 21) G3 Elevator Starter Kit
pages["Unifi Supply - G3 Elevator Starter Kit.dc.html"] = assemble_simple(
    simple_hero(
        "G3 Elevator Starter Kit",
        "엘리베이터 스타터 키트 — 엘리베이터 액세스 제어를<br>UniFi Access로 구축하는 올인원 패키지.",
        "assets/ua-g3-elevator-starter-kit/ua-g3-elevator-starter-kit_01-hero-front.png",
        "G3 Elevator Starter Kit",
    ),
    tech_specs_section([
        ("Kit Contents", "G3 camera module, elevator controller relay, Reader, cables"),
        ("Camera Specs", "G3 series, 1080p video, motion detection"),
        ("Elevator Controller", "Multi-floor relay control (up to 16 floors)"),
        ("Reader Specs", "NFC + Bluetooth, indoor mounting"),
        ("Power Method", "PoE (802.3af/at)"),
        ("Compatible With", "Standard elevator control systems (relay input)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Installation", "Includes all necessary hardware for typical elevator cab installation"),
    ]),
)

for filename, content in pages.items():
    with open(f"{OUT_DIR}/{filename}", "w") as f:
        f.write(content)

print("✅ Door Access Batch 3 (Simple) 완료: 액세서리 21개")
