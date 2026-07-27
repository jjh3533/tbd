# 네이버 스마트스토어 상품등록 자동화

`naver_상품등록_템플릿.xlsx`에 상품 정보를 채워넣으면, 이 스크립트가 Google Drive의
"Product Images" / "Product Pages" 폴더에서 이미지를 찾아 업로드하고 커머스API로
상품을 일괄 등록합니다.

## 1. 준비

```bash
pip install -r requirements.txt
```

`config.py`에 아래 값이 채워져 있는지 확인하세요:

- `CLIENT_ID`, `CLIENT_SECRET`: 커머스API센터에서 발급 (`네이버_커머스API_발급_가이드.md` 참고) — 입력 완료
- `SHIPPING_ADDRESS_ID`, `RETURN_ADDRESS_ID`: `address_lookup.py`로 조회한 값 — 입력 완료
- `PRODUCT_IMAGES_DIR`, `PRODUCT_PAGES_DIR`: Google Drive 동기화 폴더 경로 — 입력 완료

## 2. 카테고리 ID 확인

```bash
python category_lookup.py 공유기
python category_lookup.py AP
python category_lookup.py 스위칭허브
```

출력된 `leafCategoryId`를 엑셀 템플릿의 `leafCategoryId` 열에 입력합니다.

## 3. 엑셀 작성

`naver_상품등록_템플릿.xlsx` > `상품데이터` 시트에 상품을 한 행씩 입력합니다.

- `제품이미지_폴더명`: "Product Images" 폴더 안의 폴더명 그대로 (예: `UCG Ultra`, `U7 Pro XG`)
- `상세페이지_폴더명`: "Product Pages" 폴더 안의 폴더명(slug) 그대로 (예: `ucg-ultra`, `u7-pro-xg`)

이미지 선택은 스크립트가 자동으로 처리합니다.

- **대표이미지**: 폴더 내 "Datasheet"/"InTheBox"가 아닌 메인 제품샷 중 번호가 가장 작은 파일
  (예: `..._01.png`)
- **추가이미지**: 대표이미지를 제외한 나머지 이미지 중 최대 4장 (스마트스토어는 대표+추가 4장,
  총 5장까지만 노출하므로 그 이상은 자동으로 잘라냄). 메인 제품샷을 우선하고 남는 자리에
  데이터시트/구성품 이미지를 채움
- **상세페이지**: "Product Pages/<폴더명>" 안의 이미지를 `01-hero`, `02-why`... 번호 순서대로
  이어붙여 하나의 상세페이지로 생성 (영상 파일은 전부 자동 제외)

필수 항목(노란색 열)을 빠짐없이 채워야 스크립트가 해당 행을 처리합니다.

## 4. Dry-run으로 확인

실제로 API를 호출하기 전에, 어떤 이미지가 골라지고 어떤 JSON이 만들어지는지 먼저 확인하세요.

```bash
python main.py --file naver_상품등록_템플릿.xlsx --dry-run
```

콘솔에 대표이미지 경로, 추가이미지 장수, 상세페이지 장수가 출력되니 의도한 파일이 맞는지 확인하세요.

## 5. 실제 등록

```bash
python main.py --file naver_상품등록_템플릿.xlsx
```

한 상품씩 순차적으로: 대표이미지 업로드 → 추가이미지 업로드 → 상세페이지 이미지 업로드 →
상품 등록 API 호출을 수행하고, 성공/실패를 콘솔에 출력합니다.

## 알아두어야 할 것

- **첫 실행은 반드시 상품 1개로 테스트**하세요. 카테고리에 따라 네이버가 추가로 요구하는 항목
  (전자제품 인증정보, 원산지 정보, KC 인증 등)이 있을 수 있고, 이는 API가 돌려주는 에러 메시지를
  보고 `product_builder.py`의 `detail_attribute`에 보강해야 합니다.
- **추가이미지는 최대 4장까지만** 사용됩니다 (`config.MAX_OPTIONAL_IMAGES`). 스마트스토어가
  대표이미지 포함 총 5장까지만 화면에 반영하기 때문입니다. 폴더 안에 사진이 더 많아도 정상입니다.
- **이미지 업로드는 계정당 동시 1건**만 가능합니다 (스크립트는 순차 처리라 문제 없음).
- **옵션은 현재 단일 항목(예: 색상)만** 지원합니다. 색상×사이즈처럼 2개 이상 조합 옵션이
  필요하면 `product_builder.py`의 `build_option_info`를 확장해야 합니다.
- API 호출 IP가 바뀌면 요청이 막힙니다. 커머스API센터 애플리케이션 설정에서 IP를 갱신하세요.
- 이 스키마는 네이버 공식 문서와 커머스API 기술지원 GitHub의 공개 예시를 바탕으로 구성한
  것으로, 필드명이 실제 계정 환경에서 다를 가능성이 있습니다. 에러가 나면 응답 메시지를
  그대로 알려주면 스크립트를 맞춰 수정할 수 있습니다.
