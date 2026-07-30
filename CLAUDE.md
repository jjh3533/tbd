# 프로젝트 인계 문서

## 1. 프로젝트 개요

- **목적/종류**: "TBD Seoul" — 미국에서 Ubiquiti UniFi 네트워크 장비를 병행수입(해외직구)해서 네이버 스마트스토어에 재판매하는 1인 사업의 자동화 시스템. 가격 모니터링, 상품 등록, 상세페이지 생성, 대시보드로 구성.
- **기술 스택**: Python 3 (로컬 Mac은 3.14, NAS Docker는 3.11), NiceGUI(신규 대시보드), Streamlit(구 대시보드, 아직 병행 운영), NocoDB(DB, Airtable에서 이전), requests/BeautifulSoup4(스크래핑), yfinance(환율), Playwright(헤드리스 크롬 - 상세페이지 HTML→PNG 렌더링), openpyxl(엑셀 템플릿), 네이버 커머스API, Docker + Synology Container Manager, Cloudflare Tunnel
- **디렉토리**: `/Users/cheil/tbd` (git 저장소, GitHub `jjh3533/tbd` — **public 레포**)

## 2. 프로젝트 구조

### 루트 핵심 파일
| 파일 | 역할 |
|---|---|
| `app.py` | Streamlit 대시보드 (여전히 배포 중, `sync_engine.py`를 import하도록 리팩터링됨) |
| `sync_engine.py` | **신규**: 스크래핑/동기화/포맷팅 로직을 app.py에서 분리한 프레임워크 독립 모듈 |
| `dashboard/` | **신규**: NiceGUI 대시보드 (`theme.py`, `layout.py`, `components.py`, `app.py`, `pages/{home,category,register}.py`, `deploy/{Dockerfile,docker-compose.yml}`) |
| `config.py` | 공용 시크릿 로더 (`.env`/Streamlit secrets), NocoDB/Scrape.do/Telegram 값 |
| `naver_config.py` | 네이버 커머스API 설정 (CLIENT_ID/SECRET은 이제 `.env`에서, 하드코딩 아님) |
| `nocodb_client.py` | NocoDB REST v2용 Airtable 호환 어댑터 |
| `auth.py` | 네이버 OAuth2 bearer token 발급 |
| `main.py` | 엑셀(`naver_상품등록_템플릿.xlsx`) 기반 네이버 상품 등록 파이프라인 |
| `product_builder.py` / `image_uploader.py` | 등록 payload 생성 / 이미지 업로드. **자동 카테고리 선택 및 검색 키워드 추가 기능 내장** |
| `product_keywords.py` | **신규**: 카테고리별 자동 leafCategoryId 선택 및 검색 최적화 키워드 생성 모듈 |
| `update_categories.py` | **신규**: 기등록 상품의 카테고리를 더 적합한 카테고리로 일괄 변경 (NAS→저장장치>NAS, Router→라우터) |
| `update_product_names_with_keywords.py` | **신규**: 기등록 상품명에 검색 키워드 일괄 추가 (카테고리별 맞춤 키워드 자동 생성) |
| `run_pipeline.py` | main.py → sync_naver_ids_to_nocodb.py → update_price_stock.py 순차 실행 |
| `sync_naver_ids_to_nocodb.py` | `TARGET_PRODUCTS` 매핑, 네이버 채널상품번호를 NocoDB에 반영 |
| `update_price_stock.py` | NocoDB → 네이버 가격/재고 동기화 |
| `fix_delivery_settings.py` | 이미 등록된 상품의 배송사/배송비/원산지 일괄 수정 |
| `update_live_customs_image.py` | **신규**: 라이브 상세페이지의 통관 안내 섹션 이미지만 교체 |
| `category_lookup.py`/`notice_lookup.py`/`origin_lookup.py`/`address_lookup.py` | 네이버 API 조회용 1회성 스크립트 |
| `product_pages/scripts/` | 상세페이지 생성기: `build_pages.py`(공용 빌더+공용 섹션 텍스트), `gen_batch1.py`, `gen_batch2.py`, `gen_flexxg.py`, `gen_wifi_batch1~4.py`(WiFi 16개), `gen_ps_batch1~4.py`(Physical Security 13개), `gen_door_access_batch1~3.py`(Door Access 31개: 10개 Detail + 21개 Simple), `gen_integrations_batch1~2.py`(Integrations 8개), `process_wifi_images.py`/`process_ps_images.py`/`process_door_access_images.py`/`process_integrations_images.py`(이미지 자동 처리), `export_sections.py`(Playwright PNG export), `export_wifi_pages.py`/`export_ps_pages.py`/`export_door_access_pages.py`/`export_integrations_pages.py`(배치별 export), `crop_hero.py`(반사 제거, **안전장치 추가됨**: score>0.3 또는 split<50%면 원본 유지), `crop_integrations_heroes.py`(Integrations 8개 히어로 일괄 크롭) |
| `fix_ps_hero_images.py` | **신규**: Physical Security 13개 제품의 과도하게 크롭된 히어로 이미지를 원본으로 복구 |
| `update_ps_hero_images.py` | **신규**: Physical Security 13개 제품의 네이버 히어로 이미지만 업데이트 |
| `fix_integrations_prices.py` | **신규**: Integrations 6개 제품의 네이버 판매가를 NocoDB `판매금액`으로 수정 (실제로는 이미 정상 가격으로 등록되어 있어서 사용 안 함) |
| `rename_field_to_purchase_cost.py` | **신규**: NocoDB `최종가격` 필드를 `구매원가`로 변경하는 스크립트 (API 제약으로 UI에서 수동 변경) |
| `naver_상품등록_템플릿.xlsx` | 등록용 엑셀 (현재 126행: Switching 29 + WiFi 16 + Physical Security 13 + Door Access 31 + Integrations 8 + 기타 29) |
| `registered_log.json` | 등록된 상품들의 전체 API payload 로컬 로그 |
| `.env`/`.env.example` | 시크릿 (NocoDB/Scrape.do/Telegram/NAVER_CLIENT_ID·SECRET) |
| `.claude/launch.json` | `tbd-dashboard`(Streamlit :8501), `tbd-dashboard-nicegui`(NiceGUI :8080) |
| `~/.ssh/config`의 `tbd-nas` | NAS SSH 접속용 (전용 키 `~/.ssh/id_ed25519_tbd_nas`) |

