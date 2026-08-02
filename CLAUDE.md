# 프로젝트 인계 문서

지난 세션들의 상세 작업 이력(시간순, 무엇을 왜 했는지)은 `HISTORY.md` 참고 —
이 문서는 "지금 상태"만 빠르게 파악하기 위한 용도입니다.

## 1. 프로젝트 개요

- **목적/종류**: "TBD Seoul" — 미국에서 Ubiquiti UniFi 네트워크 장비를 병행수입(해외직구)해서 네이버 스마트스토어에 재판매하는 1인 사업의 자동화 시스템. 가격 모니터링, 상품 등록, 상세페이지 생성, 대시보드로 구성.
- **기술 스택**: Python 3 (로컬 Mac은 3.14, NAS Docker는 3.11), NiceGUI(대시보드), NocoDB(DB, Airtable에서 이전), requests/BeautifulSoup4(스크래핑), yfinance(환율), APScheduler(자동 동기화 스케줄러), Playwright(헤드리스 크롬 - 상세페이지 HTML→PNG 렌더링), openpyxl(엑셀 템플릿), 네이버 커머스API, Docker + Synology Container Manager, Cloudflare Tunnel
- **디렉토리**: `/Users/cheil/Desktop/dev/tbd` (git 저장소, GitHub `jjh3533/tbd` — **private 레포**, 로컬 git만 사용, GitHub 푸시 안 함). 2026-07-31에 `~/tbd`에서 이 위치로 이동함. **맥 두 대에서 사용** — 다른 한 대(`jay` 계정)는 아직 `/Users/jay/tbd`에 있을 수 있음, 두 기기 경로를 맞추려면 그쪽도 동일하게 옮길 것. 코드에 홈 디렉토리를 직접 하드코딩하지 말고 `os.path.expanduser("~/...")`로 작성할 것 (`naver_config.py`의 `PRODUCT_IMAGES_DIR`/`PRODUCT_PAGES_DIR` 참고) — 두 기기 모두 같은 구글 드라이브 계정(`jjh3533@gmail.com`)을 쓰므로 이 방식이면 기기별 설정 없이 그대로 동작함

## 2. 프로젝트 구조

