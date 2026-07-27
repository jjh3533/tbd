"""
UniFi 제품 이미지 크롤러 — 남은 115개 제품 처리용

전제:
- 이 스크립트는 `product_slug_map.json`, `done_products_slugs.json`,
  `remaining_urls.py`가 있는 폴더(Drive 동기화되는 tbd 폴더)에 함께 두고 실행합니다.
- 기본적으로 이 스크립트가 놓인 폴더 바로 아래 "Product Images"에 저장하므로,
  스크립트를 tbd 동기화 폴더 안에 두기만 하면 자동으로 Drive에 올라갑니다.
  (PC마다 홈 디렉터리 경로가 달라도 상관없음 — 예: /Users/jay/tbd, /Users/cheil/tbd 등)

설치:
    pip install requests beautifulsoup4 playwright
    playwright install chromium

실행:
    python crawl_remaining_images.py --test 3     # 먼저 3개 제품만 테스트
    python crawl_remaining_images.py               # 전체 115개 실행
    python crawl_remaining_images.py --playwright-only  # JSON 지름길 안 쓰고 바로 브라우저 방식
    python crawl_remaining_images.py --output-dir "/path/to/Product Images"  # 저장 경로 직접 지정

동작 방식:
1. 제품마다 먼저 techspecs.ui.com의 Next.js JSON 데이터 엔드포인트를 시도합니다
   (탭 클릭 없이 requests만으로 원본 이미지 URL을 뽑아낼 수 있는지 시도, 빠름).
2. JSON 방식이 실패하거나 이미지를 하나도 못 찾으면, 자동으로 Playwright로
   실제 페이지를 열어 Marketing Images / In The Box / Datasheet 탭을 각각
   클릭하며 이미지를 수집하는 방식으로 넘어갑니다(인계 문서에 정리된 방식).
3. 제품 하나가 끝날 때마다 done_products_slugs.json에 바로 기록하므로,
   중간에 멈춰도 이어서 실행하면 이미 끝난 제품은 건너뜁니다.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import requests
from bs4 import BeautifulSoup

# ── 경로 설정 ────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
SLUG_MAP_FILE = SCRIPT_DIR / "product_slug_map.json"
DONE_FILE = SCRIPT_DIR / "done_products_slugs.json"
FAILED_FILE = SCRIPT_DIR / "failed_products.json"

# 기본 저장 위치: 스크립트가 놓인 폴더(=tbd 동기화 폴더) 바로 아래 "Product Images".
# --output-dir 옵션으로 덮어쓸 수 있음.
DEFAULT_PRODUCT_IMAGES_DIR = SCRIPT_DIR / "Product Images"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

IMAGE_URL_RE = re.compile(
    r'https?://[^\s"\'\\]+?\.(?:png|jpe?g|webp)(?:\?[^\s"\'\\]*)?',
    re.IGNORECASE,
)
INVALID_CHARS_RE = re.compile(r'[/:*?"<>|]')


def dedup_url_variants(urls: list[str]) -> list[str]:
    """같은 이미지가 해상도/쿼리 파라미터만 다르게 여러 번 나오는 걸 하나로 합침.

    예: foo.png?w=640, foo.png?w=1280, foo.png?w=1920 -> 그중 제일 큰 것만 남김.
    쿼리 스트링을 뗀 (scheme+host+path)를 키로 묶고, w/width/size/q 파라미터가
    있으면 가장 큰 값을 가진 URL을 대표로 선택. 없으면 처음 나온 것을 사용.
    """
    groups: dict[str, list[str]] = {}
    order: list[str] = []
    for u in urls:
        parts = urlsplit(u)
        key = f"{parts.scheme}://{parts.netloc}{parts.path}"
        if key not in groups:
            order.append(key)
            groups[key] = []
        groups[key].append(u)

    def score(u: str) -> int:
        qs = parse_qs(urlsplit(u).query)
        for k in ("w", "width", "size", "q", "quality"):
            if k in qs:
                try:
                    return int(qs[k][0])
                except ValueError:
                    pass
        return -1  # 쿼리에 크기 힌트가 없으면 최저 우선순위(먼저 나온 것 사용)

    result = []
    for key in order:
        variants = groups[key]
        if len(variants) == 1:
            result.append(variants[0])
            continue
        best_score = max(score(v) for v in variants)
        if best_score == -1:
            result.append(variants[0])
        else:
            result.append(next(v for v in variants if score(v) == best_score))
    return result


# ── 유틸 ────────────────────────────────────────────────────────────────
def sanitize_folder_name(name: str) -> str:
    return INVALID_CHARS_RE.sub("-", name).strip()


def load_slug_map() -> dict:
    records = json.loads(SLUG_MAP_FILE.read_text(encoding="utf-8"))
    return {r["techspecs_slug"]: r for r in records}


def load_done() -> dict:
    if DONE_FILE.exists():
        return json.loads(DONE_FILE.read_text(encoding="utf-8"))
    return {}


def save_done(done: dict) -> None:
    DONE_FILE.write_text(
        json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_failed() -> list:
    if FAILED_FILE.exists():
        return json.loads(FAILED_FILE.read_text(encoding="utf-8"))
    return []


def save_failed(failed: list) -> None:
    FAILED_FILE.write_text(
        json.dumps(failed, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def parse_product_urls(urls_file: str = "remaining_urls.py") -> list[str]:
    # <urls_file> 안의 PRODUCT_URLS 리스트를 그대로 가져다 씀.
    # 기본값은 남은 115개(remaining_urls.py). 전체 186개를 새로 돌리려면
    # all_product_urls.py를 지정.
    ns: dict = {}
    exec((SCRIPT_DIR / urls_file).read_text(encoding="utf-8"), ns)
    return ns["PRODUCT_URLS"]


def url_to_category_slug(url: str) -> tuple[str, str]:
    parts = urllib.parse.urlparse(url).path.strip("/").split("/")
    # .../unifi/<category>/<slug>
    return parts[-2], parts[-1]


def save_with_dedup(folder: Path, base_name: str, ext: str, content: bytes) -> str:
    """기존 파일명 규칙(<slug>-N.ext, 겹치면 <slug>-N (1).ext)을 따라 저장."""
    folder.mkdir(parents=True, exist_ok=True)
    candidate = f"{base_name}{ext}"
    n = 1
    while (folder / candidate).exists():
        candidate = f"{base_name} ({n}){ext}"
        n += 1
    (folder / candidate).write_bytes(content)
    return candidate


def download(session: requests.Session, url: str, referer: str) -> bytes | None:
    try:
        resp = session.get(
            url, headers={**HEADERS, "Referer": referer}, stream=True, timeout=30
        )
        resp.raise_for_status()
        return resp.content
    except requests.RequestException as e:
        print(f"    ! 다운로드 실패 {url}: {e}")
        return None


# ── 방법 1: Next.js JSON 데이터 엔드포인트 ─────────────────────────────
_build_id_cache: dict[str, str] = {}


def get_build_id(session: requests.Session, sample_url: str) -> str | None:
    if "id" in _build_id_cache:
        return _build_id_cache["id"]
    try:
        resp = session.get(sample_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("script", id="__NEXT_DATA__")
        build_id = None
        if tag and tag.string:
            build_id = json.loads(tag.string).get("buildId")
        if not build_id:
            m = re.search(r'"buildId":"([^"]+)"', resp.text)
            build_id = m.group(1) if m else None
        if build_id:
            _build_id_cache["id"] = build_id
        return build_id
    except Exception as e:
        print(f"  ! buildId 조회 실패: {e}")
        return None


# 3개 탭에 대응하는 JSON 필드. Datasheet = techSpecs, In The Box = whatsInTheBoxMedia,
# Marketing Images = gallery. (pageProps.regionalProducts는 다른 지역용 변형 제품이라
# 같은 이미지가 다시 통째로 들어있음 - 반드시 제외해야 함)
MEDIA_SECTIONS = ("gallery", "whatsInTheBoxMedia", "techSpecs")


def extract_product_media(product: dict) -> list[str]:
    urls: list[str] = []
    for section in MEDIA_SECTIONS:
        items = ((product or {}).get(section) or {}).get("items") or []
        for item in items:
            u = ((item or {}).get("data") or {}).get("url")
            if u and re.search(r"\.(png|jpe?g|webp)(\?|$)", u, re.I):
                urls.append(u)
    return list(dict.fromkeys(urls))


def try_json_method(
    session: requests.Session, url: str, category: str, slug: str
) -> list[str]:
    build_id = get_build_id(session, url)
    if not build_id:
        return []
    data_url = (
        f"https://techspecs.ui.com/_next/data/{build_id}/unifi/{category}/{slug}.json"
        f"?category={category}&product={slug}&productLine=unifi"
    )
    try:
        resp = session.get(data_url, headers={**HEADERS, "Referer": url}, timeout=20)
        if resp.status_code == 404:
            # buildId가 바뀌었을 수 있음 - 캐시 지우고 한 번만 재시도
            _build_id_cache.clear()
            build_id = get_build_id(session, url)
            if not build_id:
                return []
            data_url = (
                f"https://techspecs.ui.com/_next/data/{build_id}/unifi/{category}/{slug}.json"
                f"?category={category}&product={slug}&productLine=unifi"
            )
            resp = session.get(data_url, headers={**HEADERS, "Referer": url}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        print(f"  ! JSON 조회 실패: {e}")
        return []

    product = (data.get("pageProps") or {}).get("product") or {}
    urls = extract_product_media(product)

    if not urls:
        # 구조가 예상과 다를 때만 - product 객체 범위 안에서만(regionalProducts 제외)
        # 정규식으로 한 번 더 시도
        blob = json.dumps(product)
        urls = list(dict.fromkeys(IMAGE_URL_RE.findall(blob)))
        urls = [u for u in urls if not re.search(r"/(icons?|logos?|favicon)/", u, re.I)]

    # 혹시 남아있을 해상도별 쿼리파라미터 중복 정리
    urls = dedup_url_variants(urls)
    return urls


# ── 방법 2: Playwright로 탭 클릭 (fallback) ────────────────────────────
_playwright_ctx = {}


def get_browser():
    if "browser" not in _playwright_ctx:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        _playwright_ctx["pw"] = pw
        _playwright_ctx["browser"] = browser
    return _playwright_ctx["browser"]


def close_browser():
    if "browser" in _playwright_ctx:
        _playwright_ctx["browser"].close()
        _playwright_ctx["pw"].stop()


def largest_from_srcset(srcset: str) -> str | None:
    candidates = []
    for part in srcset.split(","):
        bits = part.strip().split()
        if not bits:
            continue
        u = bits[0]
        width = 0
        if len(bits) > 1 and bits[1].endswith("w"):
            try:
                width = int(bits[1][:-1])
            except ValueError:
                width = 0
        candidates.append((width, u))
    if not candidates:
        return None
    return max(candidates, key=lambda c: c[0])[1]


def try_playwright_method(url: str) -> list[str]:
    browser = get_browser()
    page = browser.new_page(user_agent=HEADERS["User-Agent"])
    found: list[str] = []
    try:
        page.goto(url, timeout=45000, wait_until="networkidle")
        for tab_name in ["Marketing Images", "In The Box", "Datasheet"]:
            tab = page.get_by_text(tab_name, exact=True)
            if tab.count() == 0:
                continue
            tab.first.click()
            page.wait_for_timeout(1200)

            # 다운로드 버튼/링크 우선
            for a in page.query_selector_all("a[download], a[href*='download']"):
                href = a.get_attribute("href")
                if href and re.search(r"\.(png|jpe?g|webp)(\?|$)", href, re.I):
                    found.append(urllib.parse.urljoin(url, href))

            # 없으면 img의 srcset 최대 해상도 또는 src
            for img in page.query_selector_all("img"):
                srcset = img.get_attribute("srcset")
                src = img.get_attribute("src")
                chosen = largest_from_srcset(srcset) if srcset else src
                if chosen and re.search(r"\.(png|jpe?g|webp)(\?|$)", chosen, re.I):
                    found.append(urllib.parse.urljoin(url, chosen))
    except Exception as e:
        print(f"  ! Playwright 처리 실패: {e}")
    finally:
        page.close()

    return list(dict.fromkeys(found))


# ── 메인 ────────────────────────────────────────────────────────────────
def process_product(
    session: requests.Session, url: str, slug_map: dict, output_dir: Path
) -> tuple[str, list[str]] | None:
    category, slug = url_to_category_slug(url)
    record = slug_map.get(slug)
    if not record:
        print(f"  ! product_slug_map.json에서 slug '{slug}'를 찾을 수 없음 - 건너뜀")
        return None

    product_name = record["name"]
    print(f"[{slug}] {product_name}")

    media_urls = try_json_method(session, url, category, slug)
    method = "json"
    if not media_urls:
        print("  JSON 방식 실패/0건 -> Playwright로 전환")
        media_urls = try_playwright_method(url)
        method = "playwright"

    if not media_urls:
        print("  !! 이미지를 하나도 찾지 못함")
        return slug, []

    folder = output_dir / sanitize_folder_name(product_name)
    saved_files = []
    for i, media_url in enumerate(media_urls, start=1):
        ext_match = re.search(r"\.(png|jpe?g|webp)", media_url, re.I)
        ext = f".{ext_match.group(1).lower()}" if ext_match else ".png"
        content = download(session, media_url, url)
        if content is None:
            continue
        fname = save_with_dedup(folder, f"{slug}-{i}", ext, content)
        saved_files.append(fname)

    print(f"  -> {len(saved_files)}개 저장 ({method} 방식) : {folder}")
    return slug, saved_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=int, default=None, help="처음 N개만 실행")
    parser.add_argument(
        "--playwright-only", action="store_true", help="JSON 지름길 건너뛰고 바로 Playwright 사용"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help='저장할 "Product Images" 폴더 경로 직접 지정 (기본값: 스크립트 폴더/Product Images)',
    )
    parser.add_argument(
        "--urls-file",
        type=str,
        default="remaining_urls.py",
        help="사용할 PRODUCT_URLS 파일 (기본값: remaining_urls.py = 남은 115개."
        " 전체 186개를 새로 돌리려면 all_product_urls.py 지정)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="done_products_slugs.json에 이미 완료로 기록된 제품도 건너뛰지 않고"
        " 다시 크롤링(전체 재크롤링용). 새로 받은 파일은 기존 파일과 이름이"
        " 겹치면 '(1)'처럼 접미사가 붙어 추가 저장되니, 완전히 깨끗하게 다시"
        " 받고 싶으면 Product Images 폴더의 해당 제품 하위 폴더를 먼저 비워두세요.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_PRODUCT_IMAGES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"저장 위치: {output_dir}")

    slug_map = load_slug_map()
    done = load_done()
    failed = load_failed()
    product_urls = parse_product_urls(args.urls_file)

    if args.test:
        product_urls = product_urls[: args.test]

    session = requests.Session()

    global try_json_method
    if args.playwright_only:
        try_json_method = lambda *a, **k: []  # noqa: E731

    processed = 0
    try:
        for url in product_urls:
            category, slug = url_to_category_slug(url)
            if slug in done and not args.force:
                continue

            result = process_product(session, url, slug_map, output_dir)
            if result is None:
                continue
            slug, files = result
            if files:
                done[slug] = files
                save_done(done)
            else:
                if slug not in failed:
                    failed.append(slug)
                save_failed(failed)

            processed += 1
            time.sleep(0.8)  # 서버 부담 줄이기
    finally:
        close_browser()

    print(f"\n완료: 이번 실행에서 {processed}개 제품 처리")
    print(f"누적 완료: {len(done)} / 186")
    if failed:
        print(f"실패(재시도 필요): {failed}")


if __name__ == "__main__":
    main()
