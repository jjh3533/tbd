"""WiFi Batch 4: U7 Pro Outdoor / U7 Pro Wall / U7 Pro XG Wall / U7 Pro XGS

WiFi 7 프로 라인업 — 옥외 AP 1개, 벽면 마운트 2개, 천장형 고성능 AP 1개.
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
# 1) UniFi U7 Pro Outdoor
# ============================================================
# E7 Campus와 비슷한 옥외 제품이지만, 더 작고 가벼우며 트라이밴드(6/5/2.4GHz)
# 스펙은 WebSearch 결과 기반으로 작성 (정확한 techspecs 페이지 로드 실패했지만 검색 결과로 기본 스펙 확보)
pages["Unifi Supply - U7 Pro Outdoor.dc.html"] = assemble(
    hero(
        "U7 Pro Outdoor",
        "WiFi 7 옥외 트라이밴드 AP — 6GHz/5GHz/2.4GHz,<br>IP67 방수방진, -40~55°C 동작, 고밀도 옥외 커버리지.",
        "assets/u7-pro-outdoor/u7-pro-outdoor_01-hero-front.png",
        "U7 Pro Outdoor",
    ),
    why_section(
        "Why U7 Pro Outdoor",
        "WiFi 7 트라이밴드,<br>IP67 옥외 등급<br>고밀도 커버리지",
        "캠퍼스, 공원, 주차장처럼 고밀도 옥외 환경에 WiFi 7 트라이밴드로 안정적인 커버리지를 제공합니다.",
        [
            ("WiFi 7 트라이밴드,<br>6GHz + 5GHz + 2.4GHz",
             "6GHz, 5GHz, 2.4GHz 트라이밴드로 혼잡한 옥외 환경에서도 안정적인 연결을 유지하며, 고밀도 클라이언트를 지원합니다."),
            ("IP67 방수방진,<br>-40~55°C 동작",
             "IP67 등급 인클로저와 -40~55°C 동작 온도로 혹한·폭염·폭우 환경에서도 안정적으로 작동합니다."),
            ("2.5GbE 업링크,<br>폴·벽 마운트",
             "1/2.5 기가비트 이더넷 업링크로 높은 처리량을 지원하며, 폴 또는 벽면 마운트 하드웨어(포함)로 다양한 설치 환경에 대응합니다."),
        ],
    ),
    design_section(
        "assets/u7-pro-outdoor/u7-pro-outdoor_02-diagram.png",
        "U7 Pro Outdoor 구성",
        "2.5GbE 업링크,<br>PoE++ 전원,<br>내후성 인클로저",
        "1개의 1/2.5 기가비트 이더넷 포트로 업링크와 PoE++ 전원을 공급받으며, IP67 등급 인클로저로 먼지와 물의 침입을 완전히 차단합니다.<br>폴 또는 벽면 마운트 하드웨어가 포함되며, 스테인리스·알루미늄 합금 마운트로 제작됩니다.",
    ),
    tech_specs_section([
        ("Dimensions", "약 200-250 mm (추정, 정확한 스펙 미확보)"),
        ("Weight", "약 1-1.5 kg (추정)"),
        ("Wi-Fi Standard", "WiFi 7 (802.11be), 트라이밴드 (6/5/2.4GHz)"),
        ("Max. Data Rate", "6GHz + 5GHz + 2.4GHz (정확한 대역별 속도 미확보)"),
        ("Ports", "(1) 1/2.5 GbE RJ45"),
        ("Power Method", "PoE++"),
        ("Operating Temperature", "-40 to 55°C (-40 to 131°F)"),
        ("Weatherproofing", "IP67"),
        ("Mounting", "Pole, Wall (마운트 포함)"),
    ]),
)

# ============================================================
# 2) UniFi U7 Pro Wall
# ============================================================
pages["Unifi Supply - U7 Pro Wall.dc.html"] = assemble(
    hero(
        "U7 Pro Wall",
        "WiFi 7 트라이밴드 벽면 마운트 AP — 6GHz/5GHz/2.4GHz,<br>300대 이상 동시접속, 1,500 ft² 커버리지, 2.5GbE 업링크.",
        "assets/u7-pro-wall/u7-pro-wall_01-hero-front.png",
        "U7 Pro Wall",
    ),
    why_section(
        "Why U7 Pro Wall",
        "WiFi 7 트라이밴드,<br>벽면 마운트<br>컴팩트한 설치",
        "호텔 객실, 사무실 벽면에 WiFi 7 트라이밴드 커버리지를 제공하는 컴팩트한 벽면 마운트 AP입니다.",
        [
            ("WiFi 7 트라이밴드,<br>6개 스트림",
             "6GHz 5.8Gbps(BW320), 5GHz 4.3Gbps(BW240), 2.4GHz 688Mbps(BW40) 트라이밴드로 2x2 MU-MIMO 총 6개 스트림을 제공합니다."),
            ("300대 이상 동시접속,<br>1,500 ft² 커버리지",
             "최대 300개 이상의 클라이언트를 지원하며, 140m²(1,500 ft²) 면적을 커버합니다."),
            ("2.5GbE 업링크,<br>벽면 마운트",
             "1/2.5 기가비트 이더넷 업링크로 높은 처리량을 지원하며, 벽면 마운트 하드웨어(포함)로 간편하게 설치할 수 있습니다."),
        ],
    ).replace(
        '<section style="padding:100px 60px;" data-screen-label="Why U7 Pro Wall">',
        '<section style="padding:100px 60px;background:#F5F4F7;" data-screen-label="Why U7 Pro Wall">',
    ),
    design_section(
        "assets/u7-pro-wall/u7-pro-wall_02-diagram.png",
        "U7 Pro Wall 구성",
        "2.5GbE 업링크,<br>PoE+ 전원,<br>컴팩트한 벽면형",
        "1개의 1/2.5 기가비트 이더넷 포트로 업링크와 PoE+ 전원(최대 22W)을 공급받으며, 150 x 103 x 36mm의 컴팩트한 크기로 벽면 설치 공간을 최소화합니다.<br>알루미늄·폴리카보네이트 인클로저와 알루미늄 마운트(포함)로 제작됩니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "150 x 103 x 36 mm (5.9 x 4.1 x 1.4\")"),
        ("Weight", "580 g (1.3 lb)"),
        ("Wi-Fi Standard", "WiFi 7 (802.11be), 트라이밴드 (6/5/2.4GHz)"),
        ("Spatial Streams", "6 (2x2 MU-MIMO per band)"),
        ("Max. Data Rate", "6GHz 5.8 Gbps (BW320) · 5GHz 4.3 Gbps (BW240) · 2.4GHz 688 Mbps (BW40)"),
        ("Coverage Area", "140 m² (1,500 ft²)"),
        ("Max. Client Count", "300+"),
        ("Ports", "(1) 1/2.5 GbE RJ45"),
        ("Power Method", "PoE+ (최대 22W, 44–57V DC)"),
        ("Operating Temperature", "-30 to 60°C (-22 to 140°F)"),
        ("Mounting", "Wall (마운트 포함)"),
    ]),
)

# ============================================================
# 3) UniFi U7 Pro XG Wall
# ============================================================
pages["Unifi Supply - U7 Pro XG Wall.dc.html"] = assemble(
    hero(
        "U7 Pro XG Wall",
        "WiFi 7 트라이밴드 벽면 마운트 AP — 10GbE 업링크,<br>6GHz/5GHz/2.4GHz, 300대 이상, 1,500 ft² 커버리지.",
        "assets/u7-pro-xg-wall/u7-pro-xg-wall_01-hero-front.png",
        "U7 Pro XG Wall",
    ),
    why_section(
        "Why U7 Pro XG Wall",
        "WiFi 7 트라이밴드,<br>10GbE 업링크<br>벽면 마운트",
        "호텔 객실, 사무실 벽면에 WiFi 7 트라이밴드와 10 기가비트 업링크를 제공하는 고성능 벽면 마운트 AP입니다.",
        [
            ("WiFi 7 트라이밴드,<br>6개 스트림",
             "6GHz 5.8Gbps(BW320), 5GHz 4.3Gbps(BW240), 2.4GHz 688Mbps(BW40) 트라이밴드로 2x2 MU-MIMO 총 6개 스트림을 제공합니다."),
            ("10GbE 업링크,<br>높은 처리량 확보",
             "1개의 10 기가비트 이더넷 업링크로 WiFi 7의 높은 처리량을 온전히 활용하며, 고밀도 트래픽을 여유롭게 처리합니다."),
            ("300대 이상 동시접속,<br>컴팩트한 벽면형",
             "최대 300개 이상의 클라이언트를 지원하며, 155 x 108 x 33.5mm의 컴팩트한 크기로 벽면 설치 공간을 최소화합니다."),
        ],
    ),
    design_section(
        "assets/u7-pro-xg-wall/u7-pro-xg-wall_02-diagram.png",
        "U7 Pro XG Wall 구성",
        "10GbE 업링크,<br>PoE+ 전원,<br>컴팩트한 벽면형",
        "1개의 10 기가비트 이더넷 포트로 업링크와 PoE+ 전원(최대 22W)을 공급받으며, U7 Pro Wall과 비슷한 크기로 벽면 설치가 간편합니다.<br>\"XG\"는 10 기가비트 업링크를 의미하며, U7 Pro Wall 대비 5배 높은 업링크 대역폭을 제공합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "155 x 108 x 33.5 mm (6.1 x 4.3 x 1.3\")"),
        ("Weight", "505 g (1.1 lb)"),
        ("Wi-Fi Standard", "WiFi 7 (802.11be), 트라이밴드 (6/5/2.4GHz)"),
        ("Spatial Streams", "6 (2x2 MU-MIMO per band)"),
        ("Max. Data Rate", "6GHz 5.8 Gbps (BW320) · 5GHz 4.3 Gbps (BW240) · 2.4GHz 688 Mbps (BW40)"),
        ("Coverage Area", "140 m² (1,500 ft²)"),
        ("Max. Client Count", "300+"),
        ("Ports", "(1) 10 GbE RJ45"),
        ("Power Method", "PoE+ (최대 22W, 42.5–57V DC)"),
        ("Operating Temperature", "-30 to 40°C (-22 to 104°F)"),
        ("Mounting", "Wall"),
    ]),
)

# ============================================================
# 4) UniFi U7 Pro XGS
# ============================================================
pages["Unifi Supply - U7 Pro XGS.dc.html"] = assemble(
    hero(
        "U7 Pro XGS",
        "WiFi 7 트라이밴드 고성능 AP — 10GbE 업링크,<br>6GHz/5GHz/2.4GHz 8개 스트림, 500대 이상, 1,750 ft² 커버리지.",
        "assets/u7-pro-xgs/u7-pro-xgs_01-hero-front.png",
        "U7 Pro XGS",
    ),
    why_section(
        "Why U7 Pro XGS",
        "WiFi 7 최고 성능,<br>10GbE 업링크<br>500대 이상",
        "대규모 사무실, 컨퍼런스 홀처럼 고밀도 환경에 WiFi 7 최고 성능과 10 기가비트 업링크를 제공하는 플래그십 AP입니다.",
        [
            ("WiFi 7 트라이밴드,<br>8개 스트림",
             "6GHz 2x2 5.8Gbps(BW320), 5GHz 4x4 8.6Gbps(BW240), 2.4GHz 2x2 688Mbps(BW40) 총 8개 스트림으로 최고 성능을 제공합니다."),
            ("500대 이상 동시접속,<br>10GbE 업링크",
             "500개 이상의 클라이언트를 지원하며, 10 기가비트 이더넷 업링크로 고밀도 트래픽을 여유롭게 처리합니다."),
            ("1,750 ft² 커버리지,<br>천장·벽 마운트",
             "최대 160m²(1,750 ft²) 면적을 커버하며, Lite Mount(포함)로 천장이나 벽면 어디든 설치할 수 있습니다."),
        ],
    ).replace(
        '<section style="padding:100px 60px;" data-screen-label="Why U7 Pro XGS">',
        '<section style="padding:100px 60px;background:#F5F4F7;" data-screen-label="Why U7 Pro XGS">',
    ),
    design_section(
        "assets/u7-pro-xgs/u7-pro-xgs_02-diagram.png",
        "U7 Pro XGS 구성",
        "10GbE 업링크,<br>PoE++ 전원,<br>플래그십 성능",
        "1개의 10 기가비트 이더넷 포트로 업링크와 PoE++(최대 29W) 전원을 공급받으며, U7 Pro 시리즈 중 가장 높은 성능을 자랑합니다.<br>\"XGS\"는 10 기가비트 업링크 + 고성능 스트림 구성을 의미하며, 5GHz 4x4 스트림이 핵심 차별점입니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "⌀215 x 32.5 mm (⌀8.5 x 1.3\")"),
        ("Weight", "800 g (1.8 lb)"),
        ("Wi-Fi Standard", "WiFi 7 (802.11be), 트라이밴드 (6/5/2.4GHz)"),
        ("Spatial Streams", "8 (6GHz 2x2, 5GHz 4x4, 2.4GHz 2x2 MU-MIMO)"),
        ("Max. Data Rate", "6GHz 5.8 Gbps (BW320) · 5GHz 8.6 Gbps (BW240) · 2.4GHz 688 Mbps (BW40)"),
        ("Coverage Area", "160 m² (1,750 ft²)"),
        ("Max. Client Count", "500+"),
        ("Ports", "(1) 10 GbE RJ45"),
        ("Power Method", "PoE++ (최대 29W, 42.5–57V DC)"),
        ("Operating Temperature", "-30 to 40°C (-22 to 104°F)"),
        ("Mounting", "Ceiling, Wall (Lite Mount 포함)"),
    ]),
)

for filename, content in pages.items():
    with open(f"{OUT_DIR}/{filename}", "w") as f:
        f.write(content)

print(f"{len(pages)}개 페이지 작성 완료:")
for name in pages:
    print(" -", name)
