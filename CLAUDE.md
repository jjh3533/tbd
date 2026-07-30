# 프로젝트 인계 문서

지난 세션들의 상세 작업 이력(시간순, 무엇을 왜 했는지)은 `HISTORY.md` 참고 —
이 문서는 "지금 상태"만 빠르게 파악하기 위한 용도입니다.

## 1. 프로젝트 개요

- **목적/종류**: "TBD Seoul" — 미국에서 Ubiquiti UniFi 네트워크 장비를 병행수입(해외직구)해서 네이버 스마트스토어에 재판매하는 1인 사업의 자동화 시스템. 가격 모니터링, 상품 등록, 상세페이지 생성, 대시보드로 구성.
- **기술 스택**: Python 3 (로컬 Mac은 3.14, NAS Docker는 3.11), NiceGUI(대시보드), NocoDB(DB, Airtable에서 이전), requests/BeautifulSoup4(스크래핑), yfinance(환율), APScheduler(자동 동기화 스케줄러), Playwright(헤드리스 크롬 - 상세페이지 HTML→PNG 렌더링), openpyxl(엑셀 템플릿), 네이버 커머스API, Docker + Synology Container Manager, Cloudflare Tunnel
- **디렉토리**: `~/tbd` (git 저장소, GitHub `jjh3533/tbd` — **private 레포**, 로컬 git만 사용, GitHub 푸시 안 함). **맥 두 대에서 사용** (`/Users/cheil/tbd`, `/Users/jay/tbd` — macOS 계정명만 다름). 코드에 홈 디렉토리를 직접 하드코딩하지 말고 `os.path.expanduser("~/...")`로 작성할 것 (`naver_config.py`의 `PRODUCT_IMAGES_DIR`/`PRODUCT_PAGES_DIR` 참고) — 두 기기 모두 같은 구글 드라이브 계정(`jjh3533@gmail.com`)을 쓰므로 이 방식이면 기기별 설정 없이 그대로 동작함

## 2. 프로젝트 구조

### 루트 핵심 파일
| 파일 | 역할 |
|---|---|
| `sync_engine.py` | 스크래핑/동기화/포맷팅 로직 - 프레임워크 독립 모듈. `start_background_scheduler()`로 매일 09:00 KST 전체 동기화 + 4시간마다 확인 필요 상품만 재조회하는 자동화도 포함 |
| `dashboard/` | NiceGUI 대시보드 (`theme.py`, `layout.py`, `components.py`, `app.py`, `pages/{home,category,register,inventory}.py`, `deploy/{Dockerfile,docker-compose.yml}`) |
| `config.py` | 공용 시크릿 로더 (`.env`), NocoDB/Scrape.do/Telegram 값 |
| `naver_config.py` | 네이버 커머스API 설정 (CLIENT_ID/SECRET은 `.env`에서) |
| `nocodb_client.py` | NocoDB REST v2용 Airtable 호환 어댑터 |
| `auth.py` | 네이버 OAuth2 bearer token 발급 |
| `main.py` | 엑셀(`naver_상품등록_템플릿.xlsx`) 기반 네이버 상품 등록 파이프라인 |
| `product_builder.py` / `image_uploader.py` | 등록 payload 생성 / 이미지 업로드. **자동 카테고리 선택 및 검색 키워드 추가 기능 내장** |
| `product_keywords.py` | 카테고리별 자동 leafCategoryId 선택 및 검색 최적화 키워드 생성 모듈 |
| `update_categories.py` | 기등록 상품의 카테고리를 더 적합한 카테고리로 일괄 변경 |
| `update_product_names_with_keywords.py` | 기등록 상품명에 검색 키워드 일괄 추가 |
| `run_pipeline.py` | main.py → sync_naver_ids_to_nocodb.py → update_price_stock.py 순차 실행 |
| `sync_naver_ids_to_nocodb.py` | `TARGET_PRODUCTS` 매핑, 네이버 채널상품번호를 NocoDB에 반영 |
| `update_price_stock.py` | NocoDB → 네이버 가격/재고 동기화 (영문 필드명 `sale_price` 사용). 화이트/블랙 색상 옵션 상품은 `{SKU} Black` 짝 로우가 있으면 옵션별로 다른 가격/재고 반영 |
| `create_color_variant_rows.py` | 화이트 기준 로우에서 `{SKU} Black`/`{Model Number}-B` 블랙 변형 로우를 생성하는 스크립트 (Category/Weight_KG/MSRP_USD/Naver_Product_No는 화이트와 동일하게 복사, 구매처 ID는 비워둠) |
| `fix_delivery_settings.py` | 이미 등록된 상품의 배송사/배송비/원산지 일괄 수정 |
| `update_live_customs_image.py` | 라이브 상세페이지의 통관 안내 섹션 이미지만 교체 |
| `rename_fields_to_english.py` | NocoDB 필드명을 한글에서 영문으로 변경하는 스크립트 |
| `FIELD_MIGRATION.md` | NocoDB 필드명 한글→영문 마이그레이션 문서 |
| `create_price_history_table.py` | NocoDB `Price_History` 테이블(가격/재고 변동 이력, EAV 스타일) 생성 1회성 스크립트 |
| `category_lookup.py`/`notice_lookup.py`/`origin_lookup.py`/`address_lookup.py` | 네이버 API 조회용 1회성 스크립트 |
| `product_pages/scripts/` | 상세페이지 생성기 - 재사용 가능한 공용 도구만 남음: `build_pages.py`(신규 생성 패턴), `crop_hero.py`(히어로 이미지 반사 크롭), `export_sections.py`(섹션별 PNG 검증용 export). 카테고리별 1회성 배치 스크립트는 `archive/product_pages_scripts/`로 이동함 |
| `archive/` | 이미 끝난 1회성 조사/디버그/검증/수정 스크립트 + 더 이상 안 쓰는 데이터/로그 보관 (삭제 아님, 필요하면 재사용 가능 - `archive/README.md` 참고) |
| `naver_상품등록_템플릿.xlsx` | 등록용 엑셀 (126행: Switching 29 + WiFi 16 + Physical Security 13 + Door Access 31 + Integrations 8 + 기타 29) |
| `registered_log.json` | 등록된 상품들의 전체 API payload 로컬 로그 |
| `product_slug_map.json` | `sync_engine.py`가 UI Store 상품 URL을 만들 때 쓰는 name↔slug 매핑 (크롤링 프로젝트 때 생성) |
| `.env`/`.env.example` | 시크릿 (NocoDB/Scrape.do/Telegram/NAVER_CLIENT_ID·SECRET) |
| `.claude/launch.json` | `tbd-dashboard-nicegui`(NiceGUI :8080) |

