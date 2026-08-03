"""브랜드/제품에 관계없이 재사용하는 상세페이지 생성 엔진.

build_pages.py의 구조 헬퍼(head/hero/why_section/design_section/
tech_specs_section/trust_to_footer)를 받아서, "콘텐츠 브리프" 딕셔너리 하나로
HTML 조립 -> assets 반입 -> PNG export까지 처리한다. GL.iNet Slate 7을
만들 때 썼던 gen_glinet_slate7.py 같은 1회성 스크립트를 매번 새로 쓰지 않아도
되도록, 그 패턴(Hero + Why 3카드 + Design + Tech Specs, Compare 없음)을
일반화한 것. 대시보드 "➕ 신규등록" 하위메뉴 3개(🖼️ 상세페이지 제작/✏️ 상세페이지
편집/🧩 공통영역 편집)가 전부 이 모듈을 직접 호출한다.

브리프 스키마 (전부 dict):
    {
      "brand": "UniFi" | "GL.inet",
      "title": "Slate 7",
      "sku": "GLiNet Slate 7 (GL-BE3600)",       # 선택 - 있으면 파일명
                                                 # ({sku}.html)/브리프 파일명/
                                                 # 에셋 slug의 기준이 됨(title은
                                                 # 사람이 자유롭게 다듬는 마케팅
                                                 # 문구라 파일 식별자로 안 씀).
                                                 # 없으면 title로 대체.
      "tagline": "...<br>...",
      "hero_source": "/절대/경로/원본이미지.jpg",
      "hero_alt": "...",                      # 생략 시 title로 대체
      "why_headline": "...<br>...",
      "why_sub": "...",
      "why_cards": [[heading, body], (3개)],
      "why_bg_gray": true/false,               # Why 섹션 배경(회색) 여부
      "design_source": "/절대/경로/원본이미지.jpg",
      "design_alt": "...",                     # 생략 시 "{title} 상세컷"
      "design_headline": "...<br>...",
      "design_body": "...",
      "specs": [[label, value], ...],
    }

이미지 필드(hero_source/design_source)는 항상 "원본" 절대경로를 받는다 -
write_page()가 매번 assets/<slug>/ 아래로 다시 복사하므로 재생성(브리프 수정
후 다시 생성)해도 항상 최신 원본 기준으로 결과가 나온다.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_pages import (  # noqa: E402
    UNIFI_BRAND, GLINET_BRAND, head, trust_to_footer,
    hero, why_section, design_section, tech_specs_section,
)

import naver_config as _config  # noqa: E402  - TBD_SEOUL_ROOT 기준 경로 (NAS도 동작)

BRANDS = {"UniFi": UNIFI_BRAND, "GL.inet": GLINET_BRAND}

# naver_config.PRODUCT_PAGES_DIR = "<TBD_SEOUL_ROOT>/Product Pages_html/exports"
# 이 모듈은 그 한 단계 위(.dc.html/assets가 있는 폴더)가 필요하다.
PAGES_ROOT = os.path.dirname(_config.PRODUCT_PAGES_DIR)
ASSETS_ROOT = os.path.join(PAGES_ROOT, "assets")
EXPORTS_ROOT = _config.PRODUCT_PAGES_DIR
COMMON_ROOT = os.path.join(PAGES_ROOT, "common")

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")
_LEADING_NUMBER_RE = re.compile(r"^(\d+)")


def list_source_images(image_folder_name: str) -> list[str]:
    """Product Images/<폴더명>/ 안의 이미지 파일 절대경로 목록 (번호순)."""
    folder = os.path.join(_config.PRODUCT_IMAGES_DIR, image_folder_name)
    if not os.path.isdir(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith(_IMAGE_EXTENSIONS)]

    def _key(f):
        m = _LEADING_NUMBER_RE.match(f)
        return int(m.group(1)) if m else 999

    files.sort(key=_key)
    return [os.path.join(folder, f) for f in files]


def _import_asset(src_path: str, slug: str, suffix: str) -> str:
    """원본 이미지를 assets/<slug>/<slug>_<suffix>.<ext>로 복사하고 상대경로를 돌려준다."""
    ext = os.path.splitext(src_path)[1] or ".png"
    dest_dir = os.path.join(ASSETS_ROOT, slug)
    os.makedirs(dest_dir, exist_ok=True)
    dest_name = f"{slug}_{suffix}{ext}"
    shutil.copy2(src_path, os.path.join(dest_dir, dest_name))
    return f"assets/{slug}/{dest_name}"


def build_html(brief: dict, slug: str) -> str:
    brand = BRANDS[brief["brand"]]
    title = brief["title"]

    hero_rel = _import_asset(brief["hero_source"], slug, "01-hero-front")
    design_rel = _import_asset(brief["design_source"], slug, "02-design")

    why_html = why_section(
        f"Why {title}",
        brief["why_headline"],
        brief["why_sub"],
        [tuple(card) for card in brief["why_cards"]],
        bg=bool(brief.get("why_bg_gray", True)),
    )
    design_html = design_section(
        design_rel,
        brief.get("design_alt") or f"{title} 상세컷",
        brief["design_headline"],
        brief["design_body"],
        bg=not brief.get("why_bg_gray", True),
    )

    return (
        head(brand)
        + hero(title, brief["tagline"], hero_rel, brief.get("hero_alt") or title, brand=brand)
        + why_html
        + design_html
        + tech_specs_section([tuple(row) for row in brief["specs"]])
        + trust_to_footer(brand, override_html=_read_common_footer_file(brief["brand"]))
    )


def write_page(brief: dict) -> tuple[str, str]:
    """브리프로 상세페이지를 생성해서 저장. (html_path, slug)를 돌려준다.

    파일명은 "{SKU}.html"(사용자 확정, 2026-08-04) - 예: "GLiNet Slate 7
    (GL-BE3600).html", "UniFi Pro Max 16.html". title이 아니라 sku(NocoDB
    검색으로 상품을 골랐을 때의 SKU - 상품의 안정적인 식별자)를 쓰는 이유는
    title이 페이지에 실제로 노출되는 마케팅 문구라 사람이 자유롭게 다듬는 게
    정상 워크플로우인데, title을 파일명에도 그대로 쓰면 "타이틀을 다듬으면
    파일명이 매번 바뀌고 이미 있던 페이지 대신 새 파일이 생기는" 문제가
    있었기 때문(사용자 실사용 중 발견, 2026-08-04). slug(에셋 폴더명)도 SKU
    기준으로 통일."""
    brand = BRANDS[brief["brand"]]
    title = brief["title"]
    sku = (brief.get("sku") or title).strip()
    slug = slugify(sku)

    html = build_html(brief, slug)
    filename = f"{sku}.html"
    html_path = os.path.join(PAGES_ROOT, filename)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path, slug


def export_pngs(html_path: str, slug: str) -> list[str]:
    """export_sections.py로 섹션별 PNG를 뽑아서 절대경로 목록을 돌려준다.

    재생성 시 섹션 개수/번호가 바뀔 수 있어(예: 헤더 섹션 추가), 기존 PNG를
    먼저 지워야 이전 번호 체계의 파일이 안 지워지고 섞여 남는 걸 막는다."""
    export_dir = os.path.join(EXPORTS_ROOT, slug)
    os.makedirs(export_dir, exist_ok=True)
    for f in os.listdir(export_dir):
        if f.lower().endswith(".png"):
            os.remove(os.path.join(export_dir, f))
    script = os.path.join(_SCRIPT_DIR, "export_sections.py")
    subprocess.run(
        [sys.executable, script, html_path, export_dir],
        check=True, capture_output=True, text=True,
    )
    files = sorted(f for f in os.listdir(export_dir) if f.lower().endswith(".png"))
    return [os.path.join(export_dir, f) for f in files]


def list_completed_pages() -> list[str]:
    """완성된 상세페이지 파일명 목록 (최근 수정순). detail_page_builder.py,
    detail_page_editor.py, smartstore.py(등록대기 매칭용) 전부 이 함수가
    필요해서 여기로 공유.

    파일명은 "{SKU}.html"(2026-08-04부로 확장자 .dc.html에서 변경 - 기존
    파일도 전부 일괄 리네임함)."""
    if not os.path.isdir(PAGES_ROOT):
        return []
    files = [f for f in os.listdir(PAGES_ROOT) if f.endswith(".html")]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(PAGES_ROOT, f)), reverse=True)
    return files


def read_page(filename: str) -> str:
    with open(os.path.join(PAGES_ROOT, filename), encoding="utf-8") as f:
        return f.read()


def write_page_content(filename: str, html: str) -> None:
    """detail_page_editor.py의 "저장하기" 버튼 - write_page()와 달리 브리프가
    아니라 이미 완성된 HTML 텍스트 그대로를 같은 파일명에 덮어쓴다."""
    with open(os.path.join(PAGES_ROOT, filename), "w", encoding="utf-8") as f:
        f.write(html)


# --- 공통영역(TBD Seoul 신뢰뱃지~통관안내~배송/반품 안내~FAQ~Footer) 편집 ---
# build_pages.py의 __EYEBROW__/__STORE__ 같은 플레이스홀더 치환 템플릿 대신,
# 완성된 HTML 텍스트를 브랜드별로 그대로 저장해뒀다가 build_html()이 그대로
# 이어붙인다(공통영역 편집 페이지, 2026-08-04 신설).
_COMMON_FOOTER_FILENAMES = {"UniFi": "unifi-footer.html", "GL.inet": "glinet-footer.html"}


def _common_footer_path(brand_key: str) -> str:
    filename = _COMMON_FOOTER_FILENAMES.get(brand_key)
    if not filename:
        raise ValueError(f"알 수 없는 브랜드: {brand_key}")
    return os.path.join(COMMON_ROOT, filename)


def _read_common_footer_file(brand_key: str) -> str | None:
    """저장된 파일이 있으면 내용을, 없으면 None(호출부가 기존 템플릿으로
    폴백)을 돌려준다."""
    path = _common_footer_path(brand_key)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return None


def read_common_footer(brand_key: str) -> str:
    """공통영역 편집 페이지가 처음 열릴 때 쓰는 함수 - 저장된 게 있으면 그걸,
    없으면 build_pages의 기본 템플릿(지금 라이브에 나가있는 문구)으로 시드해서
    편집 시작점이 항상 "현재 상태"가 되게 한다."""
    saved = _read_common_footer_file(brand_key)
    if saved is not None:
        return saved
    return trust_to_footer(BRANDS[brand_key])


def write_common_footer(brand_key: str, html: str) -> str:
    os.makedirs(COMMON_ROOT, exist_ok=True)
    path = _common_footer_path(brand_key)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


def find_nocodb_record(records: list[dict], identity: str) -> dict | None:
    """identity(보통 상세페이지 파일명에서 ".html"만 뗀 것 = SKU)로 NocoDB
    Products 레코드를 찾는다. Model Number(필드명에 공백 있음 주의,
    `Model_Number`가 아님)도 함께 확인 - 정확일치만 본다(부분일치 아님, 이
    값 자체가 그 필드에서 그대로 복사돼왔기 때문에 느슨하게 볼 필요가 없음)."""
    identity_norm = (identity or "").strip().lower()
    if not identity_norm:
        return None
    for r in records:
        f = r.get("fields", {})
        model = (f.get("Model Number") or "").strip().lower()
        sku = (f.get("SKU") or "").strip().lower()
        if identity_norm in (model, sku) and identity_norm:
            return r
    return None
