"""
로컬 이미지 파일을 커머스API 서버에 업로드하고, 상품 등록에 쓸 수 있는 URL을 받아온다.

실제 폴더 구조 (Google Drive 동기화 폴더 기준):
  Product Images/<제품폴더명>/
      UniFi_Photos_..._01.png   <- 메인 제품샷 (대표이미지 후보)
      UniFi_Photos_..._02.png
      ...
      UniFi_Photos_..._Datasheet_..._01.png   <- 스펙시트 이미지
      UniFi_Photos_..._InTheBox_..._01.png    <- 구성품 이미지
      ...(.mp4 영상은 자동 제외)
  Product Pages/<slug>/
      01-hero.png, 02-why.png, ..., 10-footer.png   <- 860px 상세페이지 이미지 (순서대로 이어붙임)

주의: 상품 이미지 업로드 API는 "스토어 계정당 동시에 1건"만 처리 가능하다.
여러 장을 올릴 때도 반드시 이전 요청의 응답을 받은 뒤 다음 요청을 보내야 한다
(이 스크립트는 순차적으로 호출하므로 별도 조치 불필요).
"""
import mimetypes
import os
import re
import time

import requests

import naver_config as config

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")
EXTRA_KEYWORDS = ("datasheet", "inthebox", "in_the_box", "in the box")

_TRAILING_NUMBER_RE = re.compile(r"(\d+)(?=\.\w+$)")
_LEADING_NUMBER_RE = re.compile(r"^(\d+)")


def _trailing_number(filename: str) -> int:
    m = _TRAILING_NUMBER_RE.search(filename)
    return int(m.group(1)) if m else 999


def _leading_number(filename: str) -> int:
    m = _LEADING_NUMBER_RE.match(filename)
    return int(m.group(1)) if m else 999


def _is_image(filename: str) -> bool:
    return filename.lower().endswith(IMAGE_EXTENSIONS)


def _is_extra_category(filename: str) -> bool:
    lower = filename.lower()
    return any(k in lower for k in EXTRA_KEYWORDS)


def resolve_product_image_folder(folder_name: str) -> str:
    return os.path.join(config.PRODUCT_IMAGES_DIR, folder_name)


def resolve_detail_page_folder(folder_name: str) -> str:
    return os.path.join(config.PRODUCT_PAGES_DIR, folder_name)


def pick_representative_image(folder_path: str):
    """
    'Datasheet'/'InTheBox'가 포함되지 않은 메인 제품샷 그룹 중 번호가 가장 작은 파일을 대표이미지로 선택.
    """
    if not os.path.isdir(folder_path):
        return None

    main_group = [
        f for f in os.listdir(folder_path)
        if _is_image(f) and not _is_extra_category(f)
    ]
    if not main_group:
        return None

    main_group.sort(key=_trailing_number)
    return os.path.join(folder_path, main_group[0])


def list_optional_images(folder_path: str, exclude_path=None, limit=None) -> list:
    """
    대표이미지로 선택된 파일을 제외한 나머지 이미지(메인샷 나머지 + 데이터시트 + 구성품)를 순서대로 반환.
    영상(.mp4 등)은 자동 제외된다.

    스마트스토어는 대표이미지 1장 + 추가이미지 최대 4장까지만 노출하므로,
    기본값(config.MAX_OPTIONAL_IMAGES)만큼만 잘라서 반환한다. 메인 제품샷을 우선하고
    남는 자리에 데이터시트/구성품 이미지를 채운다.
    """
    if not os.path.isdir(folder_path):
        return []

    if limit is None:
        limit = config.MAX_OPTIONAL_IMAGES

    exclude_name = os.path.basename(exclude_path) if exclude_path else None

    files = [f for f in os.listdir(folder_path) if _is_image(f) and f != exclude_name]
    files.sort(key=lambda f: (_is_extra_category(f), _trailing_number(f)))
    if limit is not None:
        files = files[:limit]
    return [os.path.join(folder_path, f) for f in files]


def list_detail_page_images(folder_path: str) -> list:
    """
    '01-hero.png', '02-why.png', ... 처럼 앞자리 번호로 정렬된 860px 상세페이지 이미지 목록.
    """
    if not os.path.isdir(folder_path):
        return []

    files = [f for f in os.listdir(folder_path) if _is_image(f)]
    files.sort(key=_leading_number)
    return [os.path.join(folder_path, f) for f in files]


# 커머스API 이미지 업로드는 "1회 호출당 최대 10MB"로 제한된다.
# PNG 원본은 장당 2~4MB가 흔해서 4~10장을 한 번에 보내면 쉽게 초과한다.
# 안전하게 여유를 두고 청크(chunk) 단위로 나눠서 여러 번 호출한 뒤 URL을 순서대로 이어붙인다.
MAX_UPLOAD_BYTES = 9_000_000  # 서버 한도(10,485,760바이트)보다 여유를 둔 안전값
MAX_FILES_PER_CALL = 10


def _chunk_by_size(file_paths: list, max_bytes: int = MAX_UPLOAD_BYTES, max_files: int = MAX_FILES_PER_CALL) -> list:
    """파일 목록을 (누적 용량 <= max_bytes, 개수 <= max_files) 조건으로 나눠 청크 리스트를 만든다."""
    chunks = []
    current: list = []
    current_size = 0

    for p in file_paths:
        size = os.path.getsize(p)
        would_exceed_size = current and (current_size + size > max_bytes)
        would_exceed_count = current and (len(current) + 1 > max_files)
        if would_exceed_size or would_exceed_count:
            chunks.append(current)
            current = []
            current_size = 0
        current.append(p)
        current_size += size

    if current:
        chunks.append(current)
    return chunks


def _upload_batch(token: str, file_paths: list) -> list:
    """단일 API 호출로 file_paths(전부 용량 한도 이내)를 업로드하고 URL 리스트를 돌려준다."""
    headers = {"Authorization": f"Bearer {token}"}
    files = []
    opened = []
    try:
        for p in file_paths:
            fh = open(p, "rb")
            opened.append(fh)
            mime = mimetypes.guess_type(p)[0] or "application/octet-stream"
            files.append(("imageFiles", (os.path.basename(p), fh, mime)))

        resp = requests.post(config.IMAGE_UPLOAD_URL, headers=headers, files=files, timeout=120)
        if resp.status_code >= 300:
            raise RuntimeError(f"{resp.status_code} {resp.text}")
        body = resp.json()
    finally:
        for fh in opened:
            fh.close()

    # 응답 구조 예: {"images": [{"url": "..."}]} 또는 리스트 형태 - 방어적으로 처리
    urls = []
    images = body.get("images") if isinstance(body, dict) else body
    for item in images:
        url = item.get("url") if isinstance(item, dict) else item
        urls.append(url)
    return urls


def upload_images(token: str, file_paths: list) -> list:
    """file_paths(로컬 경로 리스트)를 업로드하고 반환된 URL 리스트를 순서대로 돌려준다.

    10MB 업로드 한도를 넘지 않도록 자동으로 여러 번에 나눠 호출한다
    (스토어 계정당 동시 1건 제한을 지키기 위해 청크는 항상 순차적으로 호출한다).
    """
    if not file_paths:
        return []

    urls = []
    for chunk in _chunk_by_size(file_paths):
        urls.extend(_upload_batch(token, chunk))
    return urls


def upload_with_retry(token: str, file_paths: list, retries: int = 2) -> list:
    last_err = None
    for attempt in range(retries + 1):
        try:
            return upload_images(token, file_paths)
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1)
    raise RuntimeError(f"이미지 업로드 실패 ({file_paths}): {last_err}")
