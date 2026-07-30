import sys
sys.path.insert(0, "/Users/cheil/tbd/product_pages/scripts")
from build_pages import HEAD, TRUST_TO_FOOTER, tech_specs_section
from gen_batch1 import hero, why_section, design_section, assemble

OUT_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html"

flexxg_hero = hero(
    "Flex 10 GbE",
    "5포트 중 4개가 10GbE — 손바닥만한 크기에 담은<br>멀티기가 스위칭.",
    "assets/usw-flex-xg/usw-flex-xg_01-hero-front.png",
    "Flex 10 GbE",
)

flexxg_why = why_section(
    "Why Flex 10 GbE",
    "작은 크기에,<br>10GbE 4포트를<br>그대로 담았습니다",
    "NAS나 워크스테이션 등 10GbE가 필요한 소규모 공간을 위한 컴팩트 스위치입니다.",
    [
        ("4개의 10GbE +<br>1개의 업링크 포트",
         "4개의 10 GbE RJ45 포트로 NAS, 워크스테이션 등을 연결하고, 1개의 1 GbE 포트로 상위 네트워크와 연결합니다."),
        ("PoE+ 또는 USB-C<br>전원으로 유연하게",
         "업링크 포트로 PoE+ 전원을 입력받거나, USB Type-C(5V/5A) 어댑터로 단독 구동할 수 있습니다."),
        ("135 x 185 x 32mm,<br>컴팩트 데스크탑 디자인",
         "책상 위든 벽면이든 자리를 거의 차지하지 않는 크기로, 필요한 곳 어디에나 설치할 수 있습니다."),
    ],
)

flexxg_design = design_section(
    "assets/usw-flex-xg/usw-flex-xg_02-ports-diagram.png",
    "Flex 10 GbE 포트 구성",
    "1개의 업링크,<br>4개의 10GbE 포트",
    "포트 1은 1 GbE PoE+ 입력 전용, 포트 2-5는 10 GbE RJ45로 구성됩니다.<br>업링크 하나로 상위 네트워크와 연결하고, 나머지 4개 포트로 고대역폭 기기를 직접 연결하세요.",
    bg=False,
)

flexxg_tech_specs = tech_specs_section([
    ("Dimensions", '135 x 185 x 32 mm (5.3 x 7.3 x 1.3")'),
    ("Port Layout", "(1) 1 GbE RJ45, (4) 10 GbE RJ45"),
    ("Form Factor", "Compact desktop, wall"),
    ("Switching Capacity", "82 Gbps"),
    ("Total Non-Blocking Throughput", "41 Gbps"),
    ("Forwarding Rate", "61 Mpps"),
    ("Supported VLANs", "1,000"),
    ("Max. Power Consumption", "25 W"),
    ("Power Method", "(1) PoE+ 입력 또는 (1) USB Type-C, 5V DC, 5A"),
    ("Weight", "1.2 kg (2.7 lb)"),
])

# Compare 섹션 없이: Why -> Design -> Tech Specs -> (공용 섹션)
flexxg_page = HEAD + flexxg_hero + flexxg_why + flexxg_design + flexxg_tech_specs + TRUST_TO_FOOTER

with open(f"{OUT_DIR}/Unifi Supply - Flex 10 GbE.dc.html", "w") as f:
    f.write(flexxg_page)

print("Flex 10 GbE page written.")
