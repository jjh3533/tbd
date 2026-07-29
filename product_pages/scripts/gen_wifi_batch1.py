"""WiFi Batch 1: AC Pro / Building Bridge XG / Device Bridge / Device Bridge Switch

오래된 WiFi 5 제품(AC Pro)부터 특수목적 브리지 제품군까지 4개.
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
# 1) UniFi AC Pro
# ============================================================
pages["Unifi Supply - AC Pro.dc.html"] = assemble(
    hero(
        "AC Pro",
        "250개 이상 기기를 동시접속하는<br>검증된 WiFi 5 듀얼밴드 액세스포인트.",
        "assets/uap-ac-pro/uap-ac-pro_01-hero-front.png",
        "AC Pro",
    ),
    why_section(
        "Why AC Pro",
        "250대 이상 동시접속,<br>넓은 커버리지로<br>검증된 안정성",
        "WiFi 5 세대의 검증된 안정성과 3x3 MU-MIMO로 사무실, 카페, 소규모 매장에 충분한 성능을 제공합니다.",
        [
            ("WiFi 5 듀얼밴드,<br>3x3 MU-MIMO",
             "5GHz 1.3Gbps, 2.4GHz 450Mbps의 안정적인 듀얼밴드 연결을 3x3 공간 스트림으로 제공합니다."),
            ("250대 이상<br>동시접속 지원",
             "사무실, 카페, 소규모 매장에서 250개 이상의 기기를 동시에 안정적으로 연결할 수 있습니다."),
            ("1,500 ft² 커버리지,<br>PoE 전원",
             "최대 140m²(1,500 ft²) 면적을 커버하며, PoE 케이블 하나로 전원과 네트워크를 동시에 공급받습니다."),
        ],
    ),
    design_section(
        "assets/uap-ac-pro/uap-ac-pro_02-diagram.png",
        "AC Pro 포트 구성",
        "2개의 기가비트<br>이더넷 포트로<br>확장 연결",
        "2개의 GbE RJ45 포트를 내장해 하나는 업링크로, 다른 하나는 유선 기기 연결용으로 활용할 수 있습니다.<br>천장이나 벽면 마운트 모두 지원하며, 별도 Pro Mount 액세서리로 설치 옵션을 확장할 수 있습니다.",
    ),
    tech_specs_section([
        ("Dimensions", "⌀196.7 x 35 mm (⌀7.7 x 1.4\")"),
        ("Weight", "350 g (12.4 oz), 450 g (15.9 oz) with mount"),
        ("Wi-Fi Standard", "WiFi 5 (802.11ac), 듀얼밴드 (5/2.4GHz)"),
        ("Spatial Streams", "6 (3x3 MU-MIMO per band)"),
        ("Max. Data Rate", "5GHz 1.3 Gbps (BW80) · 2.4GHz 450 Mbps (BW40)"),
        ("Coverage Area", "140 m² (1,500 ft²)"),
        ("Max. Client Count", "250+"),
        ("Ports", "(2) GbE RJ45 ports"),
        ("Power Method", "PoE (최대 9W, PoE 어댑터 포함, 44–57V DC)"),
        ("Operating Temperature", "-10 to 70°C (14 to 158°F)"),
        ("Mounting", "Ceiling, Wall (Pro Mount 별도 구매 가능)"),
    ]),
)

# ============================================================
# 2) UniFi Building Bridge XG 2-Pack
# ============================================================
pages["Unifi Supply - Building Bridge XG.dc.html"] = assemble(
    hero(
        "Building Bridge XG",
        "건물 간 500m 무선 브리징 — 60GHz 6Gbps 주 링크,<br>5GHz 백업 링크를 갖춘 2팩 포인트-투-포인트 세트.",
        "assets/ubb-xg/ubb-xg_01-hero-front.png",
        "Building Bridge XG",
    ),
    why_section(
        "Why Building Bridge XG",
        "건물 간 최대 500m,<br>60GHz 6Gbps<br>무선 백본",
        "건물 사이에 케이블을 깔 수 없을 때, 60GHz 무선으로 최대 6Gbps 속도의 네트워크 백본을 구축합니다.",
        [
            ("60GHz 주 링크 6Gbps,<br>5GHz 백업 866Mbps",
             "57-66GHz 대역 주 링크가 6Gbps 처리량을 제공하고, 악천후나 간섭 시 5GHz 백업 링크(866Mbps)로 자동 전환됩니다."),
            ("최대 500m 거리,<br>IPX6 방수",
             "최대 500m(1,640 ft) 거리까지 포인트-투-포인트 연결이 가능하며, IPX6 방수 등급으로 옥외 설치에 적합합니다."),
            ("GbE + 10G SFP+<br>업링크 포트",
             "1개의 기가비트 이더넷과 1개의 10G SFP+ 포트를 갖춰, 높은 처리량을 온전히 활용할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/ubb-xg/ubb-xg_02-diagram.png",
        "Building Bridge XG 구성",
        "2팩 세트로 제공,<br>벽면·폴 마운트<br>하드웨어 포함",
        "한 쌍(2개)이 세트로 제공되며, 각 유닛은 벽면 또는 지름 25-63.5mm 폴에 마운트할 수 있습니다.<br>200 km/h 풍속 하중(56N)을 견디는 스테인리스 마운트와 알루미늄 합금/폴리카보네이트 인클로저로 제작됩니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions (per unit)", "⌀191.8 x 59 mm (⌀7.6 x 2.3\")"),
        ("Weight (per unit)", "1.7 kg (3.8 lb) 기기, 2.9 kg (6.3 lb) with mount"),
        ("Wireless Bridge", "60GHz 주 링크 (57-66GHz, WiFi 5 PtP, 6 Gbps), 5GHz 백업 링크 (5150-5850MHz, 866.6 Mbps BW80)"),
        ("Max. Range", "500 m (1,640 ft)"),
        ("Antenna Gain", "21 dBi (60GHz), 14 dBi (5GHz)"),
        ("Ports", "(1) GbE RJ45, (1) 1/10G SFP+"),
        ("Power Method", "PoE++ Passive PoE (최대 29W, 48V DC ±10%, 어댑터 포함)"),
        ("Operating Temperature", "-40 to 55°C (-40 to 131°F)"),
        ("Weatherproofing", "IPX6"),
        ("Mounting", "Wall, Pole (1–2.5\" / 25–63.5 mm 폴 지름), 스테인리스 마운트 포함"),
    ]),
)

# ============================================================
# 3) UniFi Device Bridge
# ============================================================
pages["Unifi Supply - Device Bridge.dc.html"] = assemble(
    hero(
        "Device Bridge",
        "WiFi 5 무선 브리지 — 유선 네트워크가 닿지 않는 곳에<br>단일 기기를 무선으로 연결하는 클라이언트 브리지.",
        "assets/udb/udb_01-hero-front.png",
        "Device Bridge",
    ),
    why_section(
        "Why Device Bridge",
        "WiFi 없는 기기를<br>무선 네트워크에<br>연결",
        "유선 전용 기기(프린터, IP 카메라, POS 단말 등)를 UniFi AP가 제공하는 5GHz WiFi 네트워크에 무선으로 연결합니다.",
        [
            ("WiFi 5, 5GHz<br>866Mbps 브리지",
             "5GHz WiFi 5 (802.11ac) 네트워크에 2x2 MIMO로 연결해 최대 866Mbps 처리량을 제공합니다."),
            ("1개 GbE 포트,<br>단일 기기 연결",
             "1개의 기가비트 이더넷 포트로 유선 전용 기기 하나를 무선 네트워크에 브리징합니다."),
            ("외장 안테나 확장,<br>테이블·벽면 마운트",
             "내장 안테나(5dBi) 외에 RP-SMA 커넥터로 외장 옴니 안테나(4dBi, 360°x30°)를 연결할 수 있으며, 테이블이나 벽면에 설치 가능합니다."),
        ],
    ),
    design_section(
        "assets/udb/udb_02-diagram.png",
        "Device Bridge 구성",
        "AC 어댑터 또는<br>PoE 입력 지원,<br>신호 LED 4개",
        "100-240V AC 어댑터(포함) 또는 PoE 입력으로 전원을 공급받으며, 4개의 파란색 신호 LED와 1개의 상태 LED로 연결 상태를 표시합니다.<br>폴리카보네이트 인클로저, 팩토리 리셋 버튼 내장.",
    ),
    tech_specs_section([
        ("Dimensions", "130 x 55 x 34 mm (5.1 x 2.2 x 1.3\")"),
        ("Weight", "200 g (7.1 oz)"),
        ("Wireless Bridge", "WiFi 5 (802.11ac), 5GHz, 2x2 MIMO, 866.7 Mbps (BW80)"),
        ("Frequency Range", "5150–5850 MHz (US/CA: U-NII-1/2A/2C/3)"),
        ("Antenna", "Internal 5 dBi + External omni 4 dBi (RP-SMA, 360°x30°)"),
        ("Max. TX Power", "21 dBm (5GHz)"),
        ("Ports", "(1) GbE RJ45"),
        ("Power Method", "100–240V AC 어댑터 (포함, 최대 25W) 또는 PoE 입력 (10W excluding PoE output)"),
        ("Operating Temperature", "-10 to 40°C (14 to 104°F)"),
        ("Mounting", "Table, Wall (마운트 하드웨어 포함)"),
    ]),
)

# ============================================================
# 4) UniFi Device Bridge Switch
# ============================================================
pages["Unifi Supply - Device Bridge Switch.dc.html"] = assemble(
    hero(
        "Device Bridge Switch",
        "WiFi 7 무선 브리지 + 8포트 PoE+ 스위치 — 6GHz/5GHz로<br>최대 5.8Gbps 무선 업링크, 7개 2.5GbE + 1개 10GbE 포트.",
        "assets/udb-switch/udb-switch_01-hero-front.png",
        "Device Bridge Switch",
    ),
    why_section(
        "Why Device Bridge Switch",
        "WiFi 7 무선 업링크,<br>8포트 PoE+ 스위치<br>하나로 통합",
        "케이블 배선이 어려운 곳에 WiFi 7 무선 백홀과 8포트 PoE+ 스위치를 하나의 장비로 설치합니다.",
        [
            ("WiFi 7, 6GHz 5.8Gbps<br>또는 5GHz 4.3Gbps",
             "6GHz 대역에서 최대 5.8Gbps(BW320) 또는 5GHz 대역에서 최대 4.3Gbps(BW240) 무선 백홀을 제공합니다."),
            ("8포트 통합:<br>10GbE 1개 + 2.5GbE 7개",
             "1개의 10 기가비트 이더넷 포트와 7개의 2.5 기가비트 이더넷 포트를 내장해, 무선으로 받은 트래픽을 여러 유선 기기로 분배합니다."),
            ("8포트 PoE+ 지원,<br>최대 185W 전력",
             "8개 포트 모두 PoE+ 출력이 가능하며, 210W 어댑터 사용 시 최대 185W PoE 전력 예산을 확보할 수 있습니다(기본 60W 어댑터 포함 시 35W)."),
        ],
    ),
    design_section(
        "assets/udb-switch/udb-switch_02-diagram.png",
        "Device Bridge Switch 포트",
        "10GbE 1개,<br>2.5GbE PoE+ 7개,<br>데스크탑·벽걸이",
        "포트 1은 10 기가비트 이더넷, 포트 2-8은 2.5 기가비트 이더넷으로 구성되며, 8개 포트 전부 PoE+ 출력을 지원합니다.<br>54V DC 어댑터(포함)로 전원을 공급하며, 데스크탑 거치 또는 벽걸이 설치가 가능합니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "212.9 x 113 x 32.5 mm (8.4 x 4.4 x 1.3\")"),
        ("Weight", "548 g (기기), 563 g (with mount)"),
        ("Wireless Bridge", "WiFi 7 (802.11be), 4 spatial streams, 2x2 MIMO (6GHz + 5GHz)"),
        ("Max. Data Rate", "6GHz 5.8 Gbps (BW320) · 5GHz 4.3 Gbps (BW240)"),
        ("Antenna Gain", "8 dBi (both bands)"),
        ("Max. TX Power", "26 dBm (combined conducted)"),
        ("Ports", "(1) 10 GbE RJ45, (7) 2.5 GbE RJ45 — all 8 ports PoE+ capable"),
        ("PoE Budget", "35W (60W 어댑터 포함) 또는 185W (210W 어댑터 사용 시)"),
        ("Power Method", "54V DC/1.1A 어댑터 (포함, 최대 25W excluding PoE output, 42.5–57V DC range)"),
        ("Operating Temperature", "-30 to 40°C (-22 to 104°F)"),
        ("Mounting", "Desktop, Wall"),
    ]),
)

for filename, content in pages.items():
    with open(f"{OUT_DIR}/{filename}", "w") as f:
        f.write(content)

print(f"{len(pages)}개 페이지 작성 완료:")
for name in pages:
    print(" -", name)
