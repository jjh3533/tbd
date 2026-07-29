"""배치 2: Switching 카테고리 중 상세페이지가 없던 6개 상품 생성.

- UniFi Enterprise 8 PoE (Vintage)
- UniFi Flex
- UniFi Flex Utility        (스위치가 아니라 USW-Flex 전용 방수 인클로저 - 스위치 별도 구매)
- UniFi Flex Utility Pro    (역시 인클로저. USW-Flex/Ultra 등 여러 모델과 호환되는 범용 제품)
- UniFi Pro 8 PoE
- UniFi Pro XG 8 PoE

Flex Utility / Flex Utility Pro는 리서치 결과 실제로는 스위치가 아니라
빈 인클로저(액세서리)임을 확인했다 - 포트/스위칭 용량 같은 스위치 스펙을
인클로저 자체의 스펙인 것처럼 쓰면 안 되므로, 이 두 페이지만 인클로저
스펙(방수 등급, 크기, 호환 모델, 동봉 어댑터) 중심으로 다르게 구성한다.
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
# 1) UniFi Enterprise 8 PoE (Vintage)
# ============================================================
pages["Unifi Supply - Enterprise 8 PoE.dc.html"] = assemble(
    hero(
        "Enterprise 8 PoE",
        "8개의 2.5G PoE+ 포트와 10G SFP+ 업링크까지,<br>1.3형 터치스크린을 갖춘 데스크탑 스위치.",
        "assets/usw-enterprise-8-poe/usw-enterprise-8-poe_01-hero-front.png",
        "Enterprise 8 PoE",
    ),
    why_section(
        "Why Enterprise 8 PoE",
        "8포트 2.5G PoE+,<br>120W 전력까지<br>하나의 스위치에",
        "다음 세대 액세스포인트와 카메라를 위한 2.5G PoE+ 스위칭 허브입니다.",
        [
            ("8포트 2.5G PoE+,<br>120W 전력 용량",
             "(8) 2.5 GbE RJ45 포트가 모두 PoE+(최대 32W)를 지원해 최대 120W 전력을 여러 기기에 동시에 공급합니다."),
            ("2개의 10G SFP+,<br>80 Gbps 스위칭 용량",
             "2개의 10G SFP+ 업링크로 상위 네트워크나 NAS에 10G 대역폭을 그대로 활용하고, 80 Gbps 스위칭 용량으로 여유롭게 처리합니다."),
            ("1.3형 터치스크린,<br>Layer 3 라우팅",
             "터치스크린으로 상태를 바로 확인하고, DHCP 서버·정적 라우팅 등 Layer 3 기능을 지원합니다."),
        ],
    ),
    design_section(
        "assets/usw-enterprise-8-poe/usw-enterprise-8-poe_02-ports-diagram.png",
        "Enterprise 8 PoE 포트 구성",
        "8개의 2.5G PoE+,<br>2개의 10G SFP+",
        "포트 1-8은 모두 2.5 GbE PoE+(최대 32W)를 지원하고, 마지막 2개(9-10)는 10G SFP+ 업링크 슬롯입니다.<br>액세스포인트, 카메라 등 PoE 기기를 8대까지 연결하고 10G로 상위 네트워크와 연결하세요.",
    ),
    tech_specs_section([
        ("Dimensions", '200 x 248 x 44 mm (7.9 x 9.8 x 1.7")'),
        ("Port Layout", "(8) 2.5 GbE RJ45 (PoE+), (2) 10G SFP+"),
        ("Form Factor", "Desktop"),
        ("Max. PoE Output", "Up to PoE+"),
        ("Total PoE Availability", "120 W"),
        ("Switching Capacity", "80 Gbps"),
        ("Total Non-Blocking Throughput", "40 Gbps"),
        ("Forwarding Rate", "60 Mpps"),
        ("LCM Display", '1.3" touchscreen'),
        ("Power Method", "AC Adapter (150 W, included)"),
        ("Weight", "2.4 kg (5.3 lb)"),
    ]),
)

# ============================================================
# 2) UniFi Flex
# ============================================================
pages["Unifi Supply - Flex.dc.html"] = assemble(
    hero(
        "Flex",
        "5개의 기가비트 포트로 PoE 기기까지 확장하는,<br>손바닥 크기의 스위치.",
        "assets/usw-flex/usw-flex_01-hero-front.png",
        "Flex",
    ),
    why_section(
        "Why Flex",
        "5포트 구성,<br>PoE로 전원부터<br>기기 확장까지",
        "PoE++ 입력 하나로 전원을 받아, 나머지 4포트로 PoE 기기를 확장하는 컴팩트 스위치입니다.",
        [
            ("5개의 1GbE 포트,<br>PoE로 전원 공급",
             "1개 포트로 PoE++/60W 전원을 입력받아 동작하고, 나머지 4개 포트로 PoE+(최대 25W)까지 출력해 기기를 확장합니다."),
            ("10 Gbps 스위칭,<br>어댑터 없이 동작",
             "별도 전원 어댑터 없이 PoE만으로 동작해 배선이 간단하고, 10 Gbps 스위칭 용량으로 소규모 네트워크를 충분히 처리합니다."),
            ("122.5 x 107.1 x 28mm,<br>실외 설치 가능",
             "손바닥 크기로 어디에나 설치할 수 있고, -40°C부터 사용 가능한 실외 등급으로 설계됐습니다."),
        ],
    ),
    design_section(
        "assets/usw-flex/usw-flex_02-ports-diagram.png",
        "Flex 포트 구성",
        "1개의 PoE 입력,<br>4개의 PoE+ 출력",
        "포트 1은 PoE++(최대 60W) 입력 전용이고, 포트 2-5는 각각 최대 25W까지 PoE+ 출력을 지원합니다.<br>업스트림에서 받은 전력으로 카메라, AP 등 PoE 기기를 그대로 확장하세요.",
    ),
    tech_specs_section([
        ("Dimensions", '122.5 x 107.1 x 28 mm (4.8 x 4.2 x 1.1")'),
        ("Port Layout", "(1) 1 GbE RJ45 (PoE++ 입력), (4) 1 GbE RJ45 (PoE+ 출력)"),
        ("Form Factor", "Compact desktop, wall, pole mount"),
        ("Switching Capacity", "10 Gbps"),
        ("Total Non-Blocking Throughput", "5 Gbps"),
        ("Forwarding Rate", "7 Mpps"),
        ("Power Method", "PoE 입력 전용 (어댑터 미포함, PoE++/60W 권장)"),
        ("Weight", "230 g (8.1 oz)"),
    ]),
)

# ============================================================
# 3) UniFi Flex Utility (인클로저 - USW-Flex 전용, 스위치 별도)
# ============================================================
pages["Unifi Supply - Flex Utility.dc.html"] = assemble(
    hero(
        "Flex Utility",
        "UniFi Flex 스위치를 실외에 안전하게 설치하는<br>방수 인클로저.",
        "assets/usw-flexutility/usw-flexutility_01-hero-front.png",
        "Flex Utility",
    ),
    why_section(
        "Why Flex Utility",
        "방수 인클로저 +<br>60W PoE 어댑터<br>한 세트로",
        "Flex 스위치를 비바람으로부터 보호하면서, 실외 어디든 깔끔하게 설치할 수 있습니다.",
        [
            ("USW-Flex 전용<br>방수 인클로저",
             "UniFi Flex 스위치를 실외 환경에서도 안전하게 보호하는 전용 인클로저입니다. (스위치는 별도 구매 상품입니다)"),
            ("60W PoE 어댑터<br>+ 패치 케이블 포함",
             "AC 100-240V 입력, 54V/1.11A 출력의 PoE 어댑터와 연결용 이더넷 패치 케이블이 함께 제공됩니다."),
            ("4kV 서지 보호,<br>나사 고정 케이블",
             "낙뢰 등 전기 서지로부터 내부 기기를 보호하고, 케이블을 나사로 고정해 임의 분리를 막습니다."),
        ],
    ),
    design_section(
        "assets/usw-flexutility/usw-flexutility_02-inside-diagram.png",
        "Flex Utility 내부 구성",
        "PoE 어댑터와<br>스위치를 함께<br>깔끔하게 수납",
        "내부에 PoE 어댑터와 USW-Flex 스위치를 나란히 장착할 수 있는 구조입니다.<br>배선을 인클로저 안에서 정리해 외부 노출 없이 깨끗하게 설치할 수 있습니다.",
    ),
    tech_specs_section([
        ("Product Type", "방수 인클로저 + PoE 어댑터 (USW-Flex 스위치 별도)"),
        ("Compatible Switch", "UniFi Flex (USW-Flex)"),
        ("Dimensions", '249 x 218 x 60 mm (9.8 x 8.6 x 2.4")'),
        ("Weight", "740 g"),
        ("Included Adapter", "AC/DC, 100-240V 입력, 54V/1.11A 출력 (약 60W)"),
        ("Adapter Dimensions", '118.5 x 63 x 34.7 mm (4.7 x 2.5 x 1.4")'),
        ("Surge Protection", "4kV"),
        ("Mounting", "벽면/기둥 마운트"),
    ]),
)

# ============================================================
# 4) UniFi Flex Utility Pro (범용 인클로저 - 스위치/어댑터 별도)
# ============================================================
pages["Unifi Supply - Flex Utility Pro.dc.html"] = assemble(
    hero(
        "Flex Utility Pro",
        "USW-Flex부터 Ultra 시리즈까지,<br>여러 스위치를 수납하는 범용 방수 인클로저.",
        "assets/uacc-flex-utility-pro/uacc-flex-utility-pro_01-hero-front.png",
        "Flex Utility Pro",
    ),
    why_section(
        "Why Flex Utility Pro",
        "IPX6 방수 등급,<br>다양한 스위치를<br>하나의 인클로저에",
        "USW-Flex, USW-Ultra 등 여러 UniFi 스위치를 실외에 설치할 수 있는 범용 인클로저입니다.",
        [
            ("USW-Flex/Ultra 등<br>다양한 스위치 호환",
             "USW-Flex, USW-Flex 2.5G 시리즈, USW-Ultra 60W/210W 등 여러 모델을 선택해 장착할 수 있습니다. (스위치는 별도 구매 상품입니다)"),
            ("IPX6 방수 등급",
             "강한 비바람에도 견디는 IPX6 등급으로 실외 어디든 안심하고 설치할 수 있습니다."),
            ("350 x 220 x 89mm,<br>벽/기둥 마운트 키트 포함",
             "여유로운 내부 공간에 스위치와 전원장치를 함께 수납하고, 벽면·기둥 마운트 키트가 기본 포함됩니다."),
        ],
    ),
    design_section(
        "assets/uacc-flex-utility-pro/uacc-flex-utility-pro_02-closed-front.png",
        "Flex Utility Pro 외관",
        "여유로운 내부 공간,<br>벽/기둥 어디든<br>깔끔하게 마운트",
        "USW-Flex부터 USW-Ultra 210W까지 폭넓게 수납할 수 있는 내부 공간을 갖췄습니다.<br>포함된 마운트 키트로 벽면이나 기둥에 바로 고정해 설치할 수 있습니다.",
    ),
    tech_specs_section([
        ("Product Type", "범용 방수 인클로저 (스위치/전원장치 별도)"),
        ("Compatible Switches", "USW-Flex, USW-Flex-2.5G-5, USW-Flex-2.5G-8,<br>USW-Flex-2.5G-8-PoE, USW-Ultra-60W, USW-Ultra-210W"),
        ("Dimensions", '350 x 220 x 89 mm (13.8 x 8.7 x 3.5")'),
        ("Weight", "1.6 kg"),
        ("Material", "Polycarbonate"),
        ("Weatherproof Rating", "IPX6"),
        ("Mounting", "벽면/기둥 마운트 키트 포함"),
    ]),
)

# ============================================================
# 5) UniFi Pro 8 PoE
# ============================================================
pages["Unifi Supply - Pro 8 PoE.dc.html"] = assemble(
    hero(
        "Pro 8 PoE",
        "6개의 PoE+와 2개의 PoE++ 포트,<br>120W 전력에 10G 업링크까지 갖춘 데스크탑 스위치.",
        "assets/usw-pro-8-poe/usw-pro-8-poe_01-hero-front.png",
        "Pro 8 PoE",
    ),
    why_section(
        "Why Pro 8 PoE",
        "8포트 PoE,<br>120W 전력에<br>10G 업링크까지",
        "AP, 카메라부터 고전력 기기까지 — 넉넉한 PoE 용량과 10G 대역폭을 함께 제공합니다.",
        [
            ("8포트 PoE 구성,<br>120W 전력 용량",
             "6개 포트는 PoE+(최대 32W), 2개 포트는 PoE++(최대 64W)까지 지원해 최대 120W 전력을 공급합니다."),
            ("2개의 10G SFP+,<br>56 Gbps 스위칭 용량",
             "2개의 10G SFP+ 업링크로 상위 네트워크와 연결하고, 56 Gbps 스위칭 용량으로 트래픽을 처리합니다."),
            ("1.3형 터치스크린,<br>Layer 3 라우팅",
             "터치스크린으로 상태를 바로 확인하고, Layer 3 라우팅 기능까지 지원합니다."),
        ],
    ),
    design_section(
        "assets/usw-pro-8-poe/usw-pro-8-poe_02-ports-diagram.png",
        "Pro 8 PoE 포트 구성",
        "6개의 PoE+,<br>2개의 PoE++,<br>2개의 10G SFP+",
        "포트 1-6은 PoE+(최대 32W), 7-8은 PoE++(최대 64W)를 지원합니다.<br>마지막 2개(9-10)는 10G SFP+ 업링크 슬롯으로 상위 네트워크와 고대역폭으로 연결됩니다.",
    ),
    tech_specs_section([
        ("Dimensions", '200 x 248 x 44 mm (7.9 x 9.8 x 1.7")'),
        ("Port Layout", "(6) 1 GbE RJ45 (PoE+), (2) 1 GbE RJ45 (PoE++), (2) 10G SFP+"),
        ("Form Factor", "Desktop, wall"),
        ("Max. PoE Output", "Up to PoE++"),
        ("Total PoE Availability", "120 W"),
        ("Switching Capacity", "56 Gbps"),
        ("Total Non-Blocking Throughput", "28 Gbps"),
        ("LCM Display", '1.3" touchscreen'),
        ("Power Method", "AC Adapter (150 W, included)"),
        ("Weight", "2.1 kg (4.6 lb)"),
    ]),
)

# ============================================================
# 6) UniFi Pro XG 8 PoE
# ============================================================
pages["Unifi Supply - Pro XG 8 PoE.dc.html"] = assemble(
    hero(
        "Pro XG 8 PoE",
        "8개 포트 전부 10G, 최대 60W PoE++까지 —<br>Etherlighting을 갖춘 프로 AV용 스위치.",
        "assets/usw-pro-xg-8-poe/usw-pro-xg-8-poe_01-hero-front.png",
        "Pro XG 8 PoE",
    ),
    why_section(
        "Why Pro XG 8 PoE",
        "8개 포트 전부 10G,<br>155W PoE++까지",
        "영상 제작/AV 환경을 위한 전 포트 10G 스위칭과 넉넉한 PoE++ 전력을 제공합니다.",
        [
            ("8개 포트 전부 10G,<br>200 Gbps 스위칭 용량",
             "8개의 10G RJ45 포트가 10G/5G/2.5G/1G까지 자동 협상하고, 200 Gbps 스위칭 용량으로 대용량 트래픽을 처리합니다."),
            ("포트당 최대 60W,<br>총 155W PoE++",
             "8개 포트 모두 PoE++(최대 60W)를 지원해 총 155W 전력을 카메라, AV 장비 등에 공급합니다."),
            ("Etherlighting,<br>Dante/NDI 프로필 지원",
             "포트별 RGB 상태 표시(Etherlighting)와 Dante, NDI, Q-SYS 프로필을 지원해 AV 환경에 최적화됐습니다."),
        ],
    ),
    design_section(
        "assets/usw-pro-xg-8-poe/usw-pro-xg-8-poe_02-ports-diagram.png",
        "Pro XG 8 PoE 포트 구성",
        "8개의 10G PoE++,<br>2개의 10G SFP+",
        "포트 1-8은 모두 10GbE PoE++(최대 60W)를 지원하고, 마지막 2개(9-10)는 10G SFP+ 업링크 슬롯입니다.<br>영상 제작 장비, AV 인코더 등 고대역폭·고전력 기기를 그대로 연결하세요.",
    ),
    tech_specs_section([
        ("Dimensions", '210.4 x 173.8 x 43.7 mm (8.28 x 6.84 x 1.7")'),
        ("Port Layout", "(8) 10 GbE RJ45 (PoE++), (2) 10G SFP+"),
        ("Form Factor", "Desktop, wall"),
        ("Max. PoE Output", "Up to PoE++"),
        ("Total PoE Availability", "155 W"),
        ("Switching Capacity", "200 Gbps"),
        ("Total Non-Blocking Throughput", "100 Gbps"),
        ("Forwarding Rate", "149 Mpps"),
        ("Power Method", "AC/DC Adapter (210 W, included)"),
        ("Weight", "1.6 kg (3.5 lb)"),
    ]),
)

for filename, content in pages.items():
    with open(f"{OUT_DIR}/{filename}", "w") as f:
        f.write(content)

print(f"{len(pages)}개 페이지 작성 완료:")
for name in pages:
    print(" -", name)
