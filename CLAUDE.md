# 프로젝트 인계 문서

지난 세션들의 상세 작업 이력(시간순, 무엇을 왜 했는지)은 `HISTORY.md` 참고 —
이 문서는 "지금 상태"만 빠르게 파악하기 위한 용도입니다.

## 1. 프로젝트 개요

- **목적/종류**: "TBD Seoul" — 미국에서 Ubiquiti UniFi 네트워크 장비를 병행수입(해외직구)해서 네이버 스마트스토어에 재판매하는 1인 사업의 자동화 시스템. 가격 모니터링, 상품 등록, 상세페이지 생성, 대시보드로 구성.
- **⚠️ 운영 원칙: 실사용은 항상 my.tbd.kr(NAS)에서** — 사용자는 로컬에서 대시보드를 직접 켜서 쓸 일이 없고, 모든 기능을 my.tbd.kr로 해결하고 싶어함(2026-08-03 명시). 새 기능을 만들 때 "로컬 전용"으로 남겨두는 걸 기본값으로 삼지 말 것 - NAS 배포까지 끝내야 실제로 완료된 것. 로컬에서 코드를 고치고 검증하는 건 개발 과정일 뿐, 기능 자체는 NAS에도 필요한 시크릿/패키지를 갖춰서 my.tbd.kr에서 동작하게 만드는 게 원칙. 이 때문에 NAS `.env`에도 `NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET`을 실제로 채워넣음(2026-08-03) — 예전엔 "NAS는 네이버 시크릿 없음"이 전제였지만 더 이상 아님. PNG Export도 2026-08-03부터 NAS Dockerfile에 Playwright + 헤드리스 Chromium을 추가해 my.tbd.kr에서 동작한다(아래 참고) - 이제 로컬 전용으로 남은 기능은 없음.
- **기술 스택**: Python 3 (로컬 Mac은 3.14, NAS Docker는 3.11), NiceGUI(대시보드), NocoDB(DB, Airtable에서 이전), requests/BeautifulSoup4(스크래핑), yfinance(환율), APScheduler(자동 동기화 스케줄러), Playwright(헤드리스 크롬 - 상세페이지 HTML→PNG 렌더링), openpyxl(엑셀 템플릿), 네이버 커머스API, Docker + Synology Container Manager, Cloudflare Tunnel
- **디렉토리**: `/Users/cheil/Desktop/dev/tbd` (git 저장소, GitHub `jjh3533/tbd` — **private 레포**, 로컬 git만 사용, GitHub 푸시 안 함). 2026-07-31에 `~/tbd`에서 이 위치로 이동함. **맥 두 대에서 사용** — 다른 한 대(`jay` 계정)는 아직 `/Users/jay/tbd`에 있을 수 있음, 두 기기 경로를 맞추려면 그쪽도 동일하게 옮길 것. 코드에 홈 디렉토리를 직접 하드코딩하지 말고 `os.path.expanduser("~/...")`로 작성할 것 (`naver_config.py`의 `PRODUCT_IMAGES_DIR`/`PRODUCT_PAGES_DIR` 참고) — 두 기기 모두 같은 구글 드라이브 계정(`jjh3533@gmail.com`)을 쓰므로 이 방식이면 기기별 설정 없이 그대로 동작함

## 2. 프로젝트 구조

