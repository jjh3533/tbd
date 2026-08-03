"""주어진 .dc.html 파일을 렌더링해서 각 data-screen-label 섹션을 2배
해상도 PNG로 내보낸다. (기존 exports/<slug>/NN-name.png 컨벤션과 동일)

사용법:
    python3 export_sections.py <html_path> <out_dir> "01-hero:Hero" "02-why:Why ..." ...

label 인자를 안 주면 "상세페이지" 자식들의 data-screen-label을 순서대로
읽어서 01, 02 ... 번호를 자동으로 매긴다("상세페이지" 자신은 제외).
"""
import sys
import os
from playwright.sync_api import sync_playwright


def slugify_label(label: str) -> str:
    mapping = {
        "Header": "header", "Hero": "hero", "Design": "design", "Compare": "compare",
        "Tech Specs": "tech-specs", "TBD Seoul": "tbd-seoul",
        "통관 안내": "customs", "배송/반품 안내": "shipping",
        "FAQ": "faq", "Footer": "footer",
    }
    if label in mapping:
        return mapping[label]
    if label.startswith("Why"):
        return "why"
    return label.lower().replace(" ", "-")


def export_sections(html_path: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    url = "file://" + os.path.abspath(html_path)

    with sync_playwright() as p:
        # --no-sandbox: NAS Docker 컨테이너가 root로 실행되는데(별도 USER
        # 지정 없음), Chromium의 자체 샌드박스는 root 권한 컨테이너에서 커널
        # 네임스페이스 제약 때문에 기본적으로 크래시한다 - 로컬 Mac에서도
        # 문제 없이 동작하는 표준적인 완화책이라 환경 분기 없이 항상 켜둠.
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 940, "height": 1200}, device_scale_factor=2)
        page.goto(url, wait_until="networkidle")

        # 최상위 상세페이지 wrapper 바로 아래 자식들 중 data-screen-label을
        # 가진 요소들을 순서대로 가져온다 (상세페이지 자신은 제외).
        handles = page.query_selector_all('[data-screen-label="상세페이지"] > [data-screen-label]')
        print(f"found {len(handles)} sections")
        for idx, el in enumerate(handles, 1):
            label = el.get_attribute("data-screen-label")
            slug = slugify_label(label)
            fname = f"{idx:02d}-{slug}.png"
            el.screenshot(path=os.path.join(out_dir, fname))
            box = el.bounding_box()
            print(f"  {fname}  label={label!r}  size={box['width']:.0f}x{box['height']:.0f}")

        browser.close()


if __name__ == "__main__":
    export_sections(sys.argv[1], sys.argv[2])
