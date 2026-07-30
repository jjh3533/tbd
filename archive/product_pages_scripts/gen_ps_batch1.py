"""Physical Security Batch 1: 카메라 5개
G6 Pro 360 / AI PTZ Industrial / G5 Turret Ultra / G6 Dome / AI Theta
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
# 1) UniFi G6 Pro 360
# ============================================================
pages["Unifi Supply - G6 Pro 360.dc.html"] = assemble(
    hero(
        "G6 Pro 360",
        "4K 360° 파노라마 카메라 — 단일 카메라로 모든 방향을<br>동시 촬영하고 AI 이벤트 감지로 놓치지 않습니다.",
        "assets/uvc-g6-pro-360/uvc-g6-pro-360_01-hero-front.png",
        "G6 Pro 360",
    ),
    why_section(
        "Why G6 Pro 360",
        "360° 전방위 시야,<br>AI 감지로<br>사각지대 없이",
        "4K 360도 파노라마 센서로 모든 방향을 동시에 촬영하고, AI가 사람·차량·패키지를 실시간으로 인식합니다.",
        [
            ("4K 360° 파노라마,<br>8MP 센서",
             "단일 8MP 센서가 360도 전방위 시야를 4K 해상도로 촬영하며, 디워프 기능으로 특정 영역을 평면 뷰로 확인할 수 있습니다."),
            ("AI 이벤트 감지<br>(사람·차량·패키지)",
             "온디바이스 AI가 사람, 차량, 패키지를 실시간으로 구분하고, 스마트 알림으로 중요한 이벤트만 알려줍니다."),
            ("PoE 전원,<br>천장·벽면 마운트",
             "PoE+ 케이블 하나로 전원과 네트워크를 동시 공급받으며, 천장이나 벽면에 설치할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/uvc-g6-pro-360/uvc-g6-pro-360_02-diagram.png",
        "G6 Pro 360 구성",
        "IPX4 방수 등급,<br>적외선 야간 촬영,<br>마이크 내장",
        "IPX4 방수 등급으로 옥내외 설치가 가능하며, 적외선 LED로 최대 10m 거리의 야간 촬영을 지원합니다.<br>마이크가 내장되어 있어 오디오 녹음이 가능하고, microSD 슬롯으로 로컬 저장소를 확장할 수 있습니다.",
    ),
    tech_specs_section([
        ("Dimensions", "⌀139.7 x 54.8 mm (⌀5.5 x 2.2\")"),
        ("Weight", "440 g (15.5 oz)"),
        ("Video Resolution", "4K (3840 x 2160), 8MP 센서, 360° 파노라마"),
        ("Frame Rate", "최대 30 FPS"),
        ("Field of View", "360° 파노라마 (디워프 지원)"),
        ("Night Vision", "적외선 LED, 최대 10 m (33 ft)"),
        ("AI Detection", "사람, 차량, 패키지 온디바이스 감지"),
        ("Audio", "마이크 내장 (스피커 없음)"),
        ("Storage", "microSD 슬롯 (로컬 저장소 확장)"),
        ("Power Method", "PoE+ (802.3at, 최대 13W)"),
        ("Mounting", "Ceiling, Wall (마운트 포함)"),
        ("Weatherproofing", "IPX4 (옥내외 설치 가능)"),
        ("Operating Temperature", "-10 to 50°C (14 to 122°F)"),
    ]),
)

# ============================================================
# 2) UniFi AI PTZ Industrial
# ============================================================
pages["Unifi Supply - AI PTZ Industrial.dc.html"] = assemble(
    hero(
        "AI PTZ Industrial",
        "4K AI PTZ 카메라 — 355° 팬, 110° 틸트, 22배 광학 줌으로<br>넓은 영역을 상세하게 감시합니다.",
        "assets/uvc-ai-ptz/uvc-ai-ptz_01-hero-front.png",
        "AI PTZ Industrial",
    ),
    why_section(
        "Why AI PTZ Industrial",
        "4K 화질,<br>22배 광학 줌,<br>AI 자동 추적",
        "4K 해상도와 22배 광학 줌으로 먼 거리의 피사체를 선명하게 촬영하고, AI가 사람과 차량을 자동으로 추적합니다.",
        [
            ("4K 8MP 센서,<br>22배 광학 줌",
             "8MP 센서가 4K 해상도로 촬영하며, 22배 광학 줌과 16배 디지털 줌을 결합해 최대 352배 확대가 가능합니다."),
            ("355° 팬, 110° 틸트,<br>AI 자동 추적",
             "355도 수평 회전과 110도 수직 틸트로 넓은 영역을 커버하며, AI가 사람과 차량을 자동으로 추적합니다."),
            ("PoE++ 전원,<br>IPX66 옥외용",
             "PoE++ (802.3bt) 케이블로 전원을 공급받으며, IPX66 방수·방진 등급으로 혹독한 옥외 환경에도 적합합니다."),
        ],
    ),
    design_section(
        "assets/uvc-ai-ptz/uvc-ai-ptz_02-diagram.png",
        "AI PTZ Industrial 구성",
        "적외선 50m 야간 촬영,<br>양방향 오디오,<br>산업용 내구성",
        "적외선 LED로 최대 50m 거리의 야간 촬영을 지원하며, 마이크와 스피커가 내장되어 양방향 오디오 통신이 가능합니다.<br>알루미늄 합금 하우징과 IPX66 등급으로 -40°C부터 60°C까지 동작하는 산업용 내구성을 갖췄습니다.",
    ),
    tech_specs_section([
        ("Dimensions", "⌀213 x 313 mm (⌀8.4 x 12.3\")"),
        ("Weight", "4.3 kg (9.5 lb)"),
        ("Video Resolution", "4K (3840 x 2160), 8MP 센서"),
        ("Frame Rate", "최대 30 FPS"),
        ("Optical Zoom", "22배 광학 줌, 16배 디지털 줌 (최대 352배)"),
        ("Pan/Tilt", "355° 팬, 110° 틸트"),
        ("Night Vision", "적외선 LED, 최대 50 m (164 ft)"),
        ("AI Detection", "사람, 차량 감지 및 자동 추적"),
        ("Audio", "마이크 + 스피커 (양방향 오디오)"),
        ("Power Method", "PoE++ (802.3bt, 최대 60W)"),
        ("Mounting", "Wall, Pole, Ceiling (마운트 포함)"),
        ("Weatherproofing", "IP66 (방수·방진)"),
        ("Operating Temperature", "-40 to 60°C (-40 to 140°F)"),
    ]),
)

# ============================================================
# 3) UniFi G5 Turret Ultra
# ============================================================
pages["Unifi Supply - G5 Turret Ultra.dc.html"] = assemble(
    hero(
        "G5 Turret Ultra",
        "4K 터렛 카메라 — 컴팩트한 폼팩터에 4K 화질과<br>향상된 야간 성능을 갖춘 옥외용 카메라.",
        "assets/uvc-g5-turret-ultra/uvc-g5-turret-ultra_01-hero-front.png",
        "G5 Turret Ultra",
    ),
    why_section(
        "Why G5 Turret Ultra",
        "4K 화질,<br>컴팩트한 디자인,<br>향상된 야간 성능",
        "4K 해상도와 f/1.6 대구경 렌즈로 밝고 선명한 영상을 제공하며, 컴팩트한 터렛 디자인으로 눈에 띄지 않게 설치할 수 있습니다.",
        [
            ("4K 8MP 센서,<br>f/1.6 대구경 렌즈",
             "8MP 센서와 f/1.6 대구경 렌즈가 4K 해상도로 밝고 선명한 영상을 제공하며, 저조도 환경에서도 우수한 성능을 발휘합니다."),
            ("103° 화각,<br>적외선 30m 야간 촬영",
             "103도 화각으로 넓은 영역을 촬영하며, 적외선 LED로 최대 30m 거리의 야간 촬영을 지원합니다."),
            ("PoE 전원,<br>IPX4 방수",
             "PoE 케이블 하나로 전원과 네트워크를 동시 공급받으며, IPX4 방수 등급으로 옥내외 설치가 가능합니다."),
        ],
    ),
    design_section(
        "assets/uvc-g5-turret-ultra/uvc-g5-turret-ultra_02-diagram.png",
        "G5 Turret Ultra 구성",
        "컴팩트한 터렛 디자인,<br>마이크 내장,<br>간편한 설치",
        "컴팩트한 터렛 디자인으로 벽면이나 천장에 눈에 띄지 않게 설치할 수 있으며, 마이크가 내장되어 오디오 녹음이 가능합니다.<br>microSD 슬롯으로 로컬 저장소를 확장할 수 있습니다.",
    ),
    tech_specs_section([
        ("Dimensions", "⌀127.6 x 110.5 mm (⌀5.0 x 4.4\")"),
        ("Weight", "370 g (13.1 oz)"),
        ("Video Resolution", "4K (3840 x 2160), 8MP 센서"),
        ("Frame Rate", "최대 30 FPS"),
        ("Lens", "f/1.6 대구경 렌즈"),
        ("Field of View", "103° (수평)"),
        ("Night Vision", "적외선 LED, 최대 30 m (98 ft)"),
        ("Audio", "마이크 내장 (스피커 없음)"),
        ("Storage", "microSD 슬롯 (로컬 저장소 확장)"),
        ("Power Method", "PoE (802.3af, 최대 12W)"),
        ("Mounting", "Wall, Ceiling (마운트 포함)"),
        ("Weatherproofing", "IPX4 (옥내외 설치 가능)"),
        ("Operating Temperature", "-10 to 50°C (14 to 122°F)"),
    ]),
)

# ============================================================
# 4) UniFi G6 Dome
# ============================================================
pages["Unifi Supply - G6 Dome.dc.html"] = assemble(
    hero(
        "G6 Dome",
        "5MP AI 돔 카메라 — AI 이벤트 감지와 IK10 파손 방지로<br>안전하고 스마트한 실내외 감시를 제공합니다.",
        "assets/uvc-g6-dome/uvc-g6-dome_01-hero-front.png",
        "G6 Dome",
    ),
    why_section(
        "Why G6 Dome",
        "5MP AI 감지,<br>IK10 파손 방지,<br>양방향 오디오",
        "5MP 해상도와 AI 이벤트 감지로 스마트한 감시를 제공하며, IK10 파손 방지 등급으로 높은 내구성을 갖췄습니다.",
        [
            ("5MP 센서,<br>AI 이벤트 감지",
             "5MP 센서가 선명한 영상을 제공하며, AI가 사람, 차량, 패키지를 실시간으로 감지하고 스마트 알림을 보냅니다."),
            ("IK10 파손 방지,<br>IPX4 방수",
             "IK10 파손 방지 등급으로 강한 충격에도 견디며, IPX4 방수 등급으로 옥내외 설치가 가능합니다."),
            ("양방향 오디오,<br>PoE 전원",
             "마이크와 스피커가 내장되어 양방향 오디오 통신이 가능하며, PoE 케이블 하나로 전원과 네트워크를 동시 공급받습니다."),
        ],
    ),
    design_section(
        "assets/uvc-g6-dome/uvc-g6-dome_02-diagram.png",
        "G6 Dome 구성",
        "IK10 파손 방지 돔,<br>적외선 야간 촬영,<br>microSD 슬롯",
        "IK10 파손 방지 등급의 돔 하우징으로 파손 위험이 높은 환경에 적합하며, 적외선 LED로 최대 30m 거리의 야간 촬영을 지원합니다.<br>microSD 슬롯으로 로컬 저장소를 확장할 수 있습니다.",
    ),
    tech_specs_section([
        ("Dimensions", "⌀152 x 112 mm (⌀6.0 x 4.4\")"),
        ("Weight", "540 g (19.0 oz)"),
        ("Video Resolution", "5MP (2688 x 1520)"),
        ("Frame Rate", "최대 30 FPS"),
        ("Field of View", "122° (수평)"),
        ("Night Vision", "적외선 LED, 최대 30 m (98 ft)"),
        ("AI Detection", "사람, 차량, 패키지 온디바이스 감지"),
        ("Audio", "마이크 + 스피커 (양방향 오디오)"),
        ("Storage", "microSD 슬롯 (로컬 저장소 확장)"),
        ("Power Method", "PoE (802.3af, 최대 12W)"),
        ("Mounting", "Ceiling, Wall (마운트 포함)"),
        ("Weatherproofing", "IPX4 (옥내외 설치 가능)"),
        ("Vandal Resistance", "IK10 (파손 방지)"),
        ("Operating Temperature", "-10 to 50°C (14 to 122°F)"),
    ]),
)

# ============================================================
# 5) UniFi AI Theta
# ============================================================
pages["Unifi Supply - AI Theta.dc.html"] = assemble(
    hero(
        "AI Theta",
        "AI 멀티 센서 허브 — 4개의 독립 카메라 모듈로<br>360° 커버리지와 AI 감지를 동시에 제공합니다.",
        "assets/uvc-ai-theta-hub/uvc-ai-theta-hub_01-hero-front.png",
        "AI Theta",
    ),
    why_section(
        "Why AI Theta",
        "4개 독립 카메라,<br>360° 커버리지,<br>AI 이벤트 감지",
        "4개의 독립 카메라 모듈이 360도 전방위를 동시에 촬영하고, AI가 사람, 차량, 패키지를 실시간으로 감지합니다.",
        [
            ("4개 독립 카메라,<br>5MP 각",
             "4개의 독립 5MP 카메라 모듈이 각각 다른 방향을 촬영하며, 각 모듈을 개별적으로 조정할 수 있습니다."),
            ("AI 이벤트 감지<br>(사람·차량·패키지)",
             "온디바이스 AI가 사람, 차량, 패키지를 실시간으로 구분하고, 스마트 알림으로 중요한 이벤트만 알려줍니다."),
            ("PoE++ 전원,<br>천장·벽면 마운트",
             "PoE++ 케이블 하나로 전원과 네트워크를 동시 공급받으며, 천장이나 벽면에 설치할 수 있습니다."),
        ],
    ),
    design_section(
        "assets/uvc-ai-theta-hub/uvc-ai-theta-hub_02-diagram.png",
        "AI Theta 구성",
        "4개 모듈 독립 조정,<br>IPX4 방수,<br>마이크 내장",
        "4개의 카메라 모듈을 각각 독립적으로 조정할 수 있어 원하는 방향을 정확하게 커버할 수 있으며, IPX4 방수 등급으로 옥내외 설치가 가능합니다.<br>마이크가 내장되어 있어 오디오 녹음이 가능합니다.",
    ),
    tech_specs_section([
        ("Dimensions", "⌀242 x 156 mm (⌀9.5 x 6.1\")"),
        ("Weight", "1.6 kg (3.5 lb)"),
        ("Video Resolution", "5MP per module (4개 모듈)"),
        ("Frame Rate", "최대 30 FPS per module"),
        ("Field of View", "360° 전방위 (4개 모듈 조합)"),
        ("Night Vision", "적외선 LED, 최대 30 m (98 ft)"),
        ("AI Detection", "사람, 차량, 패키지 온디바이스 감지"),
        ("Audio", "마이크 내장 (스피커 없음)"),
        ("Power Method", "PoE++ (802.3bt, 최대 30W)"),
        ("Mounting", "Ceiling, Wall (마운트 포함)"),
        ("Weatherproofing", "IPX4 (옥내외 설치 가능)"),
        ("Operating Temperature", "-10 to 50°C (14 to 122°F)"),
    ]),
)

# ============================================================

if __name__ == "__main__":
    for filename, content in pages.items():
        path = f"{OUT_DIR}/{filename}"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ {filename}")
    print(f"\n총 {len(pages)}개 페이지 생성 완료")
