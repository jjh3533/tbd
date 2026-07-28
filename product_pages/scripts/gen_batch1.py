import sys
sys.path.insert(0, "/Users/cheil/tbd/product_pages/scripts")
from build_pages import HEAD, TRUST_TO_FOOTER, tech_specs_section

OUT_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages_html"


def hero(title, tagline_html, img_src, img_alt):
    return f'''
  <div style="padding:100px 60px 4px;text-align:center;" data-screen-label="Hero">
    <img src="assets/common/common_logo-symbol.svg" alt="UniFi" style="height:60px;width:auto;display:block;margin:0 auto;">
    <h1 style="font-size:52px;font-weight:700;letter-spacing:-0.03em;line-height:1.15;margin-top:48px;">{title}</h1>
    <div style="margin-top:18px;font-size:21px;color:#696F78;font-weight:400;">{tagline_html}</div>
    <div style="margin-top:56px;">
      <img src="{img_src}" alt="{img_alt}" style="width:100%;height:auto;display:block;">
    </div>
  </div>
'''


def why_section(eyebrow, headline_html, sub_html, cards):
    cards_html = "\n".join(f'''      <div style="padding:36px 28px;background:#fff;border:1px solid #E4E4E9;border-radius:18px;">
        <div style="font-size:13px;color:#3371FB;font-weight:700;margin-bottom:16px;">{i:02d}</div>
        <h3 style="font-size:19px;font-weight:600;margin-bottom:10px;">{h}</h3>
        <p style="font-size:14.5px;color:#696F78;line-height:1.6;">{p}</p>
      </div>''' for i, (h, p) in enumerate(cards, 1))
    return f'''
  <section style="padding:100px 60px;" data-screen-label="{eyebrow}">
    <div style="max-width:520px;margin:0 auto 48px;text-align:center;">
      <div style="font-size:13px;letter-spacing:0.06em;color:#3371FB;font-weight:600;text-transform:uppercase;">{eyebrow}</div>
      <h2 style="font-size:36px;font-weight:700;letter-spacing:-0.02em;margin-top:10px;line-height:1.25;">{headline_html}</h2>
      <p style="margin-top:14px;font-size:17px;color:#696F78;line-height:1.6;">{sub_html}</p>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:32px;">
{cards_html}
    </div>
  </section>
'''


def design_section(img_src, img_alt, headline_html, body_html, bg=True):
    bg_style = "background:#F5F4F7;" if bg else ""
    return f'''
  <section style="padding:100px 60px;{bg_style}" data-screen-label="Design">
    <div style="display:flex;align-items:center;gap:60px;">
      <div style="flex:1;">
        <img src="{img_src}" alt="{img_alt}" style="width:100%;height:auto;display:block;">
      </div>
      <div style="flex:1;">
        <div style="font-size:13px;letter-spacing:0.06em;color:#3371FB;font-weight:600;text-transform:uppercase;margin-bottom:12px;">Design</div>
        <h2 style="font-size:30px;font-weight:700;letter-spacing:-0.02em;line-height:1.3;margin-bottom:16px;">{headline_html}</h2>
        <p style="font-size:16px;color:#696F78;line-height:1.7;">{body_html}</p>
      </div>
    </div>
  </section>
'''


def compare_cell(text, highlight=False, border_top=True, bottom_radius=False):
    bg = "background:rgba(51,113,251,0.06);" if highlight else ""
    bt = "border-top:1px solid #E4E4E9;" if border_top else ""
    br = "border-radius:0 0 12px 12px;" if bottom_radius else ""
    return f'<div style="padding:16px 12px;{bt}text-align:center;font-size:13.5px;{bg}{br}">{text}</div>'