### 루트 핵심 파일
| 파일 | 역할 |
|---|---|
| `sync_engine.py` | 스크래핑/동기화/포맷팅 로직 - 프레임워크 독립 모듈. `start_background_scheduler()`로 매일 09:00 KST 전체 동기화 + 4시간마다 확인 필요 상품만 재조회하는 자동화도 포함 |
| `dashboard/` | NiceGUI 대시보드 (`theme.py`, `layout.py`, `components.py`(시맨틱 버튼/헤더/다이얼로그 헬퍼), `app.py`, `pages/{home,category,brand,register,detail_page_builder,inventory,needs_check,orders,sync,smartstore,settings,purchase_orders,shipping}.py`, `deploy/{Dockerfile,docker-compose.yml}`) |
| `config.py` | 공용 시크릿 로더 (`.env`), NocoDB/Scrape.do/Telegram 값 |
| `naver_config.py` | 네이버 커머스API 설정 (CLIENT_ID/SECRET은 `.env`에서, NAS엔 없어도 되도록 `required=False`). `PRODUCT_IMAGES_DIR`/`PRODUCT_PAGES_DIR`는 `.env`의 `TBD_SEOUL_ROOT`로 오버라이드 가능 (맥은 미설정=Google Drive CloudStorage 경로, NAS는 `/app/dev/smartstore`로 설정) |
| `nocodb_client.py` | NocoDB REST v2용 Airtable 호환 어댑터 |
| `auth.py` | 네이버 OAuth2 bearer token 발급 (bcrypt 기반 전자서명) |
| `naver_order_api.py` | 네이버 Pay-Order/Claims API 클라이언트 (Phase C 주문관리용). `get_product_orders()`는 자유 날짜범위 조회 시 실제로 재현되는 429 Too Many Requests에 지수 백오프 재시도(최대 5회) 내장 |
| `naver_delivery_companies.py`/`naver_delivery_companies.json` | 스마트스토어센터 공식 택배사 코드표(222개, `smartstore/delivery-companies_*.xls`에서 1회성 추출)를 정적 JSON으로 보관. `/shipping`의 택배사 선택 드롭다운이 사용, 기본값 "ACE"(ACEexpress) |
| `ace_express_tracking.py` | ACE Express(acedp.co.kr) 공개 송장조회 크롤러 - 로그인 불필요(사이트 자체가 "It's free!"로 안내하는 공개 기능), `GET /welcome/Track/hno/{송장번호}`를 BeautifulSoup으로 파싱. `/orders` 새로고침이 국제배송/통관/국내배송 단계 판정에 사용 |
| `main.py` | 엑셀(`naver_상품등록_템플릿.xlsx`) 기반 네이버 상품 등록 파이프라인 |
| `product_builder.py` / `image_uploader.py` | 등록 payload 생성 / 이미지 업로드. **자동 카테고리 선택 및 검색 키워드 추가 기능 내장** |
| `product_keywords.py` | 카테고리별 자동 leafCategoryId 선택 및 검색 최적화 키워드 생성 모듈 |
| `brief_generator.py` | Claude(claude-sonnet-5)로 상세페이지 브리프(태그라인/Why 3카드/Design/Tech Specs) 초안을 생성. CheapSub 중계 API(`https://api.cheapsub.im`, Anthropic Messages API 호환) 경유, `CHEAPSUB_API_KEY` 필요(`.env`, 없으면 이 기능만 비활성화). 대시보드 `/detail-page-builder`의 "🤖 브리프 초안 생성" 버튼이 호출. **my.tbd.kr에도 배포됨** — NAS `Dockerfile`에 `anthropic` 패키지 추가(재빌드 필요) + NAS `.env`에 `CHEAPSUB_API_KEY` 설정 완료 |
| `update_categories.py` | 기등록 상품의 카테고리를 더 적합한 카테고리로 일괄 변경 |
| `update_product_names_with_keywords.py` | 기등록 상품명에 검색 키워드 일괄 추가 |
| `run_pipeline.py` | main.py → sync_naver_ids_to_nocodb.py → update_price_stock.py 순차 실행 |
| `sync_naver_ids_to_nocodb.py` | `TARGET_PRODUCTS` 매핑, 네이버 채널상품번호를 NocoDB에 반영 |
| `update_price_stock.py` | NocoDB → 네이버 가격/재고 동기화 (영문 필드명 `sale_price` 사용). `{SKU} Black` 짝 로우가 있으면 화이트/블랙 옵션별로 다른 가격/재고 반영 - 옵션이 이미 있으면 갱신, 없으면 신규 생성. `TARGET_PRODUCTS`(수작업 등록 리스트)에 있는 상품만 대상 |
| `sync_naver_price.py` | `/smartstore` 페이지의 "가격/재고 업데이트" 버튼용 - `update_price_stock.py`와 로직은 동일(그 안의 함수를 그대로 재사용)하지만 `TARGET_PRODUCTS` 없이 `Naver_Product_No`가 있는 전체 상품이 대상. `dry_run`/`limit` 파라미터로 안전장치 있음 |
| `sync_naver_status.py` | 네이버의 실제 `saleStatus`를 조회해 NocoDB `SalesStatus` 필드에 미러링(반대 방향은 안 함). `/smartstore` 페이지 통계·필터가 이 필드를 사용 |
| `create_color_variant_rows.py` | 화이트 기준 로우에서 `{SKU} Black`/`{Model Number}-B` 블랙 변형 로우를 생성하는 스크립트 (Category/Weight_KG/MSRP_USD/Naver_Product_No는 화이트와 동일하게 복사, 구매처 ID는 비워둠) |
| `search_amazon_candidates.py` | ASIN 없는 상품을 상품명+모델명으로 아마존 검색해(Scrape.do Amazon Search 플러그인) 후보를 CSV로 뽑아주는 스크립트. NocoDB에 자동으로 쓰지 않고 사람이 검토하는 용도. 실제 검색 로직은 `retailer_search.py`로 이관됨 |
| `official_scrapers/` | 구매대행 신규 브랜드 공홈 크롤러 레지스트리 (`fetch_product(brand, url)`). `shopify.py`(Shopify `.json` 엔드포인트, 브랜드 무관 공용) / `unifi.py`(store.ui.com `__NEXT_DATA__` 파싱). 현재 UniFi/GL.inet만 등록됨, 새 브랜드는 `__init__.py`의 `_BRAND_SCRAPERS`에 한 줄 추가 |
| `retailer_search.py` | 상품명+모델명으로 아마존/B&H/Adorama에서 후보를 찾는 검색 모듈. B&H/Adorama는 전용 검색 플러그인이 없어 사이트 검색결과 페이지의 URL 슬러그로 매칭(카드 `<a>`에 텍스트가 없는 경우가 많아서) |
| `update_live_customs_image.py` | 라이브 상세페이지의 통관 안내 섹션 이미지만 교체 |
| `common_settings.py`/`common_settings.json` | 브랜드 로고/문구 + 구매·배송 안내 문구(초기불량 보장 기간, 배송 소요일)를 코드 수정 없이 바꾸는 JSON 설정 저장소. 대시보드 `/settings`가 읽고 쓰고, `product_pages/scripts/build_pages.py`가 `UNIFI_BRAND`/`GLINET_BRAND`/트러스트 템플릿 기본값 위에 덮어씌움. 이미 생성된 `.dc.html`엔 소급 적용 안 됨 |
| `order_fulfillment.py` | "주문판 sync_engine" - `Order_Fulfillment` NocoDB 테이블 접근(`order_table`, `NOCODB_ORDER_TABLE_ID` 없으면 `None`), 날짜창 조회 헬퍼(`day_window`/`date_range_windows`/`merge_orders_by_id`, `orders.py`/`purchase_orders.py` 공유 - `date_range_windows(from_date, to_date)`는 임의 기간을 하루 단위로 쪼개 네이버 API 24시간 제한을 우회), 상품명↔NocoDB SKU 매칭(`match_sku_for_order`), `derive_fulfillment_status`(저장 안 하고 매번 계산). `find_or_create`는 이미 있는 로우라도 defaults 중 값이 있는데 로우엔 비어있는 필드는 채워넣는 backfill을 지원(값이 있는 필드는 절대 덮어쓰지 않음) - `/orders`가 먼저 수령인정보만으로 부분 로우를 만들어두고 `/purchase`가 나중에 나머지 필드로 완성하는 순서를 지원하기 위함 |
| `add_order_fulfillment_ace_fields.py` | `Order_Fulfillment`에 `intl_delivery_company`/`ace_customs_started_at`/`ace_domestic_started_at`/`ace_delivered_at`/`ace_last_checked_at` 컬럼을 추가한 1회성 스크립트(멱등) - `create_order_fulfillment_table.py`의 컬럼 정의에도 반영해뒀으니 이 스크립트는 이미 만들어진 기존 테이블에 소급 적용할 때만 필요 |
| `add_order_fulfillment_status_fields.py` | `Order_Fulfillment`에 `naver_order_status`/`ace_intl_shipped_at` 컬럼을 추가한 1회성 스크립트(멱등, 위와 동일 패턴) - `/orders`가 페이지 열람/새로고침 시 라이브 조회 없이 DB만으로 배송단계를 판정하도록 전환하며 필요해짐 |
| `iecot_config.py` | 배송대행지(에코트랜스) 신청서 고정값 - `IECOT_ITEM_CODE_DEFAULT="91"`, `IECOT_BRANCH_CODE="DE"`, `IECOT_SALES_AGENT_NAME="TBD Seoul"` 등 사람이 확정한 값 |
| `iecot_export.py` | `Order_Fulfillment` 레코드로 에코트랜스 업로드용 37컬럼 xlsx를 openpyxl로 생성(`build_iecot_xlsx`). 원본 샘플은 레거시 OLE2 `.xls`라 열 순 없지만 컬럼 구조만 참고해 새 `.xlsx`를 처음부터 생성. "상품명(영문)" 컬럼은 통관 절차상 영문만 허용되므로 `naver_product_name`(네이버 등록명 - 한글/키워드 섞여있음) 대신 NocoDB `SKU`(항상 영문)를 우선 쓰고, 없으면 `naver_product_name`의 " / " 앞부분만 잘라 씀(`_english_product_name`) |
| `create_order_fulfillment_table.py` | NocoDB `Order_Fulfillment` 테이블(주문→발주→현지배송→배송대행지→국제배송→네이버발송 상태 추적) 생성 1회성 스크립트, `create_price_history_table.py`와 동일 패턴 |
| `rename_fields_to_english.py` | NocoDB 필드명을 한글에서 영문으로 변경하는 스크립트 |
| `FIELD_MIGRATION.md` | NocoDB 필드명 한글→영문 마이그레이션 문서 |
| `create_price_history_table.py` | NocoDB `Price_History` 테이블(가격/재고 변동 이력, EAV 스타일) 생성 1회성 스크립트 |
| `category_lookup.py`/`notice_lookup.py`/`origin_lookup.py`/`address_lookup.py` | 네이버 API 조회용 1회성 스크립트 |
| `product_pages/scripts/` | 상세페이지 생성기 - 재사용 가능한 공용 도구: `build_pages.py`(신규 생성 패턴 - `HEAD`/`TRUST_TO_FOOTER`/`hero()`/`why_section()`이 `UNIFI_BRAND`/`GLINET_BRAND` 브랜드 딕셔너리를 파라미터로 받도록 확장됨, 인자 없이 부르면 기존 UniFi 출력과 byte-identical), `build_detail_page.py`(브랜드 무관 "콘텐츠 브리프" dict → `.dc.html` 조립 → PNG export 엔진, 대시보드 `/detail-page-builder`가 호출), `crop_hero.py`(히어로 이미지 반사 크롭 - Ubiquiti CDN 이미지 전용 로직이라 GL.iNet처럼 반사 없는 스튜디오 컷에 쓰면 오작동/과잉크롭함, 주의), `export_sections.py`(섹션별 PNG export, Playwright 필요). 카테고리별 1회성 배치 스크립트는 `archive/product_pages_scripts/`로 이동함 |
| `archive/` | 이미 끝난 1회성 조사/디버그/검증/수정 스크립트 + 더 이상 안 쓰는 데이터/로그 보관 (삭제 아님, 필요하면 재사용 가능 - `archive/README.md` 참고) |
| `naver_상품등록_템플릿.xlsx` | 등록용 엑셀 (130행: Switching 29 + WiFi 18 + Physical Security 15 + Door Access 31 + Integrations 8 + 기타 29) |
| `registered_log.json` | 등록된 상품들의 전체 API payload 로컬 로그 |
| `product_slug_map.json` | `sync_engine.py`가 UI Store 상품 URL을 만들 때 쓰는 name↔slug 매핑 (크롤링 프로젝트 때 생성). **NAS 배포 시 반드시 같이 올려야 함** - 없어도 에러 없이 조용히 링크가 안 만들어져서 놓치기 쉬움 |
| `.env`/`.env.example` | 시크릿 (NocoDB/Scrape.do/Telegram/NAVER_CLIENT_ID·SECRET/CHEAPSUB_API_KEY/NOCODB_ORDER_TABLE_ID) |
| `.claude/launch.json` | `tbd-dashboard-nicegui`(NiceGUI :8080) |