### 루트 핵심 파일
| 파일 | 역할 |
|---|---|
| `sync_engine.py` | 스크래핑/동기화/포맷팅 로직 - 프레임워크 독립 모듈. `start_background_scheduler()`로 매일 09:00 KST 전체 동기화 + 4시간마다 확인 필요 상품만 재조회하는 자동화도 포함 |
| `dashboard/` | NiceGUI 대시보드 (`theme.py`, `layout.py`, `components.py`, `app.py`, `pages/{home,category,brand,register,inventory,needs_check,orders}.py`, `deploy/{Dockerfile,docker-compose.yml}`) |
| `config.py` | 공용 시크릿 로더 (`.env`), NocoDB/Scrape.do/Telegram 값 |
| `naver_config.py` | 네이버 커머스API 설정 (CLIENT_ID/SECRET은 `.env`에서, NAS엔 없어도 되도록 `required=False`). `PRODUCT_IMAGES_DIR`/`PRODUCT_PAGES_DIR`는 `.env`의 `TBD_SEOUL_ROOT`로 오버라이드 가능 (맥은 미설정=Google Drive CloudStorage 경로, NAS는 `/app/dev/smartstore`로 설정) |
| `nocodb_client.py` | NocoDB REST v2용 Airtable 호환 어댑터 |
| `auth.py` | 네이버 OAuth2 bearer token 발급 (bcrypt 기반 전자서명) |
| `naver_order_api.py` | 네이버 Pay-Order/Claims API 클라이언트 (Phase C 주문관리용) |
| `main.py` | 엑셀(`naver_상품등록_템플릿.xlsx`) 기반 네이버 상품 등록 파이프라인 |
| `product_builder.py` / `image_uploader.py` | 등록 payload 생성 / 이미지 업로드. **자동 카테고리 선택 및 검색 키워드 추가 기능 내장** |
| `product_keywords.py` | 카테고리별 자동 leafCategoryId 선택 및 검색 최적화 키워드 생성 모듈 |
| `update_categories.py` | 기등록 상품의 카테고리를 더 적합한 카테고리로 일괄 변경 |
| `update_product_names_with_keywords.py` | 기등록 상품명에 검색 키워드 일괄 추가 |
| `run_pipeline.py` | main.py → sync_naver_ids_to_nocodb.py → update_price_stock.py 순차 실행 |
| `sync_naver_ids_to_nocodb.py` | `TARGET_PRODUCTS` 매핑, 네이버 채널상품번호를 NocoDB에 반영 |
| `update_price_stock.py` | NocoDB → 네이버 가격/재고 동기화 (영문 필드명 `sale_price` 사용). `{SKU} Black` 짝 로우가 있으면 화이트/블랙 옵션별로 다른 가격/재고 반영 - 옵션이 이미 있으면 갱신, 없으면 신규 생성 |
| `create_color_variant_rows.py` | 화이트 기준 로우에서 `{SKU} Black`/`{Model Number}-B` 블랙 변형 로우를 생성하는 스크립트 (Category/Weight_KG/MSRP_USD/Naver_Product_No는 화이트와 동일하게 복사, 구매처 ID는 비워둠) |
| `search_amazon_candidates.py` | ASIN 없는 상품을 상품명+모델명으로 아마존 검색해(Scrape.do Amazon Search 플러그인) 후보를 CSV로 뽑아주는 스크립트. NocoDB에 자동으로 쓰지 않고 사람이 검토하는 용도. 실제 검색 로직은 `retailer_search.py`로 이관됨 |
| `official_scrapers/` | 구매대행 신규 브랜드 공홈 크롤러 레지스트리 (`fetch_product(brand, url)`). `shopify.py`(Shopify `.json` 엔드포인트, 브랜드 무관 공용) / `unifi.py`(store.ui.com `__NEXT_DATA__` 파싱). 현재 UniFi/GL.inet만 등록됨, 새 브랜드는 `__init__.py`의 `_BRAND_SCRAPERS`에 한 줄 추가 |
| `retailer_search.py` | 상품명+모델명으로 아마존/B&H/Adorama에서 후보를 찾는 검색 모듈. B&H/Adorama는 전용 검색 플러그인이 없어 사이트 검색결과 페이지의 URL 슬러그로 매칭(카드 `<a>`에 텍스트가 없는 경우가 많아서) |
| `fix_delivery_settings.py` | 이미 등록된 상품의 배송사/배송비/원산지 일괄 수정 |
| `update_live_customs_image.py` | 라이브 상세페이지의 통관 안내 섹션 이미지만 교체 |
| `rename_fields_to_english.py` | NocoDB 필드명을 한글에서 영문으로 변경하는 스크립트 |
| `FIELD_MIGRATION.md` | NocoDB 필드명 한글→영문 마이그레이션 문서 |
| `create_price_history_table.py` | NocoDB `Price_History` 테이블(가격/재고 변동 이력, EAV 스타일) 생성 1회성 스크립트 |
| `category_lookup.py`/`notice_lookup.py`/`origin_lookup.py`/`address_lookup.py` | 네이버 API 조회용 1회성 스크립트 |
| `product_pages/scripts/` | 상세페이지 생성기 - 재사용 가능한 공용 도구만 남음: `build_pages.py`(신규 생성 패턴), `crop_hero.py`(히어로 이미지 반사 크롭), `export_sections.py`(섹션별 PNG 검증용 export). 카테고리별 1회성 배치 스크립트는 `archive/product_pages_scripts/`로 이동함 |
| `archive/` | 이미 끝난 1회성 조사/디버그/검증/수정 스크립트 + 더 이상 안 쓰는 데이터/로그 보관 (삭제 아님, 필요하면 재사용 가능 - `archive/README.md` 참고) |
| `naver_상품등록_템플릿.xlsx` | 등록용 엑셀 (130행: Switching 29 + WiFi 18 + Physical Security 15 + Door Access 31 + Integrations 8 + 기타 29) |
| `registered_log.json` | 등록된 상품들의 전체 API payload 로컬 로그 |
| `product_slug_map.json` | `sync_engine.py`가 UI Store 상품 URL을 만들 때 쓰는 name↔slug 매핑 (크롤링 프로젝트 때 생성). **NAS 배포 시 반드시 같이 올려야 함** - 없어도 에러 없이 조용히 링크가 안 만들어져서 놓치기 쉬움 |
| `.env`/`.env.example` | 시크릿 (NocoDB/Scrape.do/Telegram/NAVER_CLIENT_ID·SECRET) |
| `.claude/launch.json` | `tbd-dashboard-nicegui`(NiceGUI :8080) |