def compare_section(headline_html, sub_html, cols, rows):
    """cols: list of (img_src, alt, name, desc_html, highlight_bool)
       rows: list of (label, [values per col])"""
    n = len(cols)
    header_imgs = "\n".join(
        f'''      <div style="padding:0 16px 20px;text-align:center;height:130px;display:flex;align-items:flex-end;justify-content:center;{"background:rgba(51,113,251,0.06);border-radius:12px 12px 0 0;" if hl else ""}">
        <img src="{img}" alt="{alt}" style="max-width:100%;max-height:100%;object-fit:contain;display:block;">
      </div>''' for img, alt, name, desc, hl in cols)
    name_cells = "\n".join(
        f'''      <div style="padding:0 12px 20px;text-align:center;{"background:rgba(51,113,251,0.06);" if hl else ""}">
        <div style="font-size:16px;font-weight:700;color:#3371FB;margin-bottom:8px;">{name}</div>
        <div style="font-size:12.5px;color:#696F78;line-height:1.5;">{desc}</div>
      </div>''' for img, alt, name, desc, hl in cols)
    row_html_parts = []
    total_rows = len(rows)
    for ridx, (label, values) in enumerate(rows):
        is_last = ridx == total_rows - 1
        label_style = "padding:16px 0;border-top:1px solid #E4E4E9;font-size:13.5px;color:#696F78;"
        if is_last:
            label_style += "border-bottom:1px solid #E4E4E9;"
        row = [f'<div style="{label_style}">{label}</div>']
        for cidx, val in enumerate(values):
            hl = cols[cidx][4]
            bg = "background:rgba(51,113,251,0.06);" if hl else ""
            bt = "border-top:1px solid #E4E4E9;"
            bb = "border-bottom:1px solid #E4E4E9;" if is_last else ""
            brad = "border-radius:0 0 12px 12px;" if (is_last and hl) else ""
            row.append(f'<div style="padding:16px 12px;{bt}{bb}text-align:center;font-size:13.5px;{bg}{brad}">{val}</div>')
        row_html_parts.append("\n      ".join(row))
    rows_html = "\n      ".join(row_html_parts)
    cols_template = " ".join(["1fr"] * n)
    min_width = 200 + n * 160
    return f'''
  <section style="padding:100px 60px;" data-screen-label="Compare">
    <div style="max-width:520px;margin:0 auto 48px;text-align:center;">
      <div style="font-size:13px;letter-spacing:0.06em;color:#3371FB;font-weight:600;text-transform:uppercase;">Compare</div>
      <h2 style="font-size:36px;font-weight:700;letter-spacing:-0.02em;margin-top:10px;line-height:1.25;">{headline_html}</h2>
      <p style="margin-top:14px;font-size:17px;color:#696F78;line-height:1.6;">{sub_html}</p>
    </div>
    <div style="overflow-x:auto;">
    <div style="display:grid;grid-template-columns:170px {cols_template};min-width:{min_width}px;">
      <div></div>
{header_imgs}
      <div></div>
{name_cells}
      {rows_html}
    </div>
    </div>
  </section>
'''


# ============================================================
# 1) UniFi Pro Max 16
# ============================================================
pm16_hero = hero(
    "Pro Max 16",
    "12개의 기가비트 포트부터 10G SFP+ 업링크까지,<br>Layer 3 라우팅을 지원하는 랙마운트 애그리게이션 스위치.",
    "assets/usw-pro-max-16/usw-pro-max-16_01-hero-front.png",
    "Pro Max 16",
)

pm16_why = why_section(
    "Why Pro Max 16",
    "18개의 포트,<br>10G 업링크까지<br>하나의 스위치에",
    "1GbE부터 2.5GbE, 10G SFP+까지 — 늘어나는 네트워크 트래픽을 위한 애그리게이션 스위치입니다.",
    [
        ("18포트 구성,<br>84 Gbps 스위칭 용량",
         "(12) 1 GbE RJ45, (4) 2.5 GbE RJ45, (2) 10G SFP+ 업링크까지 — 84 Gbps 스위칭 용량으로 여유롭게 처리합니다."),
        ("Layer 3 라우팅,<br>VLAN 1,000개",
         "IPv4 정적 라우트와 최대 1,000개 VLAN을 지원해 네트워크를 세그먼트로 나누고 트래픽을 직접 라우팅합니다."),
        ("랙/데스크탑/벽걸이 +<br>1.3형 터치스크린",
         "1U 랙마운트부터 데스크탑, 벽걸이까지 설치 환경에 맞춰 선택하고, 1.3형 터치스크린으로 상태를 바로 확인합니다."),
    ],
)

