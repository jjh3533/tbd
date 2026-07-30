"""Integrations Batch 2: 5G Max / Mobile Router Ultra / PoE Audio Port / LTE Backup Pro

재고 있는 Integrations 제품 나머지 4개.
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
# 1) UniFi 5G Max
# ============================================================
pages["Unifi Supply - 5G Max.dc.html"] = assemble(
    hero(
        "5G Max",
        "5G/LTE 모바일 WAN — nanoSIM + eSIM 이중 SIM,<br>WiFi 6E 트라이밴드로 최대 300개 클라이언트 연결.",
        "assets/u5g-max/u5g-max_01-hero-front.png",
        "5G Max",
    ),
    why_section(
        "Why 5G Max",
        "5G 모바일 WAN에<br>WiFi 6E 트라이밴드를<br>결합한 올인원",
        "5G/LTE 모바일 WAN과 WiFi 6E 트라이밴드 액세스포인트를 하나의 기기에 통합했습니다.",
        [
            ("5G/LTE 모바일 WAN,<br>nanoSIM + eSIM",
             "5G Sub-6 GHz와 LTE Cat 20을 지원하며, nanoSIM 슬롯과 eSIM을 동시 활용해 이중 SIM 페일오버를 구현합니다."),
            ("WiFi 6E 트라이밴드,<br>6/5/2.4GHz",
             "WiFi 6E(6GHz) + WiFi 6(5GHz) + WiFi 5(2.4GHz) 트라이밴드로 최대 300개 클라이언트를 동시 연결합니다."),
            ("2.5GbE 포트,<br>PoE 출력 지원",
             "1개의 2.5GbE RJ45 포트는 PoE 출력(최대 25W)을 지원해 UniFi 카메라나 액세스포인트에 전원을 공급할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/u5g-max/u5g-max_02-diagram.png",
        "5G Max 포트 구성",
        "2.5GbE PoE 출력,<br>4G/5G SMA 안테나,<br>WiFi 6E 내장",
        "1개의 2.5GbE RJ45 포트는 PoE 출력을 지원하며, 외장 4G/5G SMA 안테나 4개를 연결합니다.<br>WiFi 6E 트라이밴드 안테나가 내장되어 있으며, 데스크탑·랙마운트 모두 지원합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "442.4 x 285.6 x 66 mm (17.4 x 11.2 x 2.6\")"),
        ("Weight", "3.2 kg (7.1 lb)"),
        ("Cellular", "5G Sub-6 GHz (n1/2/3/5/7/8/12/20/25/28/38/40/41/66/71/77/78), LTE Cat 20 (B1/2/3/4/5/7/8/12/13/17/18/19/20/25/26/28/29/30/32/38/39/40/41/42/43/46/66/71)"),
        ("SIM", "nanoSIM (4FF) + eSIM, dual-SIM failover"),
        ("Wi-Fi", "WiFi 6E (6GHz), WiFi 6 (5GHz), WiFi 5 (2.4GHz), 트라이밴드, 4x4 MIMO per band"),
        ("Max. Data Rate", "6GHz 4.8 Gbps (BW160) · 5GHz 4.8 Gbps (BW160) · 2.4GHz 574 Mbps (BW40)"),
        ("Max. Client Count", "300+"),
        ("Ports", "(1) 2.5GbE RJ45 with PoE output (25W max)"),
        ("Antenna", "(4) External 4G/5G SMA connectors (5dBi omnidirectional cellular antennas included), WiFi 6E tri-band internal antennas"),
        ("Power Method", "100–240V AC (최대 65W, 어댑터 포함)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Mounting", "Desktop, Rackmount (1U, 랙마운트 키트 포함)"),
    ]),
)

# ============================================================
# 2) UniFi Mobile Router Ultra
# ============================================================
pages["Unifi Supply - Mobile Router Ultra.dc.html"] = assemble(
    hero(
        "Mobile Router Ultra",
        "컴팩트 5G/LTE 모바일 라우터 — nanoSIM + eSIM 이중 SIM,<br>WiFi 6 듀얼밴드로 이동 중에도 안정적인 연결.",
        "assets/umr-ultra/umr-ultra_01-hero-front.png",
        "Mobile Router Ultra",
    ),
    why_section(
        "Why Mobile Router Ultra",
        "주머니에 들어가는<br>컴팩트한 5G/LTE<br>모바일 라우터",
        "작고 가벼운 본체에 5G/LTE와 WiFi 6 듀얼밴드를 담아, 이동 중에도 안정적인 네트워크를 제공합니다.",
        [
            ("5G/LTE 모바일 WAN,<br>nanoSIM + eSIM",
             "5G Sub-6 GHz와 LTE Cat 20을 지원하며, nanoSIM 슬롯과 eSIM을 동시 활용해 이중 SIM 페일오버를 구현합니다."),
            ("WiFi 6 듀얼밴드,<br>최대 32개 클라이언트",
             "WiFi 6(5/2.4GHz) 듀얼밴드로 최대 32개 클라이언트를 동시 연결하며, 2x2 MIMO로 안정적인 속도를 제공합니다."),
            ("컴팩트 디자인,<br>5,000mAh 배터리",
             "130 x 68 x 19mm의 주머니 크기에 5,000mAh 배터리를 내장해 외출 시에도 장시간 사용할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/umr-ultra/umr-ultra_02-diagram.png",
        "Mobile Router Ultra 구성",
        "USB-C 충전,<br>내장 안테나,<br>LED 디스플레이",
        "USB-C 포트로 충전하고, 4G/5G 안테나와 WiFi 안테나를 모두 내장했습니다.<br>전면 LED 디스플레이로 신호 강도, 배터리 잔량, 데이터 사용량을 실시간으로 확인할 수 있습니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "130 x 68 x 19 mm (5.1 x 2.7 x 0.7\")"),
        ("Weight", "240 g (8.5 oz)"),
        ("Cellular", "5G Sub-6 GHz (n1/2/3/5/7/8/12/20/25/28/38/40/41/66/71/77/78), LTE Cat 20 (B1/2/3/4/5/7/8/12/13/17/18/19/20/25/26/28/29/30/32/38/39/40/41/42/43/46/66/71)"),
        ("SIM", "nanoSIM (4FF) + eSIM, dual-SIM failover"),
        ("Wi-Fi", "WiFi 6 (802.11ax), 듀얼밴드 (5/2.4GHz), 2x2 MIMO"),
        ("Max. Client Count", "32"),
        ("Battery", "5,000 mAh, USB-C 충전"),
        ("Antenna", "Internal 4G/5G and WiFi antennas"),
        ("Display", "LED (신호 강도, 배터리, 데이터 사용량)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
    ]),
)

# ============================================================
# 3) UniFi PoE Audio Port
# ============================================================
pages["Unifi Supply - PoE Audio Port.dc.html"] = assemble(
    hero(
        "PoE Audio Port",
        "PoE 오디오 인터페이스 — 기존 스피커를 PoE 네트워크에<br>연결하고 UniFi Talk로 원격 제어하는 오디오 브리지.",
        "assets/upl-port/upl-port_01-hero-front.png",
        "PoE Audio Port",
    ),
    why_section(
        "Why PoE Audio Port",
        "기존 스피커를<br>UniFi Talk<br>네트워크 오디오로",
        "기존 패시브 스피커나 앰프를 PoE 네트워크에 연결해, UniFi Talk로 원격 방송·음악 재생을 제어합니다.",
        [
            ("스피커 터미널 +<br>라인 출력",
             "스피커 터미널(최대 30W 출력)과 3.5mm 라인 출력을 모두 갖춰, 패시브 스피커나 외부 앰프에 직접 연결합니다."),
            ("UniFi Talk 통합,<br>원격 방송·음악",
             "UniFi Talk 앱에서 개별 또는 그룹 스피커에 실시간 방송을 송출하거나, 예약된 음악·안내 방송을 재생할 수 있습니다."),
            ("PoE 전원,<br>볼륨 노브 내장",
             "PoE(802.3at)로 전원을 공급받아 별도 전원 케이블이 필요 없으며, 전면 볼륨 노브로 현장에서 음량을 직접 조절합니다."),
        ],
    ),
    design_section(
        "assets/upl-port/upl-port_02-diagram.png",
        "PoE Audio Port 포트 구성",
        "스피커 터미널,<br>라인 출력,<br>GbE PoE 입력",
        "후면에 스피커 터미널(좌/우), 3.5mm 라인 출력, GbE RJ45 PoE 입력을 배치하고, 전면에 볼륨 노브와 상태 LED를 제공합니다.<br>금속 하우징, 벽면·랙마운트 모두 지원합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "144 x 144 x 44 mm (5.7 x 5.7 x 1.7\")"),
        ("Weight", "700 g (24.7 oz)"),
        ("Audio Output", "스피커 터미널 (최대 30W, 8Ω), 3.5mm 라인 출력 (스테레오)"),
        ("Frequency Response", "20 Hz – 20 kHz"),
        ("THD+N", "< 0.05% @ 1 kHz"),
        ("UniFi Talk", "원격 방송, 음악 재생, 예약 안내 방송, 그룹 제어"),
        ("Ports", "(1) GbE RJ45 (PoE 입력), 스피커 터미널 (L/R), 3.5mm line out"),
        ("Controls", "전면 볼륨 노브, 상태 LED"),
        ("Power Method", "PoE+ (802.3at, 최대 30W)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Mounting", "Wall, Rackmount (1U, 랙마운트 키트 별도)"),
    ]),
)

# ============================================================
# 4) UniFi LTE Backup Pro
# ============================================================
pages["Unifi Supply - LTE Backup Pro.dc.html"] = assemble(
    hero(
        "LTE Backup Pro",
        "LTE 백업 WAN — 기존 유선 WAN 장애 시 자동 전환,<br>nanoSIM + eSIM 이중 SIM으로 비즈니스 연속성 보장.",
        "assets/u-lte-pro/u-lte-pro_01-hero-front.png",
        "LTE Backup Pro",
    ),
    why_section(
        "Why LTE Backup Pro",
        "유선 WAN 장애 시<br>LTE로 자동 전환,<br>비즈니스 연속성 확보",
        "기존 유선 인터넷(케이블·광랜)이 끊겼을 때, LTE 백업 WAN으로 즉시 전환해 네트워크 가용성을 높입니다.",
        [
            ("LTE Cat 18 백업 WAN,<br>nanoSIM + eSIM",
             "LTE Cat 18(최대 1.2Gbps 다운로드)을 지원하며, nanoSIM 슬롯과 eSIM을 동시 활용해 이중 SIM 페일오버를 구현합니다."),
            ("자동 페일오버,<br>UniFi Network 통합",
             "UniFi Gateway와 연동해 유선 WAN 장애 시 자동으로 LTE로 전환하고, 복구 시 다시 유선으로 돌아갑니다."),
            ("GbE 이더넷 포트,<br>외장 LTE 안테나",
             "1개의 GbE RJ45 포트로 UniFi Gateway에 연결하고, 외장 LTE SMA 안테나 2개(5dBi)를 측면에 장착해 신호를 최적화합니다."),
        ],
    ),
    design_section(
        "assets/u-lte-pro/u-lte-pro_02-diagram.png",
        "LTE Backup Pro 포트 구성",
        "GbE 포트,<br>LTE SMA 안테나,<br>PoE 전원",
        "1개의 GbE RJ45 포트로 UniFi Gateway에 연결하고, 외장 LTE SMA 안테나 2개를 측면에 장착합니다.<br>PoE(802.3af)로 전원을 공급받아 별도 전원 케이블이 필요 없습니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "130 x 130 x 32 mm (5.1 x 5.1 x 1.3\")"),
        ("Weight", "400 g (14.1 oz)"),
        ("Cellular", "LTE Cat 18 (B1/2/3/4/5/7/8/12/13/17/18/19/20/25/26/28/29/30/32/38/39/40/41/42/43/46/66/71), UMTS/HSPA+"),
        ("Max. Data Rate", "LTE: 1.2 Gbps down / 150 Mbps up"),
        ("SIM", "nanoSIM (4FF) + eSIM, dual-SIM failover"),
        ("Ports", "(1) GbE RJ45"),
        ("Antenna", "(2) External LTE SMA connectors (5dBi omnidirectional LTE antennas included)"),
        ("Failover", "UniFi Gateway 연동, 자동 WAN 페일오버"),
        ("Power Method", "PoE (802.3af, 최대 12.5W)"),
        ("Operating Temperature", "0 to 40°C (32 to 104°F)"),
        ("Mounting", "Desktop, Wall (마운트 하드웨어 포함)"),
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
