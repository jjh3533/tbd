"""GL.iNet Slate 7 (GL-BE3600) 상세페이지 생성 - GL.iNet 브랜드 최초의 상세페이지.

기존 UniFi 페이지들과 동일한 4섹션 패턴(Compare 없이 Hero/Why/Design/Tech Specs,
흰/회색 배경 교차)을 build_pages.py의 브랜드 파라미터(GLINET_BRAND)로 재현한다.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_pages import (
    GLINET_BRAND, head, trust_to_footer, tech_specs_section,
    hero, why_section, design_section,
)

OUT_DIR = os.path.expanduser(
    "~/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html"
)


def assemble(hero_html, why_html, design_html, tech_specs_html):
    return head(GLINET_BRAND) + hero_html + why_html + design_html + tech_specs_html + trust_to_footer(GLINET_BRAND)


pages = {}

why_html = why_section(
    "Why Slate 7",
    "손바닥만한 크기에 담은<br>Wi-Fi 7 트래블 라우터",
    "터치스크린 하나로 네트워크 상태부터 VPN까지 직접 제어하는, GL.iNet의 최신 여행용 라우터입니다.",
    [
        ("Wi-Fi 7 듀얼밴드,<br>최대 3.5Gbps 속도",
         "5GHz 2,882Mbps · 2.4GHz 688Mbps의 이론상 최대 속도를 지원하며, MLO(멀티링크 오퍼레이션)로 두 밴드를 동시에 묶어 더 안정적인 연결을 제공합니다."),
        ("정전식 터치스크린으로<br>원터치 제어",
         "본체 전면 화면에서 이더넷/리피터/테더링/셀룰러 모드를 바로 전환하고, VPN 클라이언트 연결과 실시간 속도, Wi-Fi QR 공유까지 화면 터치만으로 처리합니다."),
        ("2.5G 포트 2개 +<br>USB-C PD 전원",
         "LAN/WAN 겸용 2.5G 포트 2개와 USB 3.0 포트를 갖춰 호텔·에어비앤비 유선 인터넷도 그대로 확장하고, USB-C PD(5V/9V/12V)로 보조배터리·범용 어댑터 어디서나 전원을 연결할 수 있습니다."),
    ],
).replace(
    '<section style="padding:100px 60px;" data-screen-label="Why Slate 7">',
    '<section style="padding:100px 60px;background:#F5F4F7;" data-screen-label="Why Slate 7">',
)

pages["GLiNET Supply - Slate 7.dc.html"] = assemble(
    hero(
        "Slate 7",
        "터치스크린으로 제어하는 Wi-Fi 7 트래블 라우터.<br>어디서나 빠르고 안전한 인터넷을 손안에.",
        "assets/glinet-slate-7/glinet-slate-7_01-hero-front.png",
        "GL.iNet Slate 7",
        brand=GLINET_BRAND,
    ),
    why_html,
    design_section(
        "assets/glinet-slate-7/glinet-slate-7_02-ports.jpg",
        "Slate 7 포트 구성",
        "LAN/WAN 겸용 2.5G 포트 2개,<br>USB-C PD로 전원까지",
        "2.5G RJ45 포트 2개는 LAN/WAN 어느 쪽으로도 쓸 수 있어 호텔 객실이나 사무실의 유선 인터넷을 그대로 공유·확장합니다. USB 3.0 포트로 외장 저장장치나 스마트폰 테더링도 바로 연결되고, USB-C PD(5V/3A·9V/3A·12V/2.5A) 입력이라 노트북 어댑터나 보조배터리로도 전원을 공급할 수 있습니다.",
        bg=False,
    ),
    tech_specs_section([
        ("Dimensions", "130 x 91 x 34 mm"),
        ("Weight", "295 g"),
        ("CPU", "Qualcomm 쿼드코어 1.1GHz"),
        ("Memory / Storage", "1GB DDR4 RAM / 512MB NAND Flash"),
        ("Wi-Fi Standard", "Wi-Fi 7 (802.11be), 듀얼밴드 (5/2.4GHz), MLO 지원"),
        ("Max. Data Rate", "5GHz 2,882 Mbps · 2.4GHz 688 Mbps"),
        ("Ports", "2.5G RJ45 x2 (LAN/WAN 겸용), USB 3.0 x1"),
        ("Display", "정전식 터치스크린 (모드 전환 · VPN 제어 · Wi-Fi QR 공유 · 속도 측정)"),
        ("Power", "USB-C PD 입력 (5V/3A, 9V/3A, 12V/2.5A)"),
        ("VPN", "WireGuard/OpenVPN 클라이언트·서버, 상용 VPN 원터치 연동"),
        ("OS", "GL.iNet 펌웨어 (OpenWrt 기반)"),
    ]),
)

for filename, content in pages.items():
    with open(os.path.join(OUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content)

print(f"{len(pages)}개 페이지 작성 완료:")
for name in pages:
    print(" -", name)