### 접근 권한 필요한 외부 폴더 (git 저장소 밖, Google Drive 동기화)
- `.../TBD Seoul/Product Images/<Brand> <Model Number>/` — 원본 제품 사진. 폴더명 규칙은 **"{Brand} {Model Number}"**(예: `UniFi UCG-Ultra`, `GLiNET GL-BE3600`) — SKU(크롤링된 긴 상품명)는 폴더명으로 쓰지 않음. Brand 표기는 `dashboard/pages/register.py`의 `_BRAND_FOLDER_NAMES`에 있음 (`GL.inet` → 점 생략 + 대문자 NET인 `GLiNET`, 일반적인 규칙으로 유추 불가하니 새 브랜드 추가 시 여기서 실제 표기를 확인할 것). 2026-08-01에 기존 폴더 전체(189개)를 이 규칙으로 일괄 정리함 — NocoDB에 없는 상품(Model Number 모름)은 옛 이름 그대로 남아있을 수 있음
- `.../TBD Seoul/Product Pages_html/` — 상세페이지 `.dc.html` 소스 + `assets/`(폰트/로고) + `exports/<slug>/`(번호 매겨진 PNG, main.py가 실제 업로드하는 이미지)
- NAS: `/volume1/docker/nicegui/` (Synology DS925+, `192.168.50.245`, SSH 계정 `jay`) — NiceGUI 대시보드 운영 환경
- NAS: `/volume1/docker/nicegui/dev/smartstore/` — Synology Drive로 위 Google Drive "TBD Seoul" 폴더와 같은 내용을 동기화해둔 사본(2026-08-01 신설). `docker-compose.yml`이 리포 루트 전체(`.:/app`)를 이미 마운트하고 있어서 별도 볼륨 설정 없이 컨테이너 안에서 `/app/dev/smartstore`로 그대로 보임 — `naver_config.py`의 `TBD_SEOUL_ROOT` 오버라이드가 이 경로를 가리킴. 컨테이너가 만든 파일은 root 소유라 NAS에서 지우려면 `sudo rm` 필요

## 3. 현재 상태

알려진 미해결 버그나 진행 중인 작업 없음. 세부 경위는 `HISTORY.md` 참고 (항목 42~59).

- **코드 리뷰 기반 수정 완료**: `CODE_REVIEW.md`(ChatGPT 검토, 2026-08-02)를 실제 코드와 대조 검증 후 우선순위를 다시 매겨 전부 대응함:
  - P0 대시보드 로그인 인증 (아래 항목 참고), P1 NocoDB 갱신 실패 전파+Price History 순서, Sync 취소 후 세대(generation) 기반 레이스 방지, 주문 "최근 7일" 하루 단위 분할 조회 — 커밋 완료.
  - P2 주문/클레임 API 시간대 정규화(`naver_order_api._to_kst`)+클레임 24시간 검증 — 커밋 완료.
  - P2 공홈 크롤링 3중 호출→1회 통합 + 공홈 실패의 Needs_Check 반영, 그리고 등록 파이프라인(`/register`) 동시실행 방지(프로세스 전역 락)+dry-run 확인창 스킵은 **구현·검증 완료했지만 별도 커밋은 못 함** — 둘 다 아직 미커밋인 Phase B(신규 브랜드 자동추적)/파이프라인 UI 코드 자체를 고치는 것이라, HEAD에 그 기반 코드가 없어 격리 커밋이 불가능함. 작업 트리에는 반영돼 있고 Phase B를 커밋할 때 함께 커밋될 예정.
  - P3 `tests/`에 pytest 단위 테스트 28개 추가(핵심 순수 함수 mock 기반 회귀 테스트) — 커밋 완료. `python3 -m pytest tests/` (requirements-dev.txt 참고).

