"""WiFi Batch 3: U6 Mesh / U6 Mesh Pro / U6+ / U7 Outdoor

WiFi 6 메시 AP 3개 + WiFi 7 옥외 AP 1개.
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
# 1) UniFi U6 Mesh
# ============================================================
pages["Unifi Supply - U6 Mesh.dc.html"] = assemble(
    hero(
        "U6 Mesh",
        "WiFi 6 옥외 메시 AP — 4x4 5GHz 4.8Gbps, IPX5 방수,<br>-30~60°C 동작, 벽면·폴 마운트 무선 메시 확장.",
        "assets/u6-mesh/u6-mesh_01-hero-front.png",
        "U6 Mesh",
    ),
    why_section(
        "Why U6 Mesh",
        "옥외 메시로<br>커버리지를<br>무선 확장",
        "정원, 주차장, 야외 공간에 유선 배선 없이 WiFi 6 메시로 네트워크를 확장합니다.",
        [
            ("WiFi 6, 4x4 5GHz<br>4.8Gbps",
             "5GHz 4x4 MU-MIMO로 최대 4.8Gbps(BW160), 2.4GHz 2x2로 573Mbps를 제공하며, 무선 메시 백홀로 업링크를 확보합니다."),
            ("IPX5 방수,<br>-30~60°C 동작",
             "IPX5 방수 등급과 -30~60°C 동작 온도로 옥외 환경에서 안정적으로 작동하며, UV 안정화 폴리카보네이트 인클로저로 제작됩니다."),
            ("250대 이상 동시접속,<br>벽·폴 마운트",
             "250개 이상의 클라이언트를 지원하며, 벽면 또는 폴 마운트 하드웨어(포함)로 다양한 설치 환경에 대응합니다."),
        ],
    ),
    design_section(
        "assets/u6-mesh/u6-mesh_02-diagram.png",
        "U6 Mesh 구성",
        "1개 GbE 포트,<br>PoE 어댑터 포함,<br>원통형 디자인",
        "1개의 기가비트 이더넷 포트로 유선 업링크(또는 무선 메시 백홀)를 연결하며, PoE 어댑터(포함)로 전원을 공급합니다.<br>지름 48.5mm의 원통형 디자인으로 설치 공간을 최소화하며, 벽면·폴 마운트 모두 지원합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "⌀48.5 x 159.5 mm (⌀1.9 x 6.3\")"),
        ("Weight", "400 g (14.1 oz)"),
        ("Wi-Fi Standard", "WiFi 6 (802.11ax), 듀얼밴드 (5/2.4GHz)"),
        ("Spatial Streams", "6 (4x4 MU-MIMO on 5GHz, 2x2 on 2.4GHz)"),
        ("Max. Data Rate", "5GHz 4.8 Gbps (BW160) · 2.4GHz 573.5 Mbps (BW40)"),
        ("Coverage Area", "140 m² (1,500 ft²)"),
        ("Max. Client Count", "250+"),
        ("Ports", "(1) GbE RJ45"),
        ("Power Method", "PoE (최대 13W, PoE 어댑터 포함, 44–57V DC)"),
        ("Operating Temperature", "-30 to 60°C (-22 to 140°F)"),
        ("Weatherproofing", "IPX5"),
        ("Mounting", "Wall, Pole (마운트 포함)"),
    ]),
)

# ============================================================
# 2) UniFi U6 Mesh Pro
# ============================================================
pages["Unifi Supply - U6 Mesh Pro.dc.html"] = assemble(
    hero(
        "U6 Mesh Pro",
        "WiFi 6 옥외 메시 AP — 2,000 ft² 커버리지, 8dBi 안테나,<br>IPX6 방수, 2포트 GbE, 벽면·폴 마운트 고출력 메시.",
        "assets/u6-mesh-pro/u6-mesh-pro_01-hero-front.png",
        "U6 Mesh Pro",
    ),
    why_section(
        "Why U6 Mesh Pro",
        "넓은 옥외 공간에<br>2,000 ft² 고출력<br>메시 커버리지",
        "정원, 주차장, 야외 행사장처럼 넓은 옥외 공간을 8dBi 고이득 안테나로 커버하는 WiFi 6 메시 AP입니다.",
        [
            ("2,000 ft² 커버리지,<br>8dBi 안테나",
             "최대 185m²(2,000 ft²) 면적을 커버하며, 8dBi 고이득 안테나로 먼 거리까지 신호를 전달합니다."),
            ("WiFi 6, 2x2 듀얼밴드<br>2.4Gbps + 573Mbps",
             "5GHz 2x2 MU-MIMO로 최대 2.4Gbps(BW160), 2.4GHz 2x2로 573Mbps를 제공하며, 무선 메시 백홀로 업링크를 확보합니다."),
            ("IPX6 방수,<br>2포트 GbE",
             "IPX6 방수 등급과 -30~60°C 동작 온도로 옥외 환경에 최적화되어 있으며, 2개의 기가비트 이더넷 포트를 갖췄습니다."),
        ],
    ).replace(
        '<section style="padding:100px 60px;" data-screen-label="Why U6 Mesh Pro">',
        '<section style="padding:100px 60px;background:#F5F4F7;" data-screen-label="Why U6 Mesh Pro">',
    ),
    design_section(
        "assets/u6-mesh-pro/u6-mesh-pro_02-diagram.png",
        "U6 Mesh Pro 구성",
        "2개 GbE 포트,<br>폴·벽 마운트,<br>UV 안정화 인클로저",
        "2개의 기가비트 이더넷 포트로 유선 업링크와 다운링크(또는 무선 메시 백홀)를 구성하며, PoE 어댑터(포함)로 전원을 공급합니다.<br>UV 안정화 폴리카보네이트 인클로저와 알루미늄 합금/스틸 마운트로 제작되며, 폴(지름 25-63.5mm) 또는 벽면에 설치 가능합니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "343.2 x 181.2 x 60.2 mm (13.5 x 7.1 x 2.4\")"),
        ("Weight", "819 g (1.8 lb)"),
        ("Wi-Fi Standard", "WiFi 6 (802.11ax), 듀얼밴드 (5/2.4GHz)"),
        ("Spatial Streams", "4 (2x2 MU-MIMO per band)"),
        ("Max. Data Rate", "5GHz 2.4 Gbps (BW160) · 2.4GHz 573.5 Mbps (BW40)"),
        ("Coverage Area", "185 m² (2,000 ft²)"),
        ("Max. Client Count", "250+"),
        ("Antenna Gain", "8 dBi (both bands)"),
        ("Max. TX Power", "27 dBm (5GHz), 22 dBm (2.4GHz)"),
        ("Ports", "(2) GbE RJ45"),
        ("Power Method", "PoE (최대 9W, PoE 어댑터 포함, 42.5–57V DC)"),
        ("Operating Temperature", "-30 to 60°C (-22 to 140°F)"),
        ("Weatherproofing", "IPX6"),
        ("Mounting", "Wall, Pole (1–2.5\" / 25–63.5 mm, 마운트 포함)"),
    ]),
)

# ============================================================
# 3) UniFi U6+
# ============================================================
pages["Unifi Supply - U6+.dc.html"] = assemble(
    hero(
        "U6+",
        "WiFi 6 듀얼밴드 AP — 5GHz 2.4Gbps, 300대 이상 동시접속,<br>1,500 ft² 커버리지, 컴팩트한 천장·벽 마운트 AP.",
        "assets/u6-plus/u6-plus_01-hero-front.png",
        "U6+",
    ),
    why_section(
        "Why U6+",
        "WiFi 6 듀얼밴드,<br>300대 이상<br>동시접속",
        "사무실, 카페, 소규모 매장에 WiFi 6 듀얼밴드 커버리지를 제공하는 컴팩트한 액세스포인트입니다.",
        [
            ("WiFi 6, 2x2 듀얼밴드<br>2.4Gbps + 573Mbps",
             "5GHz 2x2 MU-MIMO로 최대 2.4Gbps(BW160), 2.4GHz 2x2로 573Mbps를 제공하며, 안정적인 듀얼밴드 연결을 지원합니다."),
            ("300대 이상 동시접속,<br>1,500 ft² 커버리지",
             "최대 300개 이상의 클라이언트를 지원하며, 140m²(1,500 ft²) 면적을 커버합니다."),
            ("컴팩트한 디자인,<br>천장·벽 마운트",
             "지름 160mm의 컴팩트한 디자인으로 설치 공간을 최소화하며, 천장이나 벽면 어디든 설치할 수 있습니다(마운트 포함)."),
        ],
    ),
    design_section(
        "assets/u6-plus/u6-plus_02-diagram.png",
        "U6+ 구성",
        "1개 GbE 포트,<br>PoE 전원,<br>간결한 디자인",
        "1개의 기가비트 이더넷 포트로 업링크와 PoE 전원을 동시에 공급받으며, 최대 9W로 낮은 전력 소모를 자랑합니다.<br>천장·벽 마운트 하드웨어가 포함되며, -30~60°C 동작 온도로 다양한 환경에 대응합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "⌀160 x 33 mm (⌀6.3 x 1.3\")"),
        ("Weight", "338 g (11.9 oz), 413 g (14.6 oz) with mount"),
        ("Wi-Fi Standard", "WiFi 6 (802.11ax), 듀얼밴드 (5/2.4GHz)"),
        ("Spatial Streams", "4 (2x2 MU-MIMO per band)"),
        ("Max. Data Rate", "5GHz 2.4 Gbps (BW160) · 2.4GHz 573.5 Mbps (BW40)"),
        ("Coverage Area", "140 m² (1,500 ft²)"),
        ("Max. Client Count", "300+"),
        ("Ports", "(1) GbE RJ45"),
        ("Power Method", "PoE (최대 9W, 44–57V DC)"),
        ("Operating Temperature", "-30 to 60°C (-22 to 140°F)"),
        ("Mounting", "Ceiling, Wall (마운트 포함)"),
    ]),
)

# ============================================================
# 4) UniFi U7 Outdoor
# ============================================================
pages["Unifi Supply - U7 Outdoor.dc.html"] = assemble(
    hero(
        "U7 Outdoor",
        "WiFi 7 옥외 AP — 5GHz 4.3Gbps, 5,000 ft² 커버리지,<br>IPX6 방수, -30~60°C 동작, 벽면·폴 마운트 옥외 AP.",
        "assets/u7-outdoor/u7-outdoor_01-hero-front.png",
        "U7 Outdoor",
    ),
    why_section(
        "Why U7 Outdoor",
        "WiFi 7 옥외 AP,<br>5,000 ft² 광역<br>커버리지",
        "정원, 주차장, 야외 행사장에 WiFi 7 듀얼밴드로 5,000 ft² 광역 커버리지를 제공하는 옥외 액세스포인트입니다.",
        [
            ("WiFi 7, 5GHz 4.3Gbps<br>+ 2.4GHz 688Mbps",
             "5GHz 2x2 MU-MIMO로 최대 4.3Gbps(BW240), 2.4GHz 2x2로 688Mbps를 제공하며, WiFi 7 최신 기술을 옥외 환경에 적용합니다."),
            ("5,000 ft² 광역 커버리지,<br>250대 이상 동시접속",
             "최대 465m²(5,000 ft²) 면적을 커버하며, 250개 이상의 클라이언트를 안정적으로 연결합니다."),
            ("IPX6 방수,<br>2.5GbE 업링크",
             "IPX6 방수 등급과 -30~60°C 동작 온도로 옥외 환경에 최적화되어 있으며, 1/2.5 기가비트 이더넷 업링크로 높은 처리량을 지원합니다."),
        ],
    ).replace(
        '<section style="padding:100px 60px;" data-screen-label="Why U7 Outdoor">',
        '<section style="padding:100px 60px;background:#F5F4F7;" data-screen-label="Why U7 Outdoor">',
    ),
    design_section(
        "assets/u7-outdoor/u7-outdoor_02-diagram.png",
        "U7 Outdoor 구성",
        "2.5GbE 업링크,<br>폴·벽 마운트,<br>UV 안정화 인클로저",
        "1개의 1/2.5 기가비트 이더넷 포트로 업링크와 PoE+ 전원(최대 19W)을 공급받으며, 폴(지름 25-60mm) 또는 벽면에 설치 가능합니다.<br>UV 안정화 폴리카보네이트/알루미늄 합금 인클로저로 제작되며, 마운트 하드웨어가 포함됩니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "170 x 208 x 54.5 mm (6.7 x 8.2 x 2.1\")"),
        ("Weight", "1.2 kg (2.6 lb)"),
        ("Wi-Fi Standard", "WiFi 7 (802.11be), 듀얼밴드 (5/2.4GHz)"),
        ("Spatial Streams", "4 (2x2 MU-MIMO per band)"),
        ("Max. Data Rate", "5GHz 4.3 Gbps (BW240) · 2.4GHz 688 Mbps (BW40)"),
        ("Coverage Area", "465 m² (5,000 ft²)"),
        ("Max. Client Count", "250+"),
        ("Ports", "(1) 1/2.5 GbE RJ45"),
        ("Power Method", "PoE+ (최대 19W, 42.5–57V DC)"),
        ("Operating Temperature", "-30 to 60°C (-22 to 140°F)"),
        ("Weatherproofing", "IPX6"),
        ("Mounting", "Wall, Pole (1–2.36\" / 25–60 mm, 마운트 포함)"),
    ]),
)

for filename, content in pages.items():
    with open(f"{OUT_DIR}/{filename}", "w") as f:
        f.write(content)

print(f"{len(pages)}개 페이지 작성 완료:")
for name in pages:
    print(" -", name)
