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
| `product_builder.py` / `image_uploader.py` | 등록 payload 생성 / 이미지 업로드 |
| `run_pipeline.py` | main.py → sync_naver_ids_to_nocodb.py → update_price_stock.py 순차 실행 |
| `sync_naver_ids_to_nocodb.py` | `TARGET_PRODUCTS` 매핑, 네이버 채널상품번호를 NocoDB에 반영 |
| `update_price_stock.py` | NocoDB → 네이버 가격/재고 동기화 |
| `fix_delivery_settings.py` | 이미 등록된 상품의 배송사/배송비/원산지 일괄 수정 |
| `update_live_customs_image.py` | **신규**: 라이브 상세페이지의 통관 안내 섹션 이미지만 교체 |
| `category_lookup.py`/`notice_lookup.py`/`origin_lookup.py`/`address_lookup.py` | 네이버 API 조회용 1회성 스크립트 |
| `product_pages/scripts/` | 상세페이지 생성기: `build_pages.py`(공용 빌더+공용 섹션 텍스트), `gen_batch1.py`, `gen_batch2.py`, `gen_flexxg.py`, `export_sections.py`(Playwright PNG export), `crop_hero.py` |
| `naver_상품등록_템플릿.xlsx` | 등록용 엑셀 (현재 29행: 기존 26 + 신규 3) |
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

## 4. 현재 작업 상태

이번 세션에서 진행한 작업은 **전부 완료 및 검증됨**. 마지막 액션은 커밋 `74ad9c6`을 GitHub에 push. 알려진 미해결 버그나 진행 중인 작업 없음.

**현재 수치**:
- 네이버 스마트스토어 등록 상품: 29개 (이전 26개)
- 상세페이지(HTML) 보유: 29개
- NocoDB `Product_Page = Detail` 설정: 29개
- NocoDB `Naver_Product_No` 연동: 29개

## 5. 다음 작업 계획 (우선순위 순은 아니며, 이전에 합의된 로드맵)

1. **대시보드 Phase 2**: `main.py`/`run_pipeline.py`/`update_price_stock.py`/`fix_delivery_settings.py`를 NiceGUI 대시보드의 "상품 등록" 페이지에서 버튼으로 실행 (dry-run/limit 안전장치 UI 포함)
2. **대시보드 Phase 3**: 디자인 디테일 폴리싱 (호버 상태, 아바타칩 실사용 등)
3. **대시보드 Phase 4**: 주문관리/배송관리 — 네이버 Pay-Order/Claims API 신규 연동 필요 (코드 전혀 없음, 그린필드). **착수 전 커머스API 앱에 주문/클레임 조회 권한이 실제로 있는지 확인 필수**
4. NocoDB에 Switching 외 다른 카테고리(AP, Door Access, Physical Security 등)에도 미등록(`Naver_Product_No` 없음) 상품이 더 있는지 확인 — 사용자가 원하면 계속 등록 확장
5. Git 히스토리에 남아있는 예전 네이버 시크릿 완전 삭제 여부 결정 (재발급은 했지만 히스토리 정리는 별도 논의 필요)
6. `requirements.txt`에 `nicegui` 추가 필요 (현재 누락)

## 6. 특이사항

- **커밋 컨벤션**: 논리적으로 분리된 원자적 커밋, 본문은 "왜"를 설명(한국어), 끝에 `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`. **레포가 public이므로 커밋 전 시크릿 포함 여부 항상 재확인**
- **라이브 데이터 수정 스크립트 안전 패턴**: 전부 `--dry-run`(미리보기) + `--limit N`(N개만 테스트) 지원. 항상 1개 테스트 → 검증 → 전체 실행 순서를 따름
- **네이버 API PUT 패턴**: GET으로 전체 객체 조회 → 필요한 필드만 교체 → 전체를 그대로 PUT (건드리지 않은 필드도 다 넣어야 함, 안 그러면 날아감)
- **네이버 API 자주 겪는 이슈**:
  - IP 허용 목록 — 네트워크 바뀌면(5G ↔ 집 와이파이) `GW.IP_NOT_ALLOWED` 403 발생, 커머스API센터에서 재등록 필요
  - `statusType: OUTOFSTOCK`은 GET엔 나오지만 PUT엔 거부됨 → `SALE`로 정규화 후 전송
  - `visitAddressId`는 0이 아니라 **필드 자체를 빼야** 방문수령 불가로 처리됨
  - 신규 등록 시 `stockQuantity=0`은 거부됨 (기존 상품 PUT 수정은 0 허용) → 1로 등록 후 실제값으로 보정
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