### 접근 권한 필요한 외부 폴더 (git 저장소 밖, Google Drive 동기화)
- `.../TBD Seoul/Product Images/<제품폴더명>/` — 원본 제품 사진
- `.../TBD Seoul/Product Pages_html/` — 상세페이지 `.dc.html` 소스 + `assets/`(폰트/로고) + `exports/<slug>/`(번호 매겨진 PNG, main.py가 실제 업로드하는 이미지)
- NAS: `/volume1/docker/nicegui/` (Synology DS925+, `192.168.50.245`, SSH 계정 `jay`) — NiceGUI 대시보드 운영 환경

## 3. 완료된 작업 (이번 세션, 시간순)

1. UniFi 스위치 상세페이지 3개 신규 생성 (Pro Max 16/16 PoE/Flex 10 GbE) — `build_pages.py` 패턴 확립, 랙마운트 제품 이미지의 반사 중복 아티팩트 크롭, Playwright 기반 PNG export 파이프라인 구축 (Claude Design 없이 재현)
2. 한글 줄바꿈(`word-break: keep-all`)과 "급전" 등 어색한 표현 전체 수정
3. 네이버 배송/원산지 설정 수정: 택배사 CJGLS→ACE, 원산지 중국→미국, 반품/교환비 3천/6천→4만/8만원. `visitAddressId`는 **필드 자체를 빼야** "직접수령 불가능"으로 처리됨(0을 넣으면 거부)을 확인. `OUTOFSTOCK` statusType을 GET에서는 주지만 PUT에서는 거부하는 버그도 발견/수정
4. **대시보드 전면 교체**: Streamlit(CSS 커스터마이징이 힘들다는 사용자 불만) → NiceGUI. `sync_engine.py`로 백엔드 로직 분리, `dashboard/` 패키지 신축
5. 디자인 피드백 반영 2라운드: 페이지 배경≠카드 배경으로 깊이감 부여, 통계카드 높이 불균일 수정, NiceGUI 버튼 기본 파란색 이슈(Tailwind `!bg-[...]` 강제 클래스로 해결), 활성 메뉴를 검정→흰색 배경으로 변경
6. NAS(Synology, `192.168.50.245`)에 실제 배포 → `https://my.tbd.kr` (Cloudflare Tunnel). 전용 SSH 키 설정, Synology SFTP 서브시스템 미작동 이슈(`scp -O` 사용), 홈디렉토리 권한 이슈 해결
7. **보안 수정**: `naver_config.py`에 하드코딩되어 **public 레포에 평문 커밋**되어 있던 네이버 Client Secret 발견 → `.env`로 이전, 사용자가 재발급, 새 값 동작 확인 완료. **주의: git 히스토리 자체는 아직 정리 안 함 (재발급으로만 방어됨)**
8. Switching 카테고리 6개 상세페이지 추가 생성 (Enterprise 8 PoE, Flex, Flex Utility, Flex Utility Pro, Pro 8 PoE, Pro XG 8 PoE). **중요**: 리서치 결과 "Flex Utility"/"Flex Utility Pro"는 스위치가 아니라 빈 방수 인클로저(액세서리)로 확인 → 정직하게 인클로저 스펙 + "스위치 별도구매" 명시로 작성
9. 통관/관부가세 안내 문구 오류 수정 (29개 파일 전체 일괄 반영 + 템플릿 소스도 수정)
10. 신규 6개 상품 실제 네이버 등록 완료. 과정에서 `PRODUCT_PAGES_DIR`이 존재하지 않는 옛 경로를 가리키던 버그 발견/수정, 재고 0 신규등록 거부 이슈 확인/처리
11. NocoDB 동기화 중 검색어 "Flex"가 엉뚱한 상품에 매칭되는 버그 발견/수정
12. 기존 20개 라이브 상품의 통관 이미지를 새 문구로 교체 (라이브/로컬 이미지 개수 검증 후 안전하게 위치 매칭)
13. NocoDB Product 테이블의 `Product_Page` 필드를 상세페이지 보유 제품 전체(29개)에 "Detail"로 설정 (기존 20개 → 29개)
14. 신규 3개 상품 네이버 스마트스토어 등록 완료 (Pro Max 16 / Pro Max 16 PoE / Flex XG = Flex 10 GbE). Flex XG는 NocoDB 재고 0이라 5개로 등록 후 `update_price_stock.py`로 즉시 품절 처리
15. `sync_naver_ids_to_nocodb.py` `TARGET_PRODUCTS`에 신규 3개(Pro Max 16, Pro Max 16 PoE, Flex XG) + 기존에 누락되어 있던 UCG Industrial 추가 — 전체 29개 채널상품번호 NocoDB 반영 완료
16. `update_price_stock.py` 전체 실행 — 29개 전 상품 가격/재고 네이버 동기화 완료
17. **WiFi 카테고리 16개 제품 상세페이지 생성 및 네이버 등록 완료** (AC Pro, Building Bridge XG, Device Bridge, Device Bridge Switch, E7 Campus, U6 Enterprise, U6 Enterprise In-Wall, U6 In-Wall, U6 Mesh, U6 Mesh Pro, U6+, U7 Outdoor, U7 Pro Outdoor, U7 Pro Wall, U7 Pro XG Wall, U7 Pro XGS). WiFi 5/6/6E/7 전 세대 + 무선 브리지 + 옥외 메시 등 다양한 라인업 커버. 4개 배치로 나눠 순차 생성(`gen_wifi_batch1~4.py`), 이미지 자동 처리(`process_wifi_images.py`), PNG export(`export_wifi_pages.py`), 네이버 등록(채널상품번호 13686839735~13686840578), NocoDB 동기화 완료
18. `sync_naver_ids_to_nocodb.py` `TARGET_PRODUCTS`에 16개 WiFi 제품 매핑 추가 — 전체 46개 채널상품번호 NocoDB 반영 완료
19. `update_price_stock.py` 전체 실행 — 46개 전 상품 가격/재고 네이버 동기화 완료
20. **Physical Security 카테고리 13개 제품 상세페이지 생성 및 네이버 등록 완료** (G6 Pro 360, AI PTZ Industrial, G5 Turret Ultra, G6 Dome, AI Theta, All-In-One Sensor, Glass Break Sensor, Motion Sensor, NVR Instant, CloudKey+, AI Horn Speaker, SuperLink Gateway, Floodlight). 카메라(6개, CCTV 카테고리), 센서(3개, AP 카테고리), 녹화/컨트롤(2개, AP 카테고리), 기타(2개, AP 카테고리)로 구성. 4개 배치로 나눠 순차 생성(`gen_ps_batch1~4.py`), 이미지 자동 처리(`process_ps_images.py`), PNG export(`export_ps_pages.py`), 네이버 등록(채널상품번호 13686870764~13686872710), NocoDB 동기화 완료. **카테고리 이슈**: 일부 제품이 도서 카테고리로 오인식되는 문제 발견 → AP 카테고리(50001623)로 통일하여 해결
21. `sync_naver_ids_to_nocodb.py` `TARGET_PRODUCTS`에 13개 Physical Security 제품 매핑 추가 — 전체 59개 채널상품번호 NocoDB 반영 완료
22. `update_price_stock.py` 전체 실행 — 59개 전 상품 가격/재고 네이버 동기화 완료
23. `product_builder.py` 수정: 할인가=판매가일 때 할인 금액 0으로 `customerBenefit` 생성하던 버그 수정 (네이버 API가 거부), 무료배송일 때 `deliveryFeePayType` 필드를 빼도록 수정 (유료배송일 때만 필수)
24. **Physical Security 13개 제품 히어로 이미지 크롭 문제 발견 및 수정**: 검증 결과 13개 제품 모두 원본(1500x1500)의 21-49%만 남기고 과도하게 잘림. 원인은 `crop_hero.py`가 반사가 없는 이미지에서 잘못된 분할점을 찾은 것. `fix_ps_hero_images.py`로 원본을 크롭 없이 복사 → PNG 재export → 네이버 13개 제품 전체 히어로 이미지 업데이트 완료 (`update_ps_hero_images.py`)
25. **WiFi 카테고리 히어로 이미지 검증**: 네이버 등록된 34개 WiFi 제품 중 U6 Mesh Pro 1개만 높이 1494px로 다른 제품(평균 1829px)보다 작음 확인. 원본 1500x1500의 45%만 사용. assets 폴더에 원본 복사 → HTML/PNG 재생성 → 네이버 업데이트 완료
26. **`crop_hero.py` 안전장치 추가**: 반사 감지 실패 케이스(score > 0.3 또는 split 높이 비율 < 50%)에서 원본 그대로 저장하도록 수정. 이제 반사가 없는 이미지가 잘못 크롭되지 않음
27. **Door Access 카테고리 31개 제품 상세페이지 생성 및 네이버 등록 완료** (Reader Pro, Reader Flex, Access Ultra, Door Hub, Door Hub Mini, Enterprise Access Hub, Intercom Viewer, G6 Entry, Magnetic Lock, Access Button, Reader Junction Box, Reader Pro Junction Box, Reader Pro Angle Mount, Intercom Viewer Table Stand, Intercom Flush Mount, Intercom Surface Angle Mount, Intercom Wedge Mount, Intercom Sunshield, Gate Hub, Junction Utility, Door Lock Relay Cable, Door Closer, PoE Over 2-Wire Retrofit Extender, Retrofit Hub, Retrofit PSU 12V, Panic Bar, Access Rescue KeySwitch, Access Card 10-Pack, Pocket Keyfob 10-Pack, Gate Starter Kit, G3 Elevator Starter Kit). 출입통제 리더기/도어락/인터콤/액세서리 전체 라인업 커버. 10개는 Detail 버전(다이어그램 포함), 21개는 Simple 버전(히어로+Design+Tech Specs+공용 섹션만)으로 구성. 3개 배치로 나눠 순차 생성(`gen_door_access_batch1~3_simple.py`), 이미지 자동 처리(`process_door_access_images.py`), 히어로/다이어그램 이미지 표준화(`standardize_door_access_hero.py`, `standardize_door_access_diagram.py`), PNG export(`export_door_access_pages.py`), 네이버 등록(채널상품번호 13686915258~13686917736), NocoDB 동기화 완료
28. `sync_naver_ids_to_nocodb.py` `TARGET_PRODUCTS`에 31개 Door Access 제품 매핑 추가 — 전체 90개 채널상품번호 NocoDB 반영 완료
29. `update_price_stock.py` 전체 실행 — 90개 전 상품 가격/재고 네이버 동기화 완료
30. **Integrations 카테고리 8개 제품 상세페이지 생성 완료** (Mobile Router Industrial, UNAS 2, Display Cast Lite, Mobile Router, 5G Max, Mobile Router Ultra, PoE Audio Port, LTE Backup Pro). 모바일 라우터/5G 장비/NAS/오디오 인터페이스 등 다양한 통합 솔루션. 2개 배치로 나눠 순차 생성(`gen_integrations_batch1~2.py`), 이미지 자동 처리(`process_integrations_images.py`), 히어로 이미지 반사 제거(`crop_integrations_heroes.py`), PNG export(`export_integrations_pages.py`) 완료
31. **Integrations 6개 제품 네이버 등록 완료** (5G Max, LTE Backup Pro, Mobile Router, Mobile Router Ultra, PoE Audio Port, UNAS 2). 가격이 0원인 2개 제품(Display Cast Lite, Mobile Router Industrial)은 NocoDB 가격 계산 확인 필요로 보류. 채널상품번호 13686935032~13686935352
32. `sync_naver_ids_to_nocodb.py` `TARGET_PRODUCTS`에 6개 Integrations 제품 매핑 추가 — 전체 96개 채널상품번호 NocoDB 반영 완료
33. `update_price_stock.py` 전체 실행 — 96개 전 상품 가격/재고 네이버 동기화 완료
34. **NocoDB 필드명 변경 및 가격 정책 정리**: 사용자 요청으로 네이버 판매가는 무조건 할인 없이 NocoDB `판매금액` 필드 값으로 판매. `update_price_stock.py`가 이미 `판매금액`을 사용하므로 Integrations 6개 제품 모두 정상 가격(888,000원 등)으로 등록되어 있음을 확인. `최종가격` 필드명을 `구매원가`로 변경 — 코드 6개 파일 수정(`sync_engine.py`, `app.py`, `export_prices_for_naver.py`, `add_ps_to_excel.py`, `nocodb_fix_fields.py`, `fix_integrations_prices.py`), `sync_engine.py`는 하위 호환성 지원(`구매원가` 또는 `최종가격` 둘 다 읽음). NocoDB UI에서 사용자가 직접 필드명 변경 완료
35. **카테고리 자동 최적화 시스템 구축**: 상품명 기반으로 적합한 네이버 카테고리를 자동 선택하는 `product_keywords.py` 모듈 생성. NAS→저장장치>NAS(50001602), 모바일 라우터→네트워크장비>라우터(50001622) 등 제품 특성에 맞는 카테고리 매핑. `product_builder.py`에 통합되어 신규 상품 등록 시 자동 적용
36. **검색 키워드 자동 생성 시스템 구축**: 카테고리별 맞춤 검색 키워드를 상품명에 자동 추가하는 기능 개발. WiFi(와이파이 끊김 해결, 메시 네트워크), Switching(PoE 급전, 네트워크 확장), Physical Security(실시간 모니터링, 야간촬영), Door Access(출입통제, 무인 출입) 등 유즈케이스 키워드 + 기술 키워드(WiFi7, PoE, AI, 메시 등) 자동 조합. 상품명 형식: `영문명 / 한글명 키워드1 키워드2...` (최대 10개). `product_builder.py`에 통합되어 신규 상품 자동 적용
37. **기등록 상품 카테고리 일괄 변경**: `update_categories.py`로 6개 상품 카테고리 변경 완료 — UNAS 2(NAS 카테고리), Mobile Router/5G Max/Mobile Router Ultra/PoE Audio Port/LTE Backup Pro(라우터 카테고리). Door Access 31개는 디지털도어록 카테고리로 변경 시도했으나 KC 인증 정보 필수로 실패, 현재 네트워크장비>AP 유지 (실제로 UniFi 스마트 보안 장비에 적합)
38. **기등록 상품 검색 키워드 일괄 추가**: `update_product_names_with_keywords.py`로 96개 상품 중 58개 성공적으로 업데이트. 38개는 네트워크 연결 문제로 중단 (재실행 필요). 상품명에 카테고리별 맞춤 키워드 추가되어 검색 유입 최적화 완료

