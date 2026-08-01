"""
네이버 커머스API 자격증명 및 매장 설정.

파일명이 naver_config.py 인 이유: tbd 폴더(NocoDB/Streamlit 프로젝트)에도
자체 config.py 가 있어서, 같은 폴더로 합쳤을 때 이름이 겹치지 않도록
이 프로젝트 쪽 설정 파일만 naver_config.py 로 이름을 구분했습니다.
naver_smartstore_uploader 쪽 스크립트들은 전부 `import naver_config as config`
형태로 이 파일을 불러옵니다.

시크릿(CLIENT_ID/CLIENT_SECRET)은 이 파일에 하드코딩하지 않고 config.py의
_get_secret()을 그대로 재사용해 .env에서 읽습니다 (NocoDB/Scrape.do 시크릿과
동일한 방식). 로컬에서는 .env에 NAVER_CLIENT_ID/NAVER_CLIENT_SECRET을
채워두세요 (.env.example 참고).
"""
import os

from config import _get_secret

# --- 커머스API 인증 정보 (apicenter.commerce.naver.com 에서 발급) ---
# required=False인 이유: 이 모듈은 main.py(네이버 등록 파이프라인, 로컬 전용)뿐
# 아니라 image_uploader.py(대시보드 "이미지 다운로드" 기능)도 import한다.
# NAS 배포본은 커머스API 시크릿이 없고 애초에 등록 파이프라인을 그쪽에서 돌리지도
# 않으므로, 여기서 필수로 걸면 PRODUCT_IMAGES_DIR 하나 읽으려고 import하는 것만으로
# 대시보드 전체가 기동 실패한다 (실제로 NAS 배포 중 발견함). CLIENT_ID/SECRET을
# 실제로 쓰는 main.py 쪽에서만 값이 있는지 확인하면 된다.
CLIENT_ID = _get_secret("NAVER_CLIENT_ID", required=False)
CLIENT_SECRET = _get_secret("NAVER_CLIENT_SECRET", required=False)

# --- 배송/반품지 정보 (스마트스토어센터 > 판매자정보 > 배송지 관리에 등록되어 있어야 함) ---
# 아래 값들은 "주소록 조회 API"(GET /external/v1/seller/addressbooks)로 확인 후 채워넣으세요.
SHIPPING_ADDRESS_ID = int(os.environ.get("NAVER_SHIPPING_ADDRESS_ID", "200519179"))  # 상품출고지 (RELEASE)
RETURN_ADDRESS_ID = int(os.environ.get("NAVER_RETURN_ADDRESS_ID", "200519180"))  # 반품교환지 (REFUND_OR_EXCHANGE)

# --- 배송 기본값 ---
DELIVERY_COMPANY = "ACE"  # 택배사 코드: ACE Express Inc. ("택배사 코드.xls" 공식 코드표 기준)
DEFAULT_RETURN_DELIVERY_FEE = 40000
DEFAULT_EXCHANGE_DELIVERY_FEE = 80000

# 직접수령(방문수령): deliveryInfo.visitAddressId 필드 자체를 아예 넣지 않으면
# "직접수령 불가능"으로 등록된다 (product_builder.py 참고). 0을 넣으면 네이버가
# "존재하지 않는 방문수령 주소"라며 등록/수정 요청을 거부하니 주의.

# --- 상품 필수 부가정보 기본값 (모든 카테고리 공통 필수 항목) ---
MINOR_PURCHASABLE = True  # 미성년자 구매 가능 여부

AS_PHONE_NUMBER = "010-5938-3577"  # A/S 문의 전화번호 - 실제 고객센터 번호로 수정 권장
AS_GUIDE_CONTENT = "제품 문의 및 A/S는 스마트스토어 문의하기를 이용해주세요."

ORIGIN_AREA_CODE = "0204000"  # 수입산>북아메리카(북미)>미국 (origin_lookup.py로 조회한 값)
ORIGIN_COUNTRY_NAME = "미국"  # 모든 UniFi 제품의 실제 생산국(미국산)으로 통일

# --- 상품정보제공고시 (공정거래위원회 표시사항) ---
# UniFi 네트워크 장비는 notice_lookup.py 조회 결과 "OFFICE_APPLIANCES(사무용기기)" 유형에 해당.
PRODUCT_INFO_NOTICE_TYPE = "OFFICE_APPLIANCES"
MANUFACTURER_NAME = "Ubiquiti Inc."
WARRANTY_POLICY_TEXT = "1년 (제조사 정책에 따름, 상세페이지 참조)"
NOT_APPLICABLE_TEXT = "상세페이지 참조"  # 정격전압/소비전력/크기/무게 등 표기 생략 시 관용적으로 쓰는 문구
IMPORTER_NAME = "TBD Seoul/티비디서울"

# --- 이미지 업로드 API ---
IMAGE_UPLOAD_URL = "https://api.commerce.naver.com/external/v1/product-images/upload"

# --- 상품 등록 API ---
PRODUCT_API_URL = "https://api.commerce.naver.com/external/v2/products"

# --- 카테고리 조회 API ---
CATEGORY_API_URL = "https://api.commerce.naver.com/external/v1/categories"

# --- 이미지 개수 제한 ---
# 스마트스토어는 대표이미지 1장 + 추가이미지 최대 4장(이미지2~5)까지만 노출된다.
# 폴더에 사진이 더 많아도 이 개수만큼만 잘라서 업로드한다.
MAX_OPTIONAL_IMAGES = 4

# --- 상품 이미지 / 상세페이지 원본 폴더 (구글드라이브 동기화 폴더) ---
# 맥 두 대(다른 macOS 계정)에서 같은 구글 드라이브 계정을 쓰므로, 홈 디렉토리만
# os.path.expanduser로 자동 치환해 어느 기기에서 실행하든 그대로 동작하게 함.
#
# NAS(도커) 배포본은 Google Drive CloudStorage 마운트가 없는 대신, Synology
# Drive로 같은 내용을 /volume1/docker/nicegui/dev/smartstore에 동기화해뒀고
# docker-compose.yml이 리포 루트 전체(`.:/app`)를 마운트해서 컨테이너 안에서는
# /app/dev/smartstore로 보인다. .env에 TBD_SEOUL_ROOT를 설정하면 그 경로를
# 우선 쓴다 (NAS만 설정, 맥 두 대는 미설정 상태로 기본값 그대로 사용).
_DEFAULT_TBD_SEOUL_ROOT = os.path.expanduser(
    "~/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul"
)
_GOOGLE_DRIVE_TBD_ROOT = _get_secret("TBD_SEOUL_ROOT", required=False) or _DEFAULT_TBD_SEOUL_ROOT
PRODUCT_IMAGES_DIR = f"{_GOOGLE_DRIVE_TBD_ROOT}/Product Images"
PRODUCT_PAGES_DIR = f"{_GOOGLE_DRIVE_TBD_ROOT}/Product Pages_html/exports"

try:
    from naver_config_local import *  # noqa  # 개인 설정으로 위 값들을 덮어쓰고 싶을 때 사용
except ImportError:
    pass