### 접근 권한 필요한 외부 폴더 (git 저장소 밖, Google Drive 동기화)
- `.../TBD Seoul/Product Images/<Brand> <Model Number>/` — 원본 제품 사진. 폴더명 규칙은 **"{Brand} {Model Number}"**(예: `UniFi UCG-Ultra`, `GLiNET GL-BE3600`) — SKU(크롤링된 긴 상품명)는 폴더명으로 쓰지 않음. Brand 표기는 `dashboard/pages/register.py`의 `_BRAND_FOLDER_NAMES`에 있음 (`GL.inet` → 점 생략 + 대문자 NET인 `GLiNET`, 일반적인 규칙으로 유추 불가하니 새 브랜드 추가 시 여기서 실제 표기를 확인할 것). 2026-08-01에 기존 폴더 전체(189개)를 이 규칙으로 일괄 정리함 — NocoDB에 없는 상품(Model Number 모름)은 옛 이름 그대로 남아있을 수 있음
- `.../TBD Seoul/Product Pages_html/` — 상세페이지 `.dc.html` 소스 + `assets/`(폰트/로고) + `exports/<slug>/`(번호 매겨진 PNG, main.py가 실제 업로드하는 이미지)
- NAS: `/volume1/docker/nicegui/` (Synology DS925+, `192.168.50.245`, SSH 계정 `jay`) — NiceGUI 대시보드 운영 환경
- NAS: `/volume1/docker/nicegui/dev/smartstore/` — Synology **CloudSync**(`syno-cloud-syncd`, Synology Drive 아님 - 실제 프로세스명으로 확인함)로 위 Google Drive "TBD Seoul" 폴더와 같은 내용을 동기화해둔 사본(2026-08-01 신설). `docker-compose.yml`이 리포 루트 전체(`.:/app`)를 이미 마운트하고 있어서 별도 볼륨 설정 없이 컨테이너 안에서 `/app/dev/smartstore`로 그대로 보임 — `naver_config.py`의 `TBD_SEOUL_ROOT` 오버라이드가 이 경로를 가리킴. 컨테이너가 만든 파일은 root 소유라 NAS에서 지우려면 `sudo rm` 필요. **이 사본은 편도 동기화가 아니라 양방향으로 갈라질 수 있음(2026-08-03 실측 확인)**: (1) `/detail-page-builder`가 NAS에서 실행되면 `write_page()`가 이 NAS 로컬 경로에 바로 파일을 쓰는데, 이게 Google Drive 쪽으로 역으로 올라간다는 보장이 없음(CloudSync가 양방향인지 편도인지 미확인) - 실제로 사용자가 NAS에서 만든 테스트 페이지 3개(`GLiNET Supply - GL-BE3600.dc.html` 등)가 로컬 Mac의 Google Drive 폴더엔 전혀 없음. (2) 반대로 로컬 Mac에서 Google Drive 폴더를 직접 수정해도 NAS 쪽에 반영되기까지 지연이 있고, **`assets/common/`처럼 CloudSync가 아예 안 건드리는 것처럼 보이는 하위 폴더도 있었음**(로고 교체 작업 때 2시간 넘게 NAS에 전혀 반영 안 됨 - 원인 미확인, 결국 `scp`로 직접 덮어써서 해결). **PNG export 자체는 2026-08-03부터 NAS에서도 됨**(Playwright 추가, 아래 "Dockerfile의 pip install 목록" 항목 참고) - 다만 NAS에서 만든 `.dc.html`이 로컬 Google Drive 쪽엔 안 보일 수 있다는 위 divergence 문제는 export와 별개로 여전히 남아있으니, 특정 상품 파일이 안 보이면 어느 쪽(로컬/NAS)에서 만들었는지부터 확인할 것. Product Pages_html 관련 파일을 급하게 NAS에 반영해야 하면 CloudSync를 기다리지 말고 `scp`로 직접 올리는 게 확실함(로고 교체 때 실제로 쓴 방법).

## 3. 현재 상태

알려진 미해결 버그: 클레임 조회 API 엔드포인트가 404(정확한 경로 미확인, `/orders`에선 이미 UI에서 뺌 - 아래 항목 참고). 그 외 진행 중인 작업 없음. 아래는 "지금 상태"만 요약한 것 — 각 항목이 왜/어떻게 그렇게 됐는지의 상세 경위는 `HISTORY.md` 참고(괄호 안 숫자가 해당 항목 번호, 전체 범위는 42~81).