### 접근 권한 필요한 외부 폴더 (git 저장소 밖, Google Drive 동기화)
- `.../TBD Seoul/Product Images/<제품폴더명>/` — 원본 제품 사진
- `.../TBD Seoul/Product Pages_html/` — 상세페이지 `.dc.html` 소스 + `assets/`(폰트/로고) + `exports/<slug>/`(번호 매겨진 PNG, main.py가 실제 업로드하는 이미지)
- NAS: `/volume1/docker/nicegui/` (Synology DS925+, `192.168.50.245`, SSH 계정 `jay`) — NiceGUI 대시보드 운영 환경

## 3. 현재 상태

알려진 미해결 버그나 진행 중인 작업 없음.

- **Price_History 테이블**: 로컬/NAS 양쪽 다 `NOCODB_HISTORY_TABLE_ID=mi258r3q4g5wu69`로 연결 완료, `https://my.tbd.kr/inventory`에서 운영 중. 아직 실제 Sync를 통해 쌓인 이력은 0건(다음 Sync 버튼 클릭부터 자연히 쌓이기 시작함) — 그래서 "15일 이상 품절" 섹션은 지금 비어있고, 미판매 상품 전체가 "기록 이전부터 품절"로 표시되는 게 정상.
- **자동 동기화 스케줄러**: NAS에서 가동 중. 매일 09:00 KST 전체 동기화 + 4시간마다 확인 필요 상품만 재조회. 스케줄 시각/주기를 바꾸려면 `sync_engine.py`의 `start_background_scheduler()` 안 `CronTrigger`/`IntervalTrigger` 파라미터만 수정하면 됨.
- **화이트/블랙 색상 옵션 관리**: 구매처마다 화이트/블랙 가격이 다른 35개 제품에 대해 `{화이트 SKU} Black` NocoDB 로우 생성 완료 (Category/Weight_KG/MSRP_USD/Naver_Product_No는 화이트와 동일, ADORAMA_ID/ASIN/BH_ID는 비어있음 → 27개는 B&H 코드 입력 완료, 실제 B&H 상품명과 대조 검증까지 마침). **다음 할 일**: 사용자가 각 Black 로우에 나머지 구매처 ID를 채워넣으면, 다음 Sync부터 자체 가격이 잡히고 `update_price_stock.py`가 네이버 "화이트"/"블랙" 옵션에 각각 다른 가격(추가금액)/재고를 반영함(ID 미입력 상태면 기존처럼 균일 적용 + 콘솔 안내). `UniFi Reader`/`UniFi G3 Reader Fingerprint`/`UniFi Retrofit Reader Fingerprint`는 화이트 자체가 NocoDB에 없어 이번엔 제외함.
- **NocoDB `Product_Page = "Clone"` 컨벤션**: 색상 옵션 클론 로우(위 35개 Black 로우)는 독립된 상세페이지/네이버 등록이 필요 없는, 화이트 로우의 옵션일 뿐이라는 뜻으로 사용자가 `Product_Page` 필드에 `Clone` 값을 도입함(`None`/`Simple`/`Detail`에 이어 4번째 옵션). `create_color_variant_rows.py`가 새로 만드는 로우에는 이 값을 자동으로 채움 - **앞으로 상품 목록을 다룰 때(대시보드 카운트, 상세페이지 생성 대상 파악 등) `Product_Page == "Clone"`인 로우는 "실제 등록 상품"이 아니라 "다른 로우의 색상 옵션"이라는 점을 감안할 것.**

