"""Integrations Batch 1: Mobile Router Industrial / UNAS 2 / Display Cast Lite / Mobile Router

재고 있는 Integrations 제품 첫 4개.
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
# 1) UniFi Mobile Router Industrial
# ============================================================
pages["Unifi Supply - Mobile Router Industrial.dc.html"] = assemble(
    hero(
        "Mobile Router Industrial",
        "산업용 5G/LTE 모바일 라우터 — IP67 방수·방진,<br>-40~65°C 동작, 차량·옥외 산업 환경을 위한 모바일 WAN.",
        "assets/umr-industrial/umr-industrial_01-hero-front.png",
        "Mobile Router Industrial",
    ),
    why_section(
        "Why Mobile Router Industrial",
        "IP67 방수·방진,<br>차량·산업 환경에<br>최적화된 5G/LTE",
        "극한 환경에서도 안정적인 5G/LTE 연결을 제공하는 산업용 모바일 라우터입니다.",
        [
            ("5G/LTE 모바일 WAN,<br>nanoSIM + eSIM",
             "5G Sub-6 GHz와 LTE Cat 20을 지원하며, nanoSIM 슬롯과 eSIM을 동시 활용해 이중 SIM 페일오버를 구현합니다."),
            ("IP67 방수·방진,<br>-40~65°C 동작",
             "IP67 등급으로 물과 먼지를 완전 차단하고, -40~65°C의 극한 온도에서도 안정적으로 작동합니다."),
            ("차량·폴 마운트,<br>이더넷 PoE 출력",
             "차량 내부나 옥외 폴에 설치 가능하며, 1개의 GbE PoE 출력 포트로 액세스포인트 등을 직접 전원 공급할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/umr-industrial/umr-industrial_02-diagram.png",
        "Mobile Router Industrial 포트 구성",
        "GbE PoE 출력,<br>4G/5G SMA 안테나,<br>IP67 인클로저",
        "1개의 GbE RJ45 포트는 PoE 출력(최대 12W)을 지원하며, 외장 4G/5G SMA 안테나 2개를 연결합니다.<br>IP67 인클로저, M12 방수 커넥터, 알루미늄 합금 하우징으로 제작되어 차량·옥외 설치에 적합합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "201 x 165 x 47.2 mm (7.9 x 6.5 x 1.9\")"),
        ("Weight", "1.3 kg (2.8 lb)"),
        ("Cellular", "5G Sub-6 GHz (n1/2/3/5/7/8/12/13/14/20/25/26/28/29/30/38/40/41/48/66/70/71/77/78), LTE Cat 20 (B1/2/3/4/5/7/8/12/13/14/17/18/19/20/25/26/28/29/30/32/38/39/40/41/42/43/46/48/66/71), UMTS/HSPA+"),
        ("SIM", "nanoSIM (4FF) + eSIM, dual-SIM failover"),
        ("Ports", "(1) GbE RJ45 with PoE output (12W max)"),
        ("Antenna", "(2) External 4G/5G SMA connectors (5dBi omnidirectional cellular antennas included)"),
        ("Power Method", "12–56V DC M12 connector (최대 25W, 차량 전원 어댑터 포함)"),
        ("Operating Temperature", "-40 to 65°C (-40 to 149°F)"),
        ("Weatherproofing", "IP67 (방수·방진)"),
        ("Mounting", "Vehicle, Pole (마운트 하드웨어 포함)"),
    ]),
)

# ============================================================
# 2) UniFi UNAS 2
# ============================================================
pages["Unifi Supply - UNAS 2.dc.html"] = assemble(
    hero(
        "UNAS 2",
        "2베이 UniFi NAS — 최대 44TB(22TB x2) 스토리지,<br>UniFi Protect 녹화·백업과 파일 공유를 하나로.",
        "assets/unas-2/unas-2_01-hero-front.png",
        "UNAS 2",
    ),
    why_section(
        "Why UNAS 2",
        "2베이 NAS로<br>UniFi Protect 녹화와<br>파일 공유를 통합",
        "UniFi Protect 카메라 녹화, 백업, 파일 공유를 하나의 2베이 NAS에서 처리합니다.",
        [
            ("최대 44TB 스토리지,<br>2베이 핫스왑",
             "3.5\" SATA HDD/SSD 2개를 핫스왑 방식으로 장착해 최대 44TB(22TB x2)까지 확장할 수 있습니다."),
            ("UniFi Protect 녹화,<br>최대 4K 30fps x30개",
             "UniFi Protect 전용 앱으로 최대 30개의 4K 카메라를 실시간 녹화(720p30 기준)하고, 스마트 탐지·타임라인 검색을 제공합니다."),
            ("2.5GbE 듀얼 포트,<br>RAID 0/1 지원",
             "2개의 2.5GbE 이더넷 포트로 높은 대역폭을 확보하며, RAID 0(성능) 또는 RAID 1(미러링) 구성을 선택할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/unas-2/unas-2_02-diagram.png",
        "UNAS 2 구성",
        "2베이 핫스왑,<br>2.5GbE 듀얼 포트,<br>팬리스 쿨링",
        "전면에 2개의 핫스왑 드라이브 베이를 갖추고, 후면에 2개의 2.5GbE RJ45 포트와 1개의 USB 3.0 포트를 제공합니다.<br>팬리스 설계로 조용하게 작동하며, 데스크탑·랙마운트 모두 지원합니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "242 x 60 x 183 mm (9.5 x 2.4 x 7.2\")"),
        ("Weight", "2.7 kg (6.0 lb) without drives"),
        ("Drive Bays", "2x 3.5\" SATA HDD/SSD, hot-swappable, 최대 22TB per bay"),
        ("Max. Storage", "44 TB (22TB x2)"),
        ("RAID", "RAID 0, RAID 1"),
        ("CPU", "Quad-core ARM Cortex-A55 @ 2.0 GHz"),
        ("Memory", "4 GB DDR4"),
        ("Ports", "(2) 2.5GbE RJ45, (1) USB 3.0 Type-A"),
        ("UniFi Protect", "최대 30개 카메라 (4K 30fps, 720p30 기준), 스마트 탐지·타임라인 검색"),
        ("Power Method", "100–240V AC (최대 100W, 어댑터 포함)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Cooling", "Fanless (passive cooling)"),
        ("Mounting", "Desktop, Rackmount (1U, 랙마운트 키트 별도)"),
    ]),
)

# ============================================================
# 3) UniFi Display Cast Lite
# ============================================================
pages["Unifi Supply - Display Cast Lite.dc.html"] = assemble(
    hero(
        "Display Cast Lite",
        "UniFi 디지털 사이니지 — 4K 60Hz 디스플레이로<br>UniFi Network 앱에서 원격 제어하는 콘텐츠 캐스팅.",
        "assets/uc-cast-lite/uc-cast-lite_01-hero-front.png",
        "Display Cast Lite",
    ),
    why_section(
        "Why Display Cast Lite",
        "UniFi 앱으로<br>원격 제어하는<br>4K 디지털 사이니지",
        "UniFi Network 앱에서 원격으로 콘텐츠를 관리하고, 4K 60Hz 디스플레이에 실시간 캐스팅합니다.",
        [
            ("4K 60Hz 출력,<br>HDMI 2.0",
             "HDMI 2.0 포트로 최대 4K 60Hz(3840x2160) 해상도를 지원하며, 고화질 이미지·영상을 디스플레이에 출력합니다."),
            ("UniFi Network 앱<br>원격 콘텐츠 관리",
             "UniFi Network 앱에서 이미지·영상·웹페이지를 업로드하고, 재생 순서·시간을 원격으로 설정할 수 있습니다."),
            ("GbE 이더넷,<br>PoE 전원",
             "1개의 GbE RJ45 포트로 네트워크에 연결하며, PoE(802.3af)로 전원을 공급받아 별도 전원 케이블이 필요 없습니다."),
        ],
    ),
    design_section(
        "assets/uc-cast-lite/uc-cast-lite_02-diagram.png",
        "Display Cast Lite 포트 구성",
        "HDMI 2.0 출력,<br>GbE PoE 입력,<br>VESA 마운트",
        "HDMI 2.0 포트로 디스플레이에 연결하고, GbE RJ45 포트로 네트워크와 전원을 동시에 공급받습니다.<br>VESA 75x75mm 마운트 홀을 갖춰 디스플레이 뒷면에 직접 부착할 수 있습니다.",
    ),
    tech_specs_section([
        ("Dimensions", "96 x 96 x 25.5 mm (3.8 x 3.8 x 1.0\")"),
        ("Weight", "200 g (7.1 oz)"),
        ("Video Output", "HDMI 2.0, 최대 4K 60Hz (3840x2160)"),
        ("Content Types", "이미지 (JPEG, PNG), 영상 (MP4, H.264), 웹페이지 (URL)"),
        ("Management", "UniFi Network 앱 (원격 콘텐츠 업로드·재생 제어)"),
        ("Ports", "(1) GbE RJ45 (PoE 입력), (1) HDMI 2.0"),
        ("Power Method", "PoE (802.3af, 최대 12.5W)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Mounting", "VESA 75x75mm (디스플레이 뒷면 부착)"),
    ]),
)

# ============================================================
# 4) UniFi Mobile Router
# ============================================================
pages["Unifi Supply - Mobile Router.dc.html"] = assemble(
    hero(
        "Mobile Router",
        "5G/LTE 모바일 라우터 — nanoSIM + eSIM 이중 SIM,<br>차량·이동 환경에 최적화된 모바일 WAN.",
        "assets/umr/umr_01-hero-front.png",
        "Mobile Router",
    ),
    why_section(
        "Why Mobile Router",
        "5G/LTE 이중 SIM으로<br>차량·이동 환경에<br>안정적인 WAN 제공",
        "차량, 이동 오피스, 임시 현장에서 5G/LTE 모바일 WAN을 안정적으로 제공합니다.",
        [
            ("5G/LTE 모바일 WAN,<br>nanoSIM + eSIM",
             "5G Sub-6 GHz와 LTE Cat 20을 지원하며, nanoSIM 슬롯과 eSIM을 동시 활용해 이중 SIM 페일오버를 구현합니다."),
            ("GbE 이더넷 포트,<br>WiFi 6 듀얼밴드",
             "1개의 GbE RJ45 포트로 유선 연결을 제공하고, WiFi 6 듀얼밴드(5/2.4GHz)로 최대 50개 클라이언트를 무선 연결합니다."),
            ("차량 마운트,<br>USB-C 전원",
             "차량 내부에 설치할 수 있는 마운트 브라켓이 포함되어 있으며, USB-C 포트로 12V 차량 전원 어댑터를 연결합니다."),
        ],
    ),
    design_section(
        "assets/umr/umr_02-diagram.png",
        "Mobile Router 포트 구성",
        "GbE 포트,<br>4G/5G SMA 안테나,<br>USB-C 전원",
        "1개의 GbE RJ45 포트와 USB-C 전원 포트를 후면에 배치하고, 외장 4G/5G SMA 안테나 2개를 측면에 연결합니다.<br>차량 마운트 브라켓과 12V 차량 전원 어댑터가 포함되어 있습니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "130 x 130 x 32 mm (5.1 x 5.1 x 1.3\")"),
        ("Weight", "450 g (15.9 oz)"),
        ("Cellular", "5G Sub-6 GHz (n1/2/3/5/7/8/12/13/14/20/25/26/28/29/30/38/40/41/48/66/70/71/77/78), LTE Cat 20 (B1/2/3/4/5/7/8/12/13/14/17/18/19/20/25/26/28/29/30/32/38/39/40/41/42/43/46/48/66/71)"),
        ("SIM", "nanoSIM (4FF) + eSIM, dual-SIM failover"),
        ("Wi-Fi", "WiFi 6 (802.11ax), 듀얼밴드 (5/2.4GHz), 2x2 MIMO"),
        ("Max. Client Count", "50+ (WiFi)"),
        ("Ports", "(1) GbE RJ45, (1) USB-C (전원)"),
        ("Antenna", "(2) External 4G/5G SMA connectors (5dBi omnidirectional cellular antennas included)"),
        ("Power Method", "USB-C (12V, 차량 전원 어댑터 포함)"),
        ("Operating Temperature", "-10 to 40°C (14 to 104°F)"),
        ("Mounting", "Vehicle (마운트 브라켓 포함)"),
    ]),
)


if __name__ == "__main__":
    import os
    for filename, html in pages.items():
        path = os.path.join(OUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✓ {filename}")
    print(f"\n총 {len(pages)}개 페이지 생성 완료.")