pm16_design = design_section(
    "assets/usw-pro-max-16/usw-pro-max-16_02-ports-diagram.png",
    "Pro Max 16 포트 구성",
    "12개의 1GbE와<br>4개의 2.5GbE,<br>2개의 10G SFP+",
    "포트 1-12는 1 GbE, 13-16은 2.5 GbE, 마지막 2개(17-18)는 10G SFP+ 업링크 슬롯입니다.<br>서버나 NAS, 상위 스위치 연결에 10G 대역폭을 그대로 활용할 수 있습니다.",
)

pm16_tech_specs = tech_specs_section([
    ("Dimensions", '325.1 x 160 x 43.7 mm (12.8 x 6.3 x 1.7")'),
    ("Port Layout", "(12) 1 GbE RJ45, (4) 2.5 GbE RJ45, (2) 10G SFP+"),
    ("Form Factor", "Rack mount (1U), desktop, wall"),
    ("Switching Capacity", "84 Gbps"),
    ("Total Non-Blocking Throughput", "42 Gbps"),
    ("Forwarding Rate", "62 Mpps"),
    ("Supported VLANs", "1,000"),
    ("LCM Display", '1.3" touchscreen'),
    ("Max. Power Consumption", "25 W"),
    ("Power Method", "AC/DC Adapter (included)"),
    ("Weight", "1.95 kg (4.3 lb)"),
])

# ============================================================
# 2) UniFi Pro Max 16 PoE
# ============================================================
pm16poe_hero = hero(
    "Pro Max 16 PoE",
    "12개의 PoE+ 포트와 4개의 PoE++ 포트,<br>최대 180W 전력까지 — Layer 3 스위칭까지 하나로.",
    "assets/usw-pro-max-16-poe/usw-pro-max-16-poe_01-hero-front.png",
    "Pro Max 16 PoE",
)

pm16poe_why = why_section(
    "Why Pro Max 16 PoE",
    "18개의 포트,<br>PoE++까지<br>하나의 스위치에",
    "AP, 카메라, 인터컴까지 — 넉넉한 PoE 용량으로 여러 기기에 동시에 안정적인 전력을 공급합니다.",
    [
        ("18포트 구성,<br>84 Gbps 스위칭 용량",
         "(12) 1 GbE RJ45, (4) 2.5 GbE RJ45, (2) 10G SFP+ 업링크까지 — Pro Max 16과 동일한 스위칭 성능입니다."),
        ("최대 180W,<br>PoE++ 전력 용량",
         "12개 포트는 PoE+, 4개 포트는 PoE++까지 지원해 최대 180W 전력을 여러 기기에 동시에 공급합니다."),
        ("랙/데스크탑/벽걸이 +<br>1.3형 터치스크린",
         "1U 랙마운트부터 데스크탑, 벽걸이까지 설치 환경에 맞춰 선택하고, 1.3형 터치스크린으로 상태를 바로 확인합니다."),
    ],
)

pm16poe_design = design_section(
    "assets/usw-pro-max-16-poe/usw-pro-max-16-poe_02-ports-diagram.png",
    "Pro Max 16 PoE 포트 구성",
    "12개의 PoE+,<br>4개의 PoE++,<br>2개의 10G SFP+",
    "포트 1-12는 PoE+ 출력(최대 32W), 13-16은 PoE++ 출력(최대 60W)을 지원합니다.<br>총 180W의 PoE 전력 용량 안에서 필요한 만큼 기기를 연결해 전력을 공급할 수 있습니다.",
)

