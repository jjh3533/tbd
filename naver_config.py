"""
네이버 커머스API 자격증명 및 매장 설정.

파일명이 naver_config.py 인 이유: tbd 폴더(NocoDB/Streamlit 프로젝트)에도
자체 config.py 가 있어서, 같은 폴더로 합쳤을 때 이름이 겹치지 않도록
이 프로젝트 쪽 설정 파일만 naver_config.py 로 이름을 구분했습니다.
naver_smartstore_uploader 쪽 스크립트들은 전부 `import naver_config as config`
형태로 이 파일을 불러옵니다.

절대 이 파일에 실제 값을 커밋/공유하지 마세요.
실제 값은 naver_config_local.py 를 만들어 덮어쓰거나, 환경변수로 주입하는 것을 권장합니다.
"""
import os

# --- 커머스API 인증 정보 (apicenter.commerce.naver.com 에서 발급) ---
CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "1vFKnRKBe0NiO9JrNcUjaM")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "$2a$04$LDmR2Ke7JxwHYKrRDuSejO")

# --- 배송/반품지 정보 (스마트스토어센터 > 판매자정보 > 배송지 관리에 등록되어 있어야 함) ---
# 아래 값들은 "주소록 조회 API"(GET /external/v1/seller/addressbooks)로 확인 후 채워넣으세요.
SHIPPING_ADDRESS_ID = int(os.environ.get("NAVER_SHIPPING_ADDRESS_ID", "200519179"))  # 상품출고지 (RELEASE)
RETURN_ADDRESS_ID = int(os.environ.get("NAVER_RETURN_ADDRESS_ID", "200519180"))  # 반품교환지 (REFUND_OR_EXCHANGE)

# --- 배송 기본값 ---
DELIVERY_COMPANY = "CJGLS"  # 택배사 코드 - 실제 이용 택배사에 맞게 수정
DEFAULT_RETURN_DELIVERY_FEE = 3000
DEFAULT_EXCHANGE_DELIVERY_FEE = 6000

# --- 상품 필수 부가정보 기본값 (모든 카테고리 공통 필수 항목) ---
MINOR_PURCHASABLE = True  # 미성년자 구매 가능 여부

AS_PHONE_NUMBER = "010-5938-3577"  # A/S 문의 전화번호 - 실제 고객센터 번호로 수정 권장
AS_GUIDE_CONTENT = "제품 문의 및 A/S는 스마트스토어 문의하기를 이용해주세요."

ORIGIN_AREA_CODE = "0200037"  # 수입산>아시아>중국 (origin_lookup.py로 조회한 값)
ORIGIN_COUNTRY_NAME = "중국"  # 대부분의 UniFi 제품 생산국. 제품별로 다르면 엑셀에 열 추가해서 조정

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
PRODUCT_IMAGES_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Images"
PRODUCT_PAGES_DIR = "/Users/cheil/Library/CloudStorage/GoogleDrive-jjh3533@gmail.com/내 드라이브/TBD Seoul/Product Pages"

try:
    from naver_config_local import *  # noqa  # 개인 설정으로 위 값들을 덮어쓰고 싶을 때 사용
except ImportError:
    pass