- **대시보드 UI 통일**: 통계 카드/버튼/로그/섹션 헤더 스타일을 전 페이지 공통으로 통일(`dashboard/components.py`의 `primary_button`/`safe_button`/`live_write_button`/`utility_button`/`section_header`/`confirm_dialog`). 시맨틱 버튼 색은 Quasar 기본 스타일과의 CSS 우선순위 싸움 때문에 CSS 클래스가 아니라 Tailwind `!bg-[...]` 임의값 클래스로 구현됨(이 프로젝트에서 유일하게 검증된 override 방법 - 새 버튼 스타일 추가 시 이 패턴을 따를 것). (78)
- **`/settings`**: 브랜드 로고/문구, 구매·배송 안내 문구(초기불량 보장 기간/배송 소요일)를 코드 수정 없이 바꾸는 페이지 - `common_settings.py`/`common_settings.json`, `build_pages.py`가 병합해서 사용. 이미 만든 `.dc.html`엔 소급 적용 안 됨. (79)
- **`/smartstore`**: 등록 파이프라인(상품 등록/전체 파이프라인 - "배송 설정 수정" 버튼은 문서 지침대로 삭제, 스크립트는 `archive/scripts/fix_delivery_settings.py`로 이동) + 네이버 상태 동기화 + 가격/재고 업데이트(전체 상품 대상, dry-run 기본값/limit/확인 다이얼로그 있음) + "등록대기"(상세페이지는 있지만 미등록인 상품) 카드+리스트가 이 페이지에 모여있고 각 버튼에 역할 설명 라벨이 붙어있음. (71, 72, 75, 76, 79)
- **주문관리 발주/배송 (`/purchase`, `/shipping`)**: 새 NocoDB 테이블 `Order_Fulfillment`(`NOCODB_ORDER_TABLE_ID`)로 주문→발주→현지배송→배송대행지(에코트랜스 xlsx, `iecot_export.py`/`iecot_config.py`)→국제배송→네이버발송까지 추적. `naver_order_api.dispatch_product_order()`를 처음으로 실제 연결(미리보기 토글+확인 다이얼로그 필수). 실제 주문 1건으로 전 단계 검증 완료. **카카오 알림톡은 API 키/템플릿 승인 대기로 이번 범위에서 제외** - Phase D의 나머지 절반. (80)
  - `/purchase`: 발주 항목 리스트 표(주문번호/성명이 맨 왼쪽, 공홈/Amazon/Adorama/B&H 가격 비교, 클릭 시 새 탭으로 상품 페이지 이동, 발주완료 항목도 계속 표시)가 전체 너비로 렌더링됨. (81)
  - `/shipping`: 택배사 선택은 "국제배송 송장 등록" 단계에서 하고(`intl_delivery_company`에 저장, 공식 코드표 기반 `naver_delivery_companies.py` 사용, 기본값 ACE), "스마트스토어 등록(발송 처리)" 단계에선 그 값을 자동 재사용 - 재선택 불필요. (81)
- **대시보드 로그인**: `dashboard/auth.py`의 `AuthMiddleware`가 `app.storage.user` 세션 기준으로 미인증 요청을 `/login`으로 리다이렉트. `DASHBOARD_PASSWORD`/`DASHBOARD_STORAGE_SECRET` 둘 다 환경변수 필수(로컬/NAS `.env` 각각 설정, 없으면 대시보드 기동 자체가 실패). 로그아웃은 사이드바 LINKS 하단 링크(`/logout`). (62)
- **자동 테스트**: `tests/`에 pytest 단위 테스트 28개(핵심 순수 함수 mock 기반 회귀 테스트) — `python3 -m pytest tests/`(`requirements-dev.txt` 필요). (67)
- **Price_History**: `NOCODB_HISTORY_TABLE_ID=mi258r3q4g5wu69`로 로컬/NAS 연결 완료, `/inventory`에서 운영 중. 이력이 막 쌓이기 시작한 단계라 "15일 이상 품절" 섹션은 아직 비어있음(정상, Sync가 쌓일수록 채워짐).
- **자동 동기화 스케줄러**: NAS에서 가동 중(매일 09:00 KST 전체 + 4시간마다 확인 필요만). 트리거는 `sync_engine.start_background_scheduler()`의 `CronTrigger`/`IntervalTrigger`.
- **Sync 겹침 방지**: `sync_engine.run_sync_guarded()`가 수동 버튼/스케줄러 공통 진입점(`_sync_lock`/`_sync_status`/`_sync_cancel_event`), 취소 직후 재시작 시 구세대 워커가 덮어쓰지 않도록 세대(generation) 번호로도 보호됨. 대시보드에 진행중 스피너+"⏹️ 중지" 버튼, Sync 중엔 모든 버튼 비활성화. (55, 64)
- **구매대행 서비스 확장 로드맵**: Phase A(상품등록 공홈 크롤링)/B(상품관리)/C(주문관리)/D(발주·배송, 카카오 메시지 제외) 전부 완료 + **my.tbd.kr 배포/검증까지 끝남**(NAS `.env`에 `NOCODB_ORDER_TABLE_ID` 추가, Dockerfile에 `openpyxl` 추가 후 `docker-compose up -d --build` 완료 — `/purchase`/`/shipping`/`/settings` 전부 my.tbd.kr에서 실제 주문 데이터로 확인함). 남은 건 카카오 알림톡(API 키/템플릿 승인 대기)뿐 — 계획은 4번 참고. (58-59, 60, 71-72, 74, 80)
- **화이트/블랙 색상 옵션**: 35개 Black 클론 로우 운영 중(`Product_Page="Clone"` 태깅, `create_color_variant_rows.py`가 생성). 27/35 B&H 코드 입력 완료, 색상 옵션이 필요한 15개 중 14개 네이버 반영 완료(`UniFi Reader Pro`만 화이트/블랙 둘 다 품절이라 보류). **`Product_Page == "Clone"` 로우는 독립된 상세페이지/등록이 필요 없는 "다른 로우의 색상 옵션"** — 대시보드 카운트나 상세페이지 생성 대상을 다룰 때 항상 감안할 것.
- **대시보드 카운트**: `sync_engine.exclude_clone_rows()`로 Clone 로우를 제외한 실제 등록 상품(100개) 기준으로 집계(`home.py`/`category.py`/`needs_check.py`). `/inventory`처럼 색상별 추적이 목적인 곳만 원본 그대로 사용.
- **ASIN 커버리지**: 84개 보유(화이트 73 + 블랙 11). 검토 원본은 `archive/data/asin_candidates.csv`.
- **UniFi Store 링크**: `product_slug_map.json` 매칭으로 160/160 전부 연결(로컬/NAS 양쪽). 이 파일은 NAS 배포 시 누락되기 쉬우니 코드 배포할 때 항상 같이 올릴 것.
- **GL.iNet 브랜드**: `/brand/unifi`, `/brand/glinet` 라우트(`dashboard/pages/brand.py`), 검색/정렬/카테고리 필터 지원, Brand 필드 기준 필터링(미설정 시 Category 폴백). GL.iNet 크롤링 시 SKU에 "GLiNet " 접두사 자동 추가(`register.py`의 `_BRAND_SKU_PREFIXES`). **GL.iNet 신규 상품 등록 시 NocoDB Category는 "WiFi"로 설정** — `/brand/glinet` 페이지는 Category 무관하게 Brand 필드로 필터링하므로 정상 조회됨. (71)
- **주문관리** (`/orders`): 네이버 주문을 카드 형식으로 표시(주문일시/주문번호/주문자명/전화번호/주소/개인통관고유부호 + 배송단계 그래픽 트래커) + 통합검색 + 15건 초과 시 페이지네이션. 상단에 7단계(주문/발주/현지배송/국제배송/통관/국내배송/완료) 카운트 카드. 조회기간은 프리셋 없이 시작일/종료일 자유 지정(기본 최근 30일). **클레임 조회(`/product-order-claims`)는 아직도 404** - 정확한 엔드포인트 경로 미확인(공식 문서 사이트 `apicenter.commerce.naver.com` 접근 불가), UI에서도 뺐음(관리 안 함), 실제로 필요해지면 그때 재조사.
  - **읽기/쓰기 완전 분리(2026-08-03, 사용자 확정)**: "페이지를 열거나 새로고침을 누르면 네이버·ACE 같은 외부 API를 호출하는 건 말이 안 되는 구조"라는 지적에 따라 아키텍처를 재설계함. 페이지 최초 진입과 "🔄 새로고침" 버튼은 `orders.py`의 `load_from_db()`만 호출해 **`Order_Fulfillment`(NocoDB)에 저장된 값만 읽는다** - 네이버·ACE Express 호출이 전혀 없어 사실상 즉시 렌더링됨. 실제 네이버 주문 목록 조회 + 수령인정보 + ACE Express 배송조회를 수행하고 그 결과를 `Order_Fulfillment`에 반영하는 건 별도 "☁️ 네이버·배송 동기화" 버튼(`sync_orders()`)만의 역할 - 이 버튼을 눌러야 새 주문이 나타나거나 배송 단계가 갱신된다(날짜창 동시조회 3개 제한 + 개별 호출 백오프 재시도는 이 함수 안으로 그대로 이전됨, 이전 세션의 "로딩 성능 개선" 작업 2건이 이 함수의 토대). 이 전환을 위해 `Order_Fulfillment`에 필드 2개를 추가함(`add_order_fulfillment_status_fields.py`, 멱등): `naver_order_status`(네이버 주문상태 - "완료" 단계 판정용, 동기화 때마다 최신값으로 덮어씀) / `ace_intl_shipped_at`(ACE 이벤트가 처음 확인된 시각 - "국제배송" 단계 판정용, 예전엔 매 새로고침마다 라이브로 판정하던 것을 동기화 시점에 저장해두는 방식으로 전환). `_compute_stage_index()`는 이제 라이브 파라미터 없이 저장된 필드만으로 단계를 계산. `sync_orders()`는 로우가 아직 없는 신규주문도 부가정보 조회 성공 여부와 무관하게 항상 최소 필드(`naver_product_name`/`orderer_name`/`naver_order_date`/`quantity`/`naver_order_status`)로 로우를 만든다 - 안 그러면 DB만 읽는 화면에서 그 주문 자체가 안 보이게 됨. **부작용 하나 발견/수정**: `naver_order_date`를 NocoDB DateTime 필드에 저장하면 네이버가 준 KST 오프셋 문자열이 UTC로 정규화되어(9시간 밀림) 돌아옴 - `_parse_order_datetime()`으로 항상 `pytz`의 Asia/Seoul로 재변환해서 표시/날짜필터 둘 다 사용.