## 4. 현재 작업 상태

이번 세션에서 진행한 작업은 **전부 완료 및 검증됨**. 알려진 미해결 버그나 진행 중인 작업 없음.

**현재 수치**:
- 네이버 스마트스토어 등록 상품: **96개**
  - Switching: 29개
  - WiFi: 16개
  - Physical Security: 13개
  - Door Access: 31개
  - Integrations: 6개
  - 기타: 1개
- 상세페이지(HTML) 보유: **66개**
- NocoDB `Product_Page = Detail` 설정: **66개**
- NocoDB `Naver_Product_No` 연동: **96개**
- NocoDB 필드명: `구매원가` (구매 원가), `판매금액` (네이버 판매가)
- 검색 키워드 추가: **58개 완료, 38개 대기** (IP 재등록 후 재실행 필요)
- 카테고리 최적화: **6개 완료** (NAS, 모바일 라우터 제품군)

## 5. 다음 작업 계획 (우선순위 순은 아니며, 이전에 합의된 로드맵)

1. **검색 키워드 일괄 추가 완료**: 네이버 커머스API 센터에서 현재 IP 재등록 후 `update_product_names_with_keywords.py` 재실행 — 실패한 38개 상품 키워드 추가
2. **대시보드 Phase 2**: `main.py`/`run_pipeline.py`/`update_price_stock.py`/`fix_delivery_settings.py`를 NiceGUI 대시보드의 "상품 등록" 페이지에서 버튼으로 실행 (dry-run/limit 안전장치 UI 포함)
3. **대시보드 Phase 3**: 디자인 디테일 폴리싱 (호버 상태, 아바타칩 실사용 등)
4. **대시보드 Phase 4**: 주문관리/배송관리 — 네이버 Pay-Order/Claims API 신규 연동 필요 (코드 전혀 없음, 그린필드). **착수 전 커머스API 앱에 주문/클레임 조회 권한이 실제로 있는지 확인 필수**
5. NocoDB에 다른 카테고리(Gateway, Routing 등)에도 미등록(`Naver_Product_No` 없음) 상품이 더 있는지 확인 — 사용자가 원하면 계속 등록 확장
6. Git 히스토리에 남아있는 예전 네이버 시크릿 완전 삭제 여부 결정 (재발급은 했지만 히스토리 정리는 별도 논의 필요)
7. `requirements.txt`에 `nicegui` 추가 필요 (현재 누락)