**현재 수치**:
- 네이버 스마트스토어 등록 상품: **96개**
  - Switching: 29개
  - WiFi: 16개
  - Physical Security: 13개
  - Door Access: 31개
  - Integrations: 6개
  - 기타: 1개
- 상세페이지(HTML) 보유: **98개** (Naver 등록 96개 + 미등록 2개: Display Cast Lite, Mobile Router Industrial)
- NocoDB `Product_Page` 설정: **96개** (Detail 75개 + Simple 21개, 등록 상품 전체 커버) + **Clone 35개** (색상 옵션 클론 로우, 별도 상세페이지 불필요)
- NocoDB `Naver_Product_No` 연동: **96개**
- **NocoDB 필드명 (영문)**: `sale_price` (판매가), `purchase_cost` (구매 원가), `profit` (수익)
- 검색 키워드 추가: **58개 완료, 38개 대기** (IP 재등록 후 재실행 필요)
- 카테고리 최적화: **6개 완료** (NAS, 모바일 라우터 제품군)
- **Git/GitHub**: 로컬 git 커밋만 사용, GitHub 푸시 안 함 (private 레포 전환)
- **대시보드**: Streamlit 제거, NiceGUI만 사용 (`https://my.tbd.kr`)

## 4. 다음 작업 계획 (우선순위 순은 아니며, 이전에 합의된 로드맵)

1. **검색 키워드 일괄 추가 완료**: 네이버 커머스API 센터에서 현재 IP 재등록 후 `update_product_names_with_keywords.py` 재실행 — 실패한 38개 상품 키워드 추가
2. **대시보드 Phase 2**: `main.py`/`run_pipeline.py`/`update_price_stock.py`/`fix_delivery_settings.py`를 NiceGUI 대시보드의 "상품 등록" 페이지에서 버튼으로 실행 (dry-run/limit 안전장치 UI 포함)
3. **대시보드 Phase 3**: 디자인 디테일 폴리싱 (호버 상태, 아바타칩 실사용 등)
4. **대시보드 Phase 4**: 주문관리/배송관리 — 네이버 Pay-Order/Claims API 신규 연동 필요 (코드 전혀 없음, 그린필드). **착수 전 커머스API 앱에 주문/클레임 조회 권한이 실제로 있는지 확인 필수**
5. NocoDB에 다른 카테고리(Gateway, Routing 등)에도 미등록(`Naver_Product_No` 없음) 상품이 더 있는지 확인 — 사용자가 원하면 계속 등록 확장
6. **가격/재고 이력 기능 관찰**: NAS 배포는 완료됐으니, 앞으로 몇 차례 Sync를 돌려서 `Price_History`에 실제 이력이 잘 쌓이는지, `/inventory`의 "15일 이상 품절" 섹션이 시간이 지나며 의도대로 채워지는지 확인
7. **자동 동기화 스케줄러 관찰**: 다음날 09:00 KST 전체 동기화가 실제로 발동하는지, 4시간마다 확인 필요 상품 재조회가 정상 도는지 `docker-compose logs`/Telegram 알림으로 며칠 지켜보기. 문제 있으면 `sync_engine.start_background_scheduler()`의 트리거 설정 확인
8. **화이트/블랙 색상 옵션 마무리**: B&H 코드는 27/35 입력 + 실제 상품명 대조 검증 완료(불일치 없음, `UniFi Access Button Black` 1855250-REG만 "(Black)" 표기가 없어 직접 확인 권장). 나머지 ADORAMA_ID/ASIN 및 남은 BH_ID를 마저 채워넣고, Sync 후 `update_price_stock.py --dry-run`으로 옵션별 가격/재고가 의도대로 갈리는지 확인. `UniFi Reader`/`UniFi G3 Reader Fingerprint`/`UniFi Retrofit Reader Fingerprint`는 화이트 자체를 나중에 등록하게 되면 그때 Black 로우도 같이 생성

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
- **NiceGUI 대시보드 디자인 시스템**: 페이지 배경(연한 회색) ≠ 카드 배경(흰색)이 핵심 원칙. 버튼 색은 반드시 Tailwind `!bg-[...]` 강제 클래스 사용(일반 커스텀 클래스는 NiceGUI 기본 `color=primary`와의 명시도 싸움에서 짐). 활성 메뉴는 흰색/surface 배경(검정 아님, 명시적 요청으로 변경됨)
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

```bash
# 파일 업로드 (sshpass 필수)
sshpass -p 'JJ2120jj!!' scp -O -o StrictHostKeyChecking=no sync_engine.py config.py nocodb_client.py jay@192.168.50.245:/volume1/docker/nicegui/
sshpass -p 'JJ2120jj!!' scp -O -o StrictHostKeyChecking=no -r dashboard jay@192.168.50.245:/volume1/docker/nicegui/
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