- **상세페이지 제작 도구** (`/detail-page-builder`): 카피라이팅(태그라인/Why 3카드/Design/Tech Specs)만 폼에 채우면 `.dc.html` 조립·PNG export는 코드가 처리. 엔진은 `product_pages/scripts/build_detail_page.py`(브랜드 무관, "콘텐츠 브리프" dict 하나로 동작). 저장된 브리프는 `Product Pages_html/briefs/<slug>.json`에 남아 "저장된 브리프 불러오기"로 재사용 가능. NocoDB SKU 검색으로 브랜드/상품명/이미지폴더명 자동채움 - **검색 결과를 고르거나 저장된 브리프를 불러오면 이미지 갤러리도 자동으로 로드됨(2026-08-03)**, 예전엔 "이미지 불러오기" 버튼을 한 번 더 눌러야 했음. "🤖 브리프 초안 생성" 버튼으로 Claude(`brief_generator.py`, CheapSub 중계 API 경유)가 공홈 URL만으로 초안을 만들어 폼을 자동으로 채워줌(생성 결과는 항상 초안 - 저장/업로드 전 사람이 검토·수정). GL.iNet 최초 상세페이지: Slate 7(`GLiNET Supply - Slate 7.dc.html`). **`.dc.html` 생성 성공 시 그 상품의 NocoDB `Product_Page`를 자동으로 "Detail"로 반영함(2026-08-03)** - `title_input.value`(NocoDB 검색으로 채워졌다면 그 레코드의 "Model Number"(공백 있는 필드명 주의, `Model_Number` 아님) 또는 SKU와 정확히 같은 문자열)로 Products 레코드를 찾아 갱신(`_find_nocodb_record`), 못 찾으면 로그에 경고만 남기고 계속 진행(생성 자체는 막지 않음). **PNG Export도 2026-08-03부터 my.tbd.kr에서 동작**(NAS Dockerfile에 `playwright` + `RUN playwright install --with-deps chromium` 추가, 아래 "Dockerfile의 pip install 목록" 항목 참고) - `export_sections.py`의 `chromium.launch()`에 `--no-sandbox`를 추가해야 했음(컨테이너가 root로 실행되는데 Chromium 자체 샌드박스가 root 권한 컨테이너에서 커널 네임스페이스 제약으로 기본 크래시하는 문제, 로컬에서도 문제 없이 동작하는 표준적 완화책이라 환경 분기 없이 항상 켜둠). 실제로 NAS 컨테이너 안에서 `export_sections.py`를 돌려 새 로고가 반영된 PNG까지 확인 완료. (68-69, 71)
- **상세페이지 헤더/푸터 로고 교체(2026-08-03)**: Google Drive `TBD Seoul/Assets/`의 신규 로고(`unifi_tbd.svg`/`glinet_tbd.svg`/`tbd_logo_gray.svg`)를 `Product Pages_html/assets/common/`에 `common_logo-unifi-tbd.svg`/`common_logo-glinet-tbd.svg`/`common_logo-footer.svg`(덮어씀)로 반영. 헤더는 기존 "브랜드 로고 + 구분선 + 작은 TBD 로고" 2단 구성을 브랜드별 콜라보 단일 로고 1개로 교체(`build_pages.py`의 `UNIFI_BRAND`/`GLINET_BRAND`의 `header_logo_src` + `head()` 템플릿, `common_settings.py`의 `DEFAULTS`도 동일하게 동기화 - 안 그러면 `/settings`에 저장된 값이 없을 때 이 파일의 구버전 기본값이 다시 덮어씀). **공용 asset 파일(footer/hero처럼 상대경로로 참조되는 이미지)은 파일 내용만 바꾸면 이미 생성된 `.dc.html`에도 소급 적용됨**(텍스트 문구와 달리 이미지는 각 파일에 내용이 박히는 게 아니라 참조만 하기 때문) - 다만 헤더는 마크업 구조 자체(2단→1단)가 바뀌어서 기존 103개 `.dc.html`을 별도 배치 스크립트로 일괄 치환함(신규 생성 페이지는 `build_pages.py` 수정만으로 자동 반영). (82)

**현재 수치**:
- 네이버 스마트스토어 등록 상품: **100개**
  - Switching: 29개
  - WiFi: 18개
  - Physical Security: 15개
  - Door Access: 31개
  - Integrations: 6개
  - 기타: 1개