pm16poe_tech_specs = tech_specs_section([
    ("Dimensions", '325.1 x 160 x 43.7 mm (12.8 x 6.3 x 1.7")'),
    ("Port Layout", "(12) 1 GbE RJ45 (PoE+), (4) 2.5 GbE RJ45 (PoE++), (2) 10G SFP+"),
    ("Form Factor", "Rack mount (1U), desktop, wall"),
    ("Max. PoE Output", "Up to PoE++"),
    ("Total PoE Availability", "180 W"),
    ("Switching Capacity", "84 Gbps"),
    ("Total Non-Blocking Throughput", "42 Gbps"),
    ("Supported VLANs", "1,000"),
    ("LCM Display", '1.3" touchscreen'),
    ("Max. Power Consumption", "25 W (본체), 210 W (PoE 출력 포함)"),
    ("Power Method", "AC Adapter (included)"),
    ("Weight", "2.1 kg (4.6 lb)"),
])

# Compare (shared between Pro Max 16 / Pro Max 16 PoE)
compare_cols_base = [
    ("assets/usw-pro-max-16/usw-pro-max-16_01-hero-front.png", "Pro Max 16", "Pro Max 16",
     "10G 업링크를 갖춘<br>Layer 3 애그리게이션 스위치"),
    ("assets/usw-pro-max-16-poe/usw-pro-max-16-poe_01-hero-front.png", "Pro Max 16 PoE", "Pro Max 16 PoE",
     "동일한 스위칭 성능에<br>최대 180W PoE++ 전력까지"),
]
compare_rows = [
    ("Dimensions", ['325.1 x 160 x 43.7 mm<br>(12.8 x 6.3 x 1.7")'] * 2),
    ("Port Layout", [
        "(12) 1 GbE RJ45<br>(4) 2.5 GbE RJ45<br>(2) 10G SFP+",
        "(12) 1 GbE RJ45 (PoE+)<br>(4) 2.5 GbE RJ45 (PoE++)<br>(2) 10G SFP+",
    ]),
    ("PoE 지원", ["미지원", "최대 180W (PoE+/PoE++)"]),
    ("Switching Capacity", ["84 Gbps", "84 Gbps"]),
    ("Non-Blocking Throughput", ["42 Gbps", "42 Gbps"]),
    ("Power Method", ["25W AC/DC 어댑터", "210W AC 어댑터"]),
    ("Weight", ["1.95 kg (4.3 lb)", "2.1 kg (4.6 lb)"]),
]

def make_compare(highlight_idx):
    cols = [(img, alt, name, desc, i == highlight_idx) for i, (img, alt, name, desc) in enumerate(compare_cols_base)]
    return compare_section(
        "UniFi Switching<br>Pro Max 16 · Pro Max 16 PoE",
        "PoE 전력 공급이 필요한지에 따라 선택하세요. 포트 구성과 스위칭 성능은 동일합니다.",
        cols, compare_rows,
    )

pm16_compare = make_compare(0)
pm16poe_compare = make_compare(1)


def assemble(hero_html, why_html, design_html, compare_html, tech_specs_html):
    return HEAD + hero_html + why_html + design_html + compare_html + tech_specs_html + TRUST_TO_FOOTER


pm16_page = assemble(pm16_hero, pm16_why, pm16_design, pm16_compare, pm16_tech_specs)
pm16poe_page = assemble(pm16poe_hero, pm16poe_why, pm16poe_design, pm16poe_compare, pm16poe_tech_specs)

with open(f"{OUT_DIR}/Unifi Supply - Pro Max 16.dc.html", "w") as f:
    f.write(pm16_page)
with open(f"{OUT_DIR}/Unifi Supply - Pro Max 16 PoE.dc.html", "w") as f:
    f.write(pm16poe_page)

print("Pro Max 16 / Pro Max 16 PoE pages written.")