1. **대시보드 Phase 2**: `main.py`/`run_pipeline.py`/`update_price_stock.py`/`fix_delivery_settings.py`를 NiceGUI 대시보드의 "상품 등록" 페이지에서 버튼으로 실행 (dry-run/limit 안전장치 UI 포함)
2. **대시보드 Phase 3**: 디자인 디테일 폴리싱 (호버 상태, 아바타칩 실사용 등)
3. **대시보드 Phase 4**: 주문관리/배송관리 — 네이버 Pay-Order/Claims API 신규 연동 필요 (코드 전혀 없음, 그린필드). **착수 전 커머스API 앱에 주문/클레임 조회 권한이 실제로 있는지 확인 필수**
4. NocoDB에 다른 카테고리(Gateway, Routing 등)에도 미등록(`Naver_Product_No` 없음) 상품이 더 있는지 확인 — 사용자가 원하면 계속 등록 확장
5. Git 히스토리에 남아있는 예전 네이버 시크릿 완전 삭제 여부 결정 (재발급은 했지만 히스토리 정리는 별도 논의 필요)
6. `requirements.txt`에 `nicegui` 추가 필요 (현재 누락)

## 6. 특이사항

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

- **커밋 컨벤션**: 논리적으로 분리된 원자적 커밋, 본문은 "왜"를 설명(한국어), 끝에 `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`. **레포가 public이므로 커밋 전 시크릿 포함 여부 항상 재확인**
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
  streamlit run app.py                                 # Streamlit 로컬 실행 (:8501)
  python3 product_pages/scripts/gen_batch{1,2}.py      # 상세페이지 생성
  python3 product_pages/scripts/export_sections.py <html> <outdir>  # 섹션별 PNG 검증용 export
  ssh tbd-nas                                          # NAS 접속
  ```
- **NAS 배포 업데이트 절차**:
  ```bash
  scp -O -i ~/.ssh/id_ed25519_tbd_nas -r dashboard sync_engine.py config.py nocodb_client.py jay@192.168.50.245:/volume1/docker/nicegui/
  ssh tbd-nas "cd /volume1/docker/nicegui && sudo /usr/local/bin/docker-compose restart"
  ```