- 상세페이지(HTML) 보유: **102개** (Naver 등록 100개 + 미등록 2개: Display Cast Lite, Mobile Router Industrial)
- NocoDB `Product_Page` 설정: **100개** (Detail 79개 + Simple 21개, 등록 상품 전체 커버) + **Clone 35개** (색상 옵션 클론 로우, 별도 상세페이지 불필요)
- NocoDB `Naver_Product_No` 연동: **100개**
- **NocoDB 필드명 (영문)**: `sale_price` (판매가), `purchase_cost` (구매 원가), `profit` (수익)
- 검색 키워드 추가: **58개 완료, 38개 대기** (IP 재등록 후 재실행 필요)
- 카테고리 최적화: **6개 완료** (NAS, 모바일 라우터 제품군)
- **Git/GitHub**: 로컬 git 커밋만 사용, GitHub 푸시 안 함 (private 레포 전환)
- **대시보드**: Streamlit 제거, NiceGUI만 사용 (`https://my.tbd.kr`)

## 4. 다음 작업 계획 (우선순위 순은 아니며, 이전에 합의된 로드맵)

1. **검색 키워드 일괄 추가 완료**: 네이버 커머스API 센터에서 현재 IP 재등록 후 `update_product_names_with_keywords.py` 재실행 — 실패한 38개 상품 키워드 추가
2. **구매대행 서비스 확장 로드맵** (상품등록→상품관리→주문관리→발주배송관리 4단계, Phase A/B/C/D(발주·배송) 완료 + my.tbd.kr 배포/검증까지 끝남 — 3번 현재 상태 참고):
   - **카카오 알림톡 연동(Phase D 나머지, 로드맵상 유일하게 남은 항목)**: 비즈니스 채널·발신프로필·템플릿 사전승인 필요 — 승인 대기시간이 기니 착수 전 미리 신청 권장. 승인 나면 `order_fulfillment.py`의 상태 전환 지점(발주완료/현지배송시작/배송대행지신청/국제배송/발송완료)에 알림 발송 훅을 추가하면 됨
   - **개인통관고유부호 자동 수집 (나중에)**: 네이버 스마트스토어센터의 "해외" 상품 항목이 아직 활성화 안 돼 있어 주문 API에 개인통관고유부호가 아예 없음(확인됨) - 현재는 배송대행지 신청서(에코트랜스 xlsx)에서 이 항목만 수동 입력. "해외" 항목 활성화되면 `naver_order_api.get_recipient_info()`에 파싱 추가 필요
   - **브랜드 확장**: UniFi+GL.inet 다음 브랜드(헤드폰 등)는 `official_scrapers`에 어댑터 추가로 온보딩 (Shopify 기반이면 `shopify.py` 그대로 재사용 가능). Phase B가 Brand 필드 분기까지 갖춰뒀으니 새 브랜드는 NocoDB에 Brand/Official_URL만 채우면 자동 추적됨
3. **대시보드 디자인 디테일 폴리싱**: 호버 상태, 아바타칩 실사용 등 (위 구매대행 로드맵과 무관한 별도 작업, 예전 "대시보드 Phase 3")
4. NocoDB에 다른 카테고리(Gateway, Routing 등)에도 미등록(`Naver_Product_No` 없음) 상품이 더 있는지 확인 — 사용자가 원하면 계속 등록 확장
5. **가격/재고 이력 기능 관찰**: NAS 배포는 완료됐으니, 앞으로 몇 차례 Sync를 돌려서 `Price_History`에 실제 이력이 잘 쌓이는지, `/inventory`의 "15일 이상 품절" 섹션이 시간이 지나며 의도대로 채워지는지 확인
6. **자동 동기화 스케줄러 관찰**: 다음날 09:00 KST 전체 동기화가 실제로 발동하는지, 4시간마다 확인 필요 상품 재조회가 정상 도는지 `docker-compose logs`/Telegram 알림으로 며칠 지켜보기. 문제 있으면 `sync_engine.start_background_scheduler()`의 트리거 설정 확인
7. **화이트/블랙 색상 옵션 커버리지 확대**: 남은 8개 Black 로우(B&H 코드 없음)와 나머지 ADORAMA_ID/ASIN을 마저 채워넣기. `UniFi Reader Pro`는 재고가 생기면 다음 Sync에서 옵션이 자동으로 만들어지는지 며칠 후 확인. `UniFi Access Button Black`(1855250-REG)은 B&H 제목에 "(Black)" 표기가 없어 실제 색상이 맞는지 직접 확인 권장. `UniFi Reader`/`UniFi G3 Reader Fingerprint`/`UniFi Retrofit Reader Fingerprint`는 화이트 자체를 나중에 등록하게 되면 그때 Black 로우도 같이 생성

## 5. 특이사항

### 신규 상품 등록 파이프라인 (자동화 적용)

**엑셀 템플릿 (`naver_상품등록_템플릿.xlsx`)**:
- **필수 컬럼**: 영문상품명, 한글상품명, 판매가, 제품이미지_폴더명, 상세페이지_폴더명, 재고수량, 배송비타입
- **선택 컬럼**: Category, leafCategoryId, 카테고리(대분류>중분류)
  - Category 또는 leafCategoryId를 비워두면 영문상품명 기반으로 **자동 추론 및 선택**
  - 카테고리별 최적 leafCategoryId 자동 매핑:
    - WiFi → 50001623 (네트워크장비>AP)
    - Switching → 50001506 (네트워크장비>스위칭허브)
    - Physical Security → 50002707 (TV/영상가전>CCTV)
    - Door Access → 50001623 (네트워크장비>AP, KC 인증 문제로 디지털도어록 불가)
    - Integrations (NAS) → 50001602 (저장장치>NAS)
    - Integrations (Router) → 50001622 (네트워크장비>라우터)
    - Cloud Gateways → 50003150 (네트워크장비>유무선공유기)
    - GLiNet → 50001622 (네트워크장비>라우터)

**검색 키워드 자동 생성** (`product_keywords.py`):
- 상품명 형식: `영문명 / 한글명 키워드1 키워드2...` (최대 10개)
- 카테고리별 키워드 전략:
  - **WiFi**: 와이파이, 무선AP, 메시 네트워크, 와이파이 끊김 해결 + 기술 키워드(WiFi6/7, 메시, PoE, 매립형 등)
  - **Switching**: 스위치, 스위칭허브, PoE 급전, 네트워크 확장 + 기술 키워드(10기가, 2.5기가, 플렉스 등)
  - **Physical Security**: CCTV, IP카메라, 실시간 모니터링, 야간촬영 + 기술 키워드(AI, PTZ, 4K, 센서 등)
  - **Door Access**: 출입통제, 스마트도어, 사무실 출입, 무인 출입 + 기술 키워드(리더기, 인터콤, 도어락 등)
  - **Integrations**: 네트워크장비, IoT 네트워크 구축, 원격 관리 + 기술 키워드(NAS, 라우터, 5G, 모바일 등)
  - **Cloud Gateways**: 게이트웨이, 안정적인 공유기, 통합 네트워크 관리 + 기술 키워드(클라우드, 원격관리 등)

**등록 명령어**:
```bash
python3 main.py --file naver_상품등록_템플릿.xlsx --dry-run  # 미리보기
python3 main.py --file naver_상품등록_템플릿.xlsx            # 실제 등록
```

