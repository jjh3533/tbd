"""U7 In-Wall 상세페이지 생성 (재고 있는 U7 라인업 중 상세페이지 없던 첫 제품).

호텔 객실/사무실 벽면 매립형 AP. 기존 U7 Pro 등과 달리 6GHz 미지원
(2.4/5GHz 듀얼밴드)이며, 2.5GbE 포트 3개(PoE 입력 1 + 데이터/PoE 출력 2)를
내장한 것이 핵심 차별점 - Compare 섹션 없이 Hero/Why/Design/Tech Specs로 구성.
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

why_html = why_section(
    "Why U7 In-Wall",
    "벽 속에 완전히 숨긴<br>Wi-Fi 7 액세스포인트",
    "월플레이트 뒤로 매립되어 배선이 드러나지 않으면서도, 유선 기기까지 함께 연결할 수 있습니다.",
    [
        ("벽면 매립형 디자인,<br>배선 완전 은닉",
         "월플레이트 뒤에 완전히 매립되어 케이블이나 본체가 드러나지 않습니다. 호텔 객실, 사무실 등에 깔끔하게 설치할 수 있습니다."),
        ("4-스트림 Wi-Fi 7,<br>200대 이상 동시접속",
         "2.4/5GHz 듀얼밴드에 4개의 공간 스트림으로, 1,250 ft²(약 35평) 면적에서 200대 이상의 기기를 안정적으로 커버합니다."),
        ("2.5GbE 포트 3개 통합,<br>PoE 스위치 내장",
         "PoE 입력 포트 1개와 2.5GbE 데이터/PoE 출력 포트 2개가 내장돼, 별도 스위치 없이 TV·데스크탑 같은 유선 기기까지 함께 연결됩니다."),
    ],
# Compare 섹션이 없어 Why(회색)/Design(흰색)으로 바꿔 흰/회색 교차 리듬을 맞춘다.
).replace(
    '<section style="padding:100px 60px;" data-screen-label="Why U7 In-Wall">',
    '<section style="padding:100px 60px;background:#F5F4F7;" data-screen-label="Why U7 In-Wall">',
)

pages["Unifi Supply - U7 In-Wall.dc.html"] = assemble(
    hero(
        "U7 In-Wall",
        "호텔 객실, 사무실 벽면에 매립 설치하는<br>3포트 통합 스위치 탑재 Wi-Fi 7 액세스포인트.",
        "assets/u7-iw/u7-iw_01-hero-front.png",
        "U7 In-Wall",
    ),
    why_html,
    design_section(
        "assets/u7-iw/u7-iw_02-diagram.png",
        "U7 In-Wall 구성도",
        "전면 2포트,<br>후면 PoE 입력<br>구조로 설치",
        "후면의 2.5GbE PoE 입력 포트로 벽 속 배선과 연결되고, 전면의 2개 포트(데이터용 1개, PoE+ 출력용 1개)로 유선 기기를 그대로 확장합니다.<br>PoE+ 입력 시에만 전면 포트의 PoE 출력이 활성화됩니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", '137 x 98.7 x 30.2 mm (5.4 x 3.9 x 1.2")'),
        ("Weight", "400 g (14.1 oz)"),
        ("Wi-Fi Standard", "Wi-Fi 7 (802.11be), 듀얼밴드 (5/2.4GHz)"),
        ("Spatial Streams", "4"),
        ("Coverage Area", "115 m² (1,250 ft²)"),
        ("Max. Client Count", "200+"),
        ("MIMO", "5GHz 2x2, 2.4GHz 2x2 (DL/UL MU-MIMO)"),
        ("Max. Data Rate", "5GHz 4.3 Gbps (BW240) · 2.4GHz 688 Mbps (BW40)"),
        ("Ports", "(1) 2.5 GbE RJ45 PoE 입력, (2) 2.5 GbE RJ45 (데이터 / PoE+ 출력)"),
        ("Power Method", "PoE/PoE+ (전면 포트 PoE 출력은 PoE+ 입력 시에만 활성화)"),
        ("Operating Temperature", "-30 to 40°C (-22 to 104°F)"),
        ("Mounting", "벽면 매립형 (월플레이트 포함)"),
    ]),
)

for filename, content in pages.items():
    with open(f"{OUT_DIR}/{filename}", "w") as f:
        f.write(content)

print(f"{len(pages)}개 페이지 작성 완료:")
for name in pages:
    print(" -", name)
