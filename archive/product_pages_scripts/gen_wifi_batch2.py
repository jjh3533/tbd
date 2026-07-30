"""WiFi Batch 2: E7 Campus / U6 Enterprise / U6 Enterprise In-Wall / U6 In-Wall

WiFi 6E 엔터프라이즈급(U6 Enterprise 시리즈)와 WiFi 7 옥외 메시 AP(E7 Campus) 4개.
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
# 1) UniFi E7 Campus
# ============================================================
pages["Unifi Supply - E7 Campus.dc.html"] = assemble(
    hero(
        "E7 Campus",
        "캠퍼스·공원·주차장 옥외 메시 커버리지 — WiFi 7,<br>6GHz/5GHz 듀얼밴드, 1000대 이상 동시접속 옥외 AP.",
        "assets/e7-campus/e7-campus_01-hero-front.png",
        "E7 Campus",
    ),
    why_section(
        "Why E7 Campus",
        "넓은 옥외 공간에<br>1000대 이상<br>동시접속",
        "캠퍼스, 공원, 주차장처럼 넓은 옥외 공간을 WiFi 7 메시로 커버하며, 1000대 이상의 기기를 동시에 연결합니다.",
        [
            ("WiFi 7, 6GHz + 5GHz<br>듀얼밴드 전용",
             "6GHz 5.8Gbps(BW320)와 5GHz 4.3Gbps(BW240) 듀얼밴드로 고밀도 옥외 환경에 최적화되어 있습니다(2.4GHz 미지원)."),
            ("1000대 이상 동시접속,<br>10GbE 업링크",
             "엔터프라이즈급 하드웨어로 1000개 이상의 클라이언트를 지원하며, 10 기가비트 이더넷 업링크로 트래픽을 처리합니다."),
            ("IP67 방수방진,<br>-40~55°C 동작",
             "IP67 등급 인클로저와 -40~55°C 동작 온도로 혹한·폭염·폭우 환경에서도 안정적으로 작동합니다."),
        ],
    ),
    design_section(
        "assets/e7-campus/e7-campus_02-diagram.png",
        "E7 Campus 구성",
        "10GbE 주 포트,<br>2.5GbE 보조 포트,<br>폴·벽 마운트",
        "1개의 10 기가비트 이더넷 주 포트와 1개의 2.5 기가비트 보조 포트를 갖춰, 메시 백홀이나 유선 확장에 활용할 수 있습니다.<br>폴(지름 60-114mm) 또는 벽면 마운트 하드웨어가 포함되며, 스테인리스·알루미늄 합금 마운트로 제작됩니다.",
    ),
    tech_specs_section([
        ("Dimensions", "⌀310 x 80 mm (⌀12.2 x 3.1\")"),
        ("Weight", "2.1 kg (4.6 lb)"),
        ("Wi-Fi Standard", "WiFi 7 (802.11be), 듀얼밴드 (6/5GHz only, 2.4GHz 미지원)"),
        ("Spatial Streams", "8 (4x4 MU-MIMO on 6GHz, 4x4 MU-MIMO on 5GHz)"),
        ("Max. Data Rate", "6GHz 5.8 Gbps (BW320) · 5GHz 4.3 Gbps (BW240)"),
        ("Max. Client Count", "1000+"),
        ("Coverage Area", "대규모 옥외 공간 (캠퍼스, 공원, 주차장)"),
        ("Ports", "(1) 10 GbE RJ45 (주), (1) 2.5 GbE RJ45 (보조)"),
        ("Power Method", "PoE++ (최대 60W)"),
        ("Operating Temperature", "-40 to 55°C (-40 to 131°F)"),
        ("Weatherproofing", "IP67"),
        ("Mounting", "Pole (60-114 mm 지름), Wall (마운트 포함, 스테인리스/알루미늄 합금)"),
    ]),
)

# ============================================================
# 2) UniFi U6 Enterprise
# ============================================================
pages["Unifi Supply - U6 Enterprise.dc.html"] = assemble(
    hero(
        "U6 Enterprise",
        "WiFi 6E 트라이밴드 — 6GHz/5GHz/2.4GHz 10개 스트림,<br>600대 이상 동시접속, 2.5GbE 업링크 엔터프라이즈 AP.",
        "assets/u6-enterprise/u6-enterprise_01-hero-front.png",
        "U6 Enterprise",
    ),
    why_section(
        "Why U6 Enterprise",
        "WiFi 6E 트라이밴드,<br>600대 이상<br>동시접속",
        "6GHz 신규 대역을 포함한 트라이밴드로 혼잡한 환경에서도 600개 이상의 기기를 안정적으로 연결합니다.",
        [
            ("WiFi 6E 트라이밴드,<br>10개 스트림",
             "6GHz 4x4, 5GHz 4x4, 2.4GHz 2x2 총 10개 공간 스트림으로 6GHz 4.8Gbps, 5GHz 4.8Gbps, 2.4GHz 573Mbps를 제공합니다."),
            ("600대 이상 동시접속,<br>2.5GbE 업링크",
             "엔터프라이즈급 하드웨어로 600개 이상의 클라이언트를 지원하며, 2.5 기가비트 이더넷 업링크로 높은 처리량을 온전히 활용합니다."),
            ("1,500 ft² 커버리지,<br>천장·벽 마운트",
             "최대 140m²(1,500 ft²) 면적을 커버하며, Pro Mount(포함)로 천장이나 벽면 어디든 설치할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/u6-enterprise/u6-enterprise_02-diagram.png",
        "U6 Enterprise 구성",
        "2.5GbE 업링크,<br>PoE+ 전원,<br>프리미엄 마운트",
        "1개의 1/2.5 기가비트 이더넷 포트로 업링크 대역폭을 확보하며, PoE+(최대 22W)로 전원을 공급받습니다.<br>알루미늄·폴리카보네이트 인클로저와 스테인리스(SUS304) Pro Mount가 포함됩니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "⌀220 x 48 mm (⌀8.7 x 1.9\")"),
        ("Weight", "960 g (2.1 lb), 1.1 kg (2.4 lb) with mount"),
        ("Wi-Fi Standard", "WiFi 6E (802.11ax), 트라이밴드 (6/5/2.4GHz)"),
        ("Spatial Streams", "10 (4x4 MU-MIMO on 6GHz, 4x4 on 5GHz, 2x2 on 2.4GHz)"),
        ("Max. Data Rate", "6GHz 4.8 Gbps (BW160) · 5GHz 4.8 Gbps (BW160) · 2.4GHz 573.5 Mbps (BW40)"),
        ("Coverage Area", "140 m² (1,500 ft²)"),
        ("Max. Client Count", "600+"),
        ("Ports", "(1) 1/2.5 GbE RJ45"),
        ("Power Method", "PoE+ (최대 22W, 44–57V DC)"),
        ("Operating Temperature", "-30 to 60°C (-22 to 140°F)"),
        ("Mounting", "Ceiling, Wall (Pro Mount 포함)"),
    ]),
)

# ============================================================
# 3) UniFi U6 Enterprise In-Wall
# ============================================================
pages["Unifi Supply - U6 Enterprise In-Wall.dc.html"] = assemble(
    hero(
        "U6 Enterprise In-Wall",
        "벽면 매립형 WiFi 6E 트라이밴드 — 600대 이상 동시접속,<br>4포트 GbE 스위치 + PoE 출력 내장, 2.5GbE 업링크.",
        "assets/u6-enterprise-iw/u6-enterprise-iw_01-hero-front.png",
        "U6 Enterprise In-Wall",
    ),
    why_section(
        "Why U6 Enterprise In-Wall",
        "벽면 매립형<br>WiFi 6E + 스위치<br>하나로 통합",
        "호텔 객실, 사무실 벽면에 매립 설치하며, WiFi 6E 트라이밴드와 4포트 스위치를 하나의 장비로 제공합니다.",
        [
            ("WiFi 6E 트라이밴드,<br>600대 이상 동시접속",
             "6GHz 4.8Gbps, 5GHz 4.8Gbps, 2.4GHz 573Mbps 트라이밴드로 600개 이상의 기기를 안정적으로 연결합니다."),
            ("4포트 GbE 스위치 내장,<br>1포트 PoE 출력",
             "4개의 기가비트 이더넷 다운링크 포트를 내장해 유선 기기를 연결하며, 그 중 1개 포트는 PoE 출력으로 IP 폰 등을 전원 공급할 수 있습니다."),
            ("2.5GbE 업링크,<br>PoE++입력 시 PoE 출력",
             "2.5 기가비트 이더넷 업링크로 높은 처리량을 확보하며, PoE++ 입력 시 다운링크 PoE 출력이 활성화됩니다(PoE+ 입력 시 PoE 출력 미지원)."),
        ],
    ),
    design_section(
        "assets/u6-enterprise-iw/u6-enterprise-iw_02-diagram.png",
        "U6 Enterprise In-Wall 포트",
        "업링크 2.5GbE 1개,<br>다운링크 GbE 4개<br>(1개 PoE 출력)",
        "후면의 2.5GbE 포트로 벽 속 배선과 연결되고, 전면의 4개 GbE 포트로 유선 기기를 확장합니다.<br>PoE++ 입력 시 1개 포트에서 PoE 출력이 가능하며, PoE+ 입력 시에는 PoE 출력이 비활성화됩니다.",
    ),
    tech_specs_section([
        ("Dimensions", "159.7 x 156.7 x 33.8 mm (6.3 x 6.2 x 1.3\")"),
        ("Weight", "884 g (1.9 lb)"),
        ("Wi-Fi Standard", "WiFi 6E (802.11ax), 트라이밴드 (6/5/2.4GHz)"),
        ("Spatial Streams", "10 (4x4 MU-MIMO on 6GHz, 4x4 on 5GHz, 2x2 on 2.4GHz)"),
        ("Max. Data Rate", "6GHz 4.8 Gbps (BW160) · 5GHz 4.8 Gbps (BW160) · 2.4GHz 573.5 Mbps (BW40)"),
        ("Coverage Area", "115 m² (1,250 ft²)"),
        ("Max. Client Count", "600+"),
        ("Ports", "(1) 1/2.5 GbE RJ45 업링크, (4) GbE RJ45 다운링크 (1개 PoE 출력)"),
        ("Power Method", "PoE+ 또는 PoE++ (최대 21W excluding PoE output, PoE++ 입력 시 PoE 출력 활성화, 44–57V DC)"),
        ("Operating Temperature", "-30 to 60°C (-22 to 140°F)"),
        ("Mounting", "In-Wall (벽면 매립형, 알루미늄 마운트 포함)"),
    ]),
)

# ============================================================
# 4) UniFi U6 In-Wall
# ============================================================
pages["Unifi Supply - U6 In-Wall.dc.html"] = assemble(
    hero(
        "U6 In-Wall",
        "벽면 매립형 WiFi 6 — 250대 이상 동시접속,<br>4포트 GbE 스위치 + PoE 출력 내장, 1.25 ft² 커버리지.",
        "assets/u6-iw/u6-iw_01-hero-front.png",
        "U6 In-Wall",
    ),
    why_section(
        "Why U6 In-Wall",
        "벽면 매립형<br>WiFi 6 + 스위치<br>하나로 통합",
        "호텔 객실, 사무실 벽면에 매립 설치하며, WiFi 6 듀얼밴드와 4포트 스위치를 하나의 장비로 제공합니다.",
        [
            ("WiFi 6 듀얼밴드,<br>6개 스트림",
             "5GHz 4x4, 2.4GHz 2x2 총 6개 공간 스트림으로 5GHz 4.8Gbps(BW160), 2.4GHz 573Mbps를 제공합니다."),
            ("4포트 GbE 스위치 내장,<br>1포트 PoE 출력",
             "4개의 기가비트 이더넷 다운링크 포트를 내장해 유선 기기를 연결하며, 그 중 1개 포트는 PoE 출력으로 IP 폰 등을 전원 공급할 수 있습니다."),
            ("250대 이상 동시접속,<br>PoE+ 입력 필수",
             "250개 이상의 클라이언트를 지원하며, PoE+ 입력 시 다운링크 PoE 출력이 활성화됩니다(PoE 입력 시 PoE 출력 미지원)."),
        ],
    ).replace(
        '<section style="padding:100px 60px;" data-screen-label="Why U6 In-Wall">',
        '<section style="padding:100px 60px;background:#F5F4F7;" data-screen-label="Why U6 In-Wall">',
    ),
    design_section(
        "assets/u6-iw/u6-iw_02-diagram.png",
        "U6 In-Wall 포트",
        "업링크 GbE 1개,<br>다운링크 GbE 4개<br>(1개 PoE 출력)",
        "후면의 GbE 데이터 입력 포트로 벽 속 배선과 연결되고, 전면의 4개 GbE 다운링크 포트로 유선 기기를 확장합니다.<br>PoE+ 입력 시 1개 포트에서 PoE 출력이 가능하며, PoE 입력 시에는 PoE 출력이 비활성화됩니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "139.7 x 96 x 31.2 mm (5.5 x 3.8 x 1.3\")"),
        ("Weight", "460 g (1 lb)"),
        ("Wi-Fi Standard", "WiFi 6 (802.11ax), 듀얼밴드 (5/2.4GHz)"),
        ("Spatial Streams", "6 (4x4 MU-MIMO on 5GHz, 2x2 on 2.4GHz)"),
        ("Max. Data Rate", "5GHz 4.8 Gbps (BW160) · 2.4GHz 573.5 Mbps (BW40)"),
        ("Coverage Area", "115 m² (1,250 ft²)"),
        ("Max. Client Count", "250+"),
        ("Ports", "(1) GbE RJ45 data-in, (4) GbE RJ45 data-out (1개 PoE 출력)"),
        ("Power Method", "PoE+ (최대 13W excluding PoE output, PoE+ 입력 필수 for PoE 출력)"),
        ("Operating Temperature", "-30 to 60°C (-22 to 140°F)"),
        ("Mounting", "In-Wall (벽면 매립형, 마운트 포함)"),
    ]),
)

for filename, content in pages.items():
    with open(f"{OUT_DIR}/{filename}", "w") as f:
        f.write(content)

print(f"{len(pages)}개 페이지 작성 완료:")
for name in pages:
    print(" -", name)