### 기등록 상품 관리 스크립트

**카테고리 일괄 변경** (`update_categories.py`):
```bash
python3 update_categories.py --dry-run              # 미리보기
python3 update_categories.py --limit 1              # 1개만 테스트
python3 update_categories.py --category WiFi        # WiFi만 변경
python3 update_categories.py                        # 전체 실행
```

**검색 키워드 일괄 추가** (`update_product_names_with_keywords.py`):
```bash
python3 update_product_names_with_keywords.py --dry-run              # 미리보기
python3 update_product_names_with_keywords.py --limit 1              # 1개만 테스트
python3 update_product_names_with_keywords.py --category WiFi        # WiFi만 추가
python3 update_product_names_with_keywords.py                        # 전체 실행
```

### 일반 특이사항

- **커밋 컨벤션**: 논리적으로 분리된 원자적 커밋, 본문은 "왜"를 설명(한국어), 끝에 `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`. **로컬 git 커밋만 사용, GitHub 푸시 안 함 (private 레포)**
- **라이브 데이터 수정 스크립트 안전 패턴**: 전부 `--dry-run`(미리보기) + `--limit N`(N개만 테스트) 지원. 항상 1개 테스트 → 검증 → 전체 실행 순서를 따름
- **네이버 API PUT 패턴**: GET으로 전체 객체 조회 → 필요한 필드만 교체 → 전체를 그대로 PUT (건드리지 않은 필드도 다 넣어야 함, 안 그러면 날아감)
- **네이버 API 자주 겪는 이슈**:
  - IP 허용 목록 — 네트워크 바뀌면(5G ↔ 집 와이파이) `GW.IP_NOT_ALLOWED` 403 발생, 커머스API센터에서 재등록 필요
  - `statusType: OUTOFSTOCK`은 GET엔 나오지만 PUT엔 거부됨 → `SALE`로 정규화 후 전송
  - `visitAddressId`는 0이 아니라 **필드 자체를 빼야** 방문수령 불가로 처리됨
  - 신규 등록 시 `stockQuantity=0`은 거부됨 (기존 상품 PUT 수정은 0 허용) → 1로 등록 후 실제값으로 보정
  - `customerBenefit.immediateDiscountPolicy.discountMethod.value`는 0보다 커야 함 (0일 때는 필드 자체를 빼야 함)
  - 무료배송(`deliveryFeeType: FREE`)일 때는 `deliveryFeePayType` 필드를 넣으면 안 됨, 유료배송(`PAID`)일 때만 필수
  - 카테고리 ID 유효성: 일부 카테고리(네트워크장비 50000098, 주변기기 50000094)는 리프 카테고리처럼 보이지만 실제로는 등록 불가. 하위 카테고리(AP 50001623, CCTV 50002707)를 사용해야 함
  - **429 Too Many Requests**: `get_product_orders()`를 연속 호출(예: `/orders`의 자유 날짜범위가 하루씩 쪼개 순차 호출)하면 간헐적으로 재현됨 - 지수 백오프 재시도로 대부분 해결되지만, 아주 넓은 범위를 조회할 땐 여전히 드물게 일부 날짜가 실패할 수 있음(레이트리밋은 초 단위로 금방 풀리니 새로고침 재시도로 해결됨)
- **Synology NAS**: `scp`/`rsync` 기본 SFTP가 안 먹혀서 `-O`(legacy SCP) 플래그 필수. 홈디렉토리/`.ssh` 권한이 조금만 느슨해도(777) SSH 키 인증을 조용히 무시함 → `chmod 700` 필요
- **상세페이지 디자인 시스템**: 860px 고정폭, UI Sans 커스텀 폰트(base64 내장), 강조색 `#3371FB`, 한글 텍스트엔 `word-break:keep-all` 필수, 공용 섹션(TBD Seoul 신뢰뱃지/통관안내/배송반품/FAQ/Footer)은 의도적 문구 수정이 아니면 그대로 유지
- **NiceGUI 대시보드 디자인 시스템**: 페이지 배경(연한 회색) ≠ 카드 배경(흰색)이 핵심 원칙. 버튼 색은 반드시 Tailwind `!bg-[...]` 강제 클래스 사용(일반 커스텀 클래스는 NiceGUI 기본 `color=primary`와의 명시도 싸움에서 짐). 활성 메뉴는 흰색/surface 배경(검정 아님, 명시적 요청으로 변경됨). **같은 행의 카드 높이를 맞추려면** `ui.row()`에 `items-stretch` 클래스 필수 — NiceGUI의 `ui.row()`는 기본 `items-center`라 카드들이 각자 content 높이로만 렌더링되고, 카드 내부의 `h-full`도 부모 div가 flex column이어야 동작함(`ui.element('div').style('...display:flex;flex-direction:column')`). 래퍼 div 없이 `ui.column()`을 쓰는 경우엔 `items-stretch`만 추가하면 됨.
- **사이드바 구조**: PRODUCTS(신규등록/상품리스트/가격업데이트/품절변동/스마트스토어) → SALES(주문) → LINKS(TBD Seoul 스마트스토어/스마트스토어센터/커머스API센터). LINKS는 외부 링크로 `target="_blank"`로 새 창 오픈, 활성 상태 없음. `dashboard/layout.py`의 `frame()` 함수에서 관리
- **Phase C(주문관리) lazy import 패턴**: `dashboard/pages/orders.py`는 module-level에서 `naver_order_api`를 import하지 않고, `load_orders()`/`load_claims()` 함수 내부에서만 import함. 이는 NAS 배포본이 네이버 커머스API 시크릿 없이도 대시보드가 기동되도록 하기 위함 — `/orders` 페이지에 실제 접근하기 전까지는 import가 발생하지 않음. `naver_order_api`는 `auth.py`를 import하고, `auth.py`는 `bcrypt`를 import하므로 Dockerfile에 `bcrypt`가 반드시 필요함 (2026-08-01 추가됨).
- **Shopify 크롤러(`official_scrapers/shopify.py`) 로케일 프리픽스 버그**: 상품 목록/검색 결과에서 복사한 URL은 `/en-us/products/...`처럼 로케일 프리픽스가 붙는데, Shopify `.json` 엔드포인트는 이 프리픽스가 붙으면 404 (정규 경로 `/products/...`에만 존재) — `/register`에서 GL.inet 이미지 크롤링이 조용히 실패하는 원인이었음. `_product_json_url`이 경로 전체를 쓰지 않고 `/products/` 이후 핸들만 뽑아 재조립하도록 수정함 (2026-08-02).
- **ACE Express 송장조회 엔드포인트**: acedp.co.kr 메인 페이지의 송장번호 검색창은 로그인 없이 누구나 조회 가능("It's free!")하고, 실제로는 `GET /welcome/Track/hno/{송장번호}`를 iframe(colorbox)으로 열어 보여주는 방식 - 사이트의 `Trackit()` JS 함수에서 확인함(HTML `onclick` 속성에 노출되어 있어 `javascript_tool`로 함수 본문을 직접 덤프해서 찾았음). 응답은 `charset=utf-8`이지만 `requests`가 자동으로 잘못 추측하는 경우가 있어 `resp.encoding = "utf-8"`을 명시로 강제해야 한글이 깨지지 않음. 송장 미확인 시 응답 바디가 그냥 `"No Data"` 문자열임.
- **테스트/빌드 명령어**:
  ```bash
  python3 -m py_compile <file>.py                     # 문법 체크
  python3 <script>.py --dry-run                       # 실행 전 항상 먼저
  python3 dashboard/app.py                             # NiceGUI 로컬 실행 (:8080)
  python3 product_pages/scripts/build_pages.py         # 새 상세페이지 생성 패턴
  python3 product_pages/scripts/export_sections.py <html> <outdir>  # 섹션별 PNG 검증용 export
  ssh tbd-nas                                          # NAS 접속
  ```