- **대시보드 로그인 인증 추가**: Cloudflare Tunnel로 my.tbd.kr을 외부에 노출 중인데 대시보드에 인증이 전혀 없어 URL만 알면 누구나 /register(실제 네이버 API 실행)·/orders(고객 주문정보)를 포함한 모든 페이지에 접근 가능했던 문제를 수정함(CODE_REVIEW.md 검토 중 발견). `dashboard/auth.py`의 `AuthMiddleware`가 `app.storage.user` 세션 기준으로 미인증 요청을 `/login`으로 리다이렉트. 단일 관리자 비밀번호 `DASHBOARD_PASSWORD`, 세션 서명 키 `DASHBOARD_STORAGE_SECRET` 둘 다 환경변수 필수(로컬/NAS `.env` 각각 설정 필요, 값이 없으면 대시보드 기동 자체가 실패함 — required 시크릿이므로 NAS 배포 전 반드시 추가). 로그아웃은 사이드바 LINKS 하단 링크(`/logout`).
- **Price_History**: `NOCODB_HISTORY_TABLE_ID=mi258r3q4g5wu69`로 로컬/NAS 연결 완료, `/inventory`에서 운영 중. 이력이 막 쌓이기 시작한 단계라 "15일 이상 품절" 섹션은 아직 비어있음(정상, Sync가 쌓일수록 채워짐).
- **자동 동기화 스케줄러**: NAS에서 가동 중(매일 09:00 KST 전체 + 4시간마다 확인 필요만). 트리거는 `sync_engine.start_background_scheduler()`의 `CronTrigger`/`IntervalTrigger`.
- **Sync 겹침 방지**: `sync_engine.run_sync_guarded()`가 수동 버튼/스케줄러 공통 진입점(`_sync_lock`/`_sync_status`/`_sync_cancel_event`). 대시보드에 진행중 스피너+"⏹️ 중지" 버튼 있음, Sync 중엔 모든 버튼 비활성화.
- **화이트/블랙 색상 옵션**: 35개 Black 클론 로우 운영 중(`Product_Page="Clone"` 태깅, `create_color_variant_rows.py`가 생성). 27/35 B&H 코드 입력 완료, 색상 옵션이 필요한 15개 중 14개 네이버 반영 완료(`UniFi Reader Pro`만 화이트/블랙 둘 다 품절이라 보류). **`Product_Page == "Clone"` 로우는 독립된 상세페이지/등록이 필요 없는 "다른 로우의 색상 옵션"** — 대시보드 카운트나 상세페이지 생성 대상을 다룰 때 항상 감안할 것.
- **대시보드 카운트**: `sync_engine.exclude_clone_rows()`로 Clone 로우를 제외한 실제 등록 상품(100개) 기준으로 집계(`home.py`/`category.py`/`needs_check.py`). `/inventory`처럼 색상별 추적이 목적인 곳만 원본 그대로 사용.
- **ASIN 커버리지**: 84개 보유(화이트 73 + 블랙 11). 검토 원본은 `archive/data/asin_candidates.csv`.
- **UniFi Store 링크**: `product_slug_map.json` 매칭으로 160/160 전부 연결(로컬/NAS 양쪽). 이 파일은 NAS 배포 시 누락되기 쉬우니 코드 배포할 때 항상 같이 올릴 것.
- **구매대행 서비스 확장 로드맵 Phase A(상품등록 공홈 크롤링) 완료**: `/register`에서 크롤링→미리보기→리테일러 후보 검색→저장까지 my.tbd.kr에 실제 배포/검증 완료(UniFi/GL.inet). 이미지 다운로드는 `/app/dev/smartstore`(위 외부 폴더 참고)에 "{Brand} {Model Number}" 폴더명으로 저장됨(위 Product Images 폴더 규칙 참고). 기존 Product Images 폴더 전체도 이 규칙으로 정리 완료(154개 이름변경 + 19개 중복 삭제, NocoDB에 없는 33개는 보류). 전체 로드맵과 남은 단계(B/D)는 4번 참고
- **GL.iNet 브랜드 지원 추가**: `dashboard/pages/brand.py` 신규 추가. `/brand/unifi`, `/brand/glinet` 라우트로 브랜드별 상품 리스트 제공. 검색·정렬(카테고리순/이름A-Z·Z-A/가격낮은순·높은순)·카테고리 필터 포함, 필터 변경 시 테이블 즉시 갱신. Brand 필드 기준 필터링(Brand 미설정 시 Category 폴백). 사이드바 "📋 상품 리스트" 서브메뉴가 카테고리 목록 대신 UniFi/GL.iNet 브랜드 링크로 교체됨. GL.iNet 크롤링 시 SKU에 "GLiNet " 접두사 자동 추가(`register.py`의 `_BRAND_SKU_PREFIXES`). **GL.iNet 신규 상품 등록 시 NocoDB Category는 "WiFi"로 설정** — `/brand/glinet` 페이지는 Category 무관하게 Brand 필드로 필터링하므로 정상 조회됨
- **구매대행 서비스 확장 로드맵 Phase C(주문관리) 완료**: `/orders` 페이지에서 네이버 Pay-Order/Claims API로 주문 목록 및 클레임 조회 기능 구현 완료. `naver_order_api.py`(API 클라이언트) + `dashboard/pages/orders.py`(UI) 추가. **로컬 전용 기능**(NAS는 네이버 시크릿 없음) — `orders.py`가 lazy import로 `naver_order_api`를 함수 내부에서만 불러와 NAS 기동 시 에러 방지. Dockerfile에 `bcrypt` 의존성 추가 (auth.py의 전자서명용)

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
2. **구매대행 서비스 확장 로드맵** (상품등록→상품관리→주문관리→발주배송관리 4단계, Phase A/C 완료 — 3번 현재 상태 참고):
   - **Phase B(상품관리 확장)**: `official_scrapers`/`retailer_search` 크롤러를 `sync_engine`의 자동 스케줄러/needs_check 로직에 연결해 신규 브랜드 상품도 자동 추적되게 하기. 신규 브랜드 상품이 `product_keywords.py`의 카테고리 자동선택 로직을 못 타는 경우 예외 처리. 대시보드 "상품 등록" 페이지에서 `main.py`/`run_pipeline.py`/`update_price_stock.py`/`fix_delivery_settings.py`를 버튼으로 실행(dry-run/limit 안전장치 포함)하는 것도 이 단계에 포함(예전엔 "대시보드 Phase 2"로 불렀던 항목)
   - **Phase D(발주 및 배송관리)**: 포워더 에코트랜스(API 없음, xlsx 대량등록 가능) 신청서 자동생성 + 송장 조회 자동화, 카카오 알림톡 연동(비즈니스 채널·발신프로필·템플릿 사전승인 필요 — 승인 대기시간이 기니 착수 전 미리 신청 권장)
   - **브랜드 확장**: UniFi+GL.inet 다음 브랜드(헤드폰 등)는 `official_scrapers`에 어댑터 추가로 온보딩 (Shopify 기반이면 `shopify.py` 그대로 재사용 가능)
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
- **Synology NAS**: `scp`/`rsync` 기본 SFTP가 안 먹혀서 `-O`(legacy SCP) 플래그 필수. 홈디렉토리/`.ssh` 권한이 조금만 느슨해도(777) SSH 키 인증을 조용히 무시함 → `chmod 700` 필요
- **상세페이지 디자인 시스템**: 860px 고정폭, UI Sans 커스텀 폰트(base64 내장), 강조색 `#3371FB`, 한글 텍스트엔 `word-break:keep-all` 필수, 공용 섹션(TBD Seoul 신뢰뱃지/통관안내/배송반품/FAQ/Footer)은 의도적 문구 수정이 아니면 그대로 유지
- **NiceGUI 대시보드 디자인 시스템**: 페이지 배경(연한 회색) ≠ 카드 배경(흰색)이 핵심 원칙. 버튼 색은 반드시 Tailwind `!bg-[...]` 강제 클래스 사용(일반 커스텀 클래스는 NiceGUI 기본 `color=primary`와의 명시도 싸움에서 짐). 활성 메뉴는 흰색/surface 배경(검정 아님, 명시적 요청으로 변경됨). **같은 행의 카드 높이를 맞추려면** `ui.row()`에 `items-stretch` 클래스 필수 — NiceGUI의 `ui.row()`는 기본 `items-center`라 카드들이 각자 content 높이로만 렌더링되고, 카드 내부의 `h-full`도 부모 div가 flex column이어야 동작함(`ui.element('div').style('...display:flex;flex-direction:column')`). 래퍼 div 없이 `ui.column()`을 쓰는 경우엔 `items-stretch`만 추가하면 됨.
- **사이드바 구조**: PRODUCTS(신규등록/상품리스트/가격업데이트/품절변동/스마트스토어) → SALES(주문) → LINKS(TBD Seoul 스마트스토어/스마트스토어센터/커머스API센터). LINKS는 외부 링크로 `target="_blank"`로 새 창 오픈, 활성 상태 없음. `dashboard/layout.py`의 `frame()` 함수에서 관리
- **Phase C(주문관리) lazy import 패턴**: `dashboard/pages/orders.py`는 module-level에서 `naver_order_api`를 import하지 않고, `load_orders()`/`load_claims()` 함수 내부에서만 import함. 이는 NAS 배포본이 네이버 커머스API 시크릿 없이도 대시보드가 기동되도록 하기 위함 — `/orders` 페이지에 실제 접근하기 전까지는 import가 발생하지 않음. `naver_order_api`는 `auth.py`를 import하고, `auth.py`는 `bcrypt`를 import하므로 Dockerfile에 `bcrypt`가 반드시 필요함 (2026-08-01 추가됨).
- **Shopify 크롤러(`official_scrapers/shopify.py`) 로케일 프리픽스 버그**: 상품 목록/검색 결과에서 복사한 URL은 `/en-us/products/...`처럼 로케일 프리픽스가 붙는데, Shopify `.json` 엔드포인트는 이 프리픽스가 붙으면 404 (정규 경로 `/products/...`에만 존재) — `/register`에서 GL.inet 이미지 크롤링이 조용히 실패하는 원인이었음. `_product_json_url`이 경로 전체를 쓰지 않고 `/products/` 이후 핸들만 뽑아 재조립하도록 수정함 (2026-08-02).
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
- **`.py`가 아닌 데이터 파일도 빠뜨리지 말 것**: `sync_engine.py`가 디스크에서 직접 읽는 파일(`product_slug_map.json` 등)은 로컬에는 있어도 NAS에 배포한 적 없으면 조용히 빈 값으로 처리됨(에러 없음 - 예: UniFi Store 링크가 로컬에선 되는데 NAS에선 전부 안 뜨는 버그로 실제 발견됨). 코드 배포할 때 이런 데이터 파일도 같이 올라갔는지 확인할 것.
- **새 모듈을 배포하기 전에 그 import 체인이 요구하는 시크릿을 먼저 확인할 것**: `dashboard/` 안에서 `import` 하는 모듈은 전부 module-level 코드가 즉시 실행되므로, 그 체인 어딘가 `_get_secret(..., required=True)`가 있고 NAS `.env`에 그 값이 없으면 그 페이지 하나가 아니라 **대시보드 전체가 기동 실패**한다(실제로 `register.py`→`image_uploader`→`naver_config`에서 겪음). NAS에서 안 쓰는 시크릿이면 값을 굳이 채워넣지 말고 `required=False`로 완화하는 쪽이 낫다.
- **NAS `.env`에 줄 추가할 때 trailing newline 확인**: `cat >> .env`로 이어붙이는데 기존 파일 끝에 개행이 없으면 마지막 줄과 새 줄이 한 줄로 붙어버려 두 값 다 깨진다(실제로 `TELEGRAM_CHAT_ID`+`TBD_SEOUL_ROOT`가 붙어버린 사고 있었음). 추가한 뒤 `cat -A .env`로 줄바꿈(`$`)이 제대로 갈라져 있는지 항상 확인할 것.

```bash
# 파일 업로드 (sshpass 필수)
sshpass -p 'JJ2120jj!!' scp -O -o StrictHostKeyChecking=no sync_engine.py config.py nocodb_client.py naver_config.py image_uploader.py product_slug_map.json jay@192.168.50.245:/volume1/docker/nicegui/
sshpass -p 'JJ2120jj!!' scp -O -o StrictHostKeyChecking=no -r dashboard official_scrapers jay@192.168.50.245:/volume1/docker/nicegui/
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