### NAS SSH 접속 및 배포

**SSH 접속 정보**:
- 주소: `jay@192.168.50.245`
- 비밀번호: `JJ2120jj!!`
- Docker Compose 경로: `/usr/local/bin/docker-compose`

**NAS 배포 업데이트 절차**:
- NAS는 비밀번호 인증만 되므로 `scp -O`도 **sshpass 없이는 Permission denied**로 실패함 — 항상 `sshpass -p 'JJ2120jj!!'`를 붙여야 함.
- `Dockerfile`/`docker-compose.yml`은 git에는 `dashboard/deploy/`에 있지만, NAS에는 `/volume1/docker/nicegui/` 루트에 그대로(중첩 없이) 올라가 있음 — `docker-compose.yml`의 `build: .`가 그 위치 기준.
- **코드만 바뀐 경우**(`sync_engine.py`, `dashboard/` 등) → `docker-compose restart`로 충분.
- **Dockerfile을 바꿔서 새 pip 패키지가 필요한 경우**(예: `apscheduler` 추가) → `restart`로는 새 패키지가 설치되지 않음, 반드시 **`docker-compose up -d --build`**로 이미지 재빌드 필요.
- **`Dockerfile`의 `pip install` 목록이 `requirements.txt`와 안 맞음**: `Dockerfile`은 `requirements.txt`를 쓰지 않고 자체 `pip install nicegui requests beautifulsoup4 yfinance python-dotenv apscheduler pytz bcrypt anthropic openpyxl playwright` 한 줄 + `RUN playwright install --with-deps chromium`으로 관리한다(2026-08-03부로 `playwright`도 추가 완료 - PNG export가 NAS에서도 동작). `requirements.txt`엔 있지만 이 목록엔 없는 `pandas`만 남은 차이 - 아직 이 패키지를 쓰는 기능이 NAS 경로에서 안 걸려서 문제 없음, 새로 NAS에서도 필요한 패키지를 쓰는 기능을 추가하면 이 pip 목록에도 반드시 같이 추가할 것. Playwright 추가로 이미지 빌드 시간이 늘어남(Chromium 다운로드 ~80초 관측) - `docker-compose up -d --build` 배포 시 감안할 것.
- **`.py`가 아닌 데이터 파일도 빠뜨리지 말 것**: `sync_engine.py`가 디스크에서 직접 읽는 파일(`product_slug_map.json` 등)은 로컬에는 있어도 NAS에 배포한 적 없으면 조용히 빈 값으로 처리됨(에러 없음 - 예: UniFi Store 링크가 로컬에선 되는데 NAS에선 전부 안 뜨는 버그로 실제 발견됨). 코드 배포할 때 이런 데이터 파일도 같이 올라갔는지 확인할 것.
- **새 모듈을 배포하기 전에 그 import 체인이 요구하는 시크릿을 먼저 확인할 것**: `dashboard/` 안에서 `import` 하는 모듈은 전부 module-level 코드가 즉시 실행되므로, 그 체인 어딘가 `_get_secret(..., required=True)`가 있고 NAS `.env`에 그 값이 없으면 그 페이지 하나가 아니라 **대시보드 전체가 기동 실패**한다(실제로 `register.py`→`image_uploader`→`naver_config`에서 겪음). NAS에서 안 쓰는 시크릿이면 값을 굳이 채워넣지 말고 `required=False`로 완화하는 쪽이 낫다.
- **NAS `.env`에 줄 추가할 때 trailing newline 확인**: `cat >> .env`로 이어붙이는데 기존 파일 끝에 개행이 없으면 마지막 줄과 새 줄이 한 줄로 붙어버려 두 값 다 깨진다(실제로 `TELEGRAM_CHAT_ID`+`TBD_SEOUL_ROOT`가 붙어버린 사고 있었음). 추가한 뒤 `cat -A .env`로 줄바꿈(`$`)이 제대로 갈라져 있는지 항상 확인할 것.
- **`docker-compose restart`가 `.env` 값에 `$`가 들어있으면 경고를 냄(무시해도 됨)**: `NAVER_CLIENT_SECRET`처럼 bcrypt 해시 형식(`$2a$04$...`)이라 리터럴 `$`가 들어있는 값을 넣으면 `docker-compose`가 자기 내부 변수치환용으로 `.env`를 다시 파싱하면서 `"$04" 변수가 설정 안 됨` 같은 경고를 띄운다. 이 프로젝트의 `docker-compose.yml`은 `environment:`/`env_file:`로 `.env`를 안 쓰고 앱이 파이썬 `python-dotenv`로 직접 읽으므로(볼륨마운트로 컨테이너 안에 `.env` 파일 자체가 그대로 보임) **실제 값은 안 깨짐** - 경고 무시하고 `docker exec ... python3 -c "import config; print(...)"`로 실제 로드된 값만 확인하면 됨.

```bash
# 파일 업로드 (sshpass 필수)
sshpass -p 'JJ2120jj!!' scp -O -o StrictHostKeyChecking=no sync_engine.py config.py nocodb_client.py naver_config.py image_uploader.py brief_generator.py product_slug_map.json jay@192.168.50.245:/volume1/docker/nicegui/
sshpass -p 'JJ2120jj!!' scp -O -o StrictHostKeyChecking=no -r dashboard official_scrapers product_pages jay@192.168.50.245:/volume1/docker/nicegui/
sshpass -p 'JJ2120jj!!' scp -O -o StrictHostKeyChecking=no retailer_search.py jay@192.168.50.245:/volume1/docker/nicegui/
# Dockerfile이 바뀌었다면 NAS 루트(중첩 아님)에 별도 업로드
sshpass -p 'JJ2120jj!!' scp -O -o StrictHostKeyChecking=no dashboard/deploy/Dockerfile jay@192.168.50.245:/volume1/docker/nicegui/

# 코드만 바뀐 경우 - 재시작
sshpass -p 'JJ2120jj!!' ssh -o StrictHostKeyChecking=no jay@192.168.50.245 \
  "cd /volume1/docker/nicegui && echo 'JJ2120jj!!' | sudo -S /usr/local/bin/docker-compose restart"

# Dockerfile이 바뀐 경우 - 재빌드
sshpass -p 'JJ2120jj!!' ssh -o StrictHostKeyChecking=no jay@192.168.50.245 \
  "cd /volume1/docker/nicegui && echo 'JJ2120jj!!' | sudo -S /usr/local/bin/docker-compose up -d --build"
```

**Synology Container Manager GUI**:
1. Container Manager 앱 열기
2. `nicegui` 컨테이너 선택
3. 재시작 버튼 클릭
