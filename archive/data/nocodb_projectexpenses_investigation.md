# NocoDB ProjectExpenses 테이블 조사 결과

**조사 날짜**: 2026-07-30  
**조사자**: Claude Code (Kiro)  
**문제**: LibreChat의 Claude가 생성했다는 ProjectExpenses 테이블(ID: m72i8atzqylc6yw)을 찾을 수 없음

---

## 1. 문제 요약

사용자가 LibreChat에 연결된 Claude에게 NocoDB에 프로젝트 비용 추적용 테이블 생성을 요청했고, Claude는 `ProjectExpenses` 테이블을 생성했다고 보고했으나, 실제로는:
- NocoDB UI에서 테이블이 보이지 않음
- 테이블 ID로 직접 조회 시 404 오류 발생
- 전체 테이블 목록에도 존재하지 않음

---

## 2. 조사 결과

### 2.1 현재 NocoDB 환경 정보

**Workspace ID**: `wxrolsu5`  
**Base ID**: `pqlruah70l8clo1`  
**Base 이름**: UniFi Supply  
**NocoDB URL**: https://nocodb.jayjeon.net  
**API Token**: nc_pat_NY3NcYP46RmFDjPRBwrfb5FeRBCJmVxrEuws4vNs (조사 시 사용)

### 2.2 현재 존재하는 테이블

```
1. Products (ID: mo6797mk38fuelu)
2. Expense (ID: mu382v0vk7rkih9)
```

**ProjectExpenses 테이블은 존재하지 않음**

### 2.3 LibreChat 대화 분석

대화 로그(`/Users/cheil/Desktop/LibreChat_Claude NocoDB Integration.txt`) 분석 결과:

#### Phase 1: 잘못된 Base에 테이블 생성 (라인 100-330)
- LibreChat Claude가 Base ID를 `p8kugz1c66qjd51`로 잘못 식별
- 이 잘못된 Base에 `ProjectExpenses` 테이블 생성 (ID: `m9q0amtb4ruu88v`)
- 사용자는 이 테이블을 UI에서 볼 수 없었음 (당연히, 다른 Base였으므로)

#### Phase 2: Expense 테이블 수정 시도 (라인 966-1143)
- 사용자가 직접 만든 `Expense` 테이블 발견
- LibreChat Claude가 이 테이블에 필드 추가 시도
- 뷰 컬럼 설정 `show: false` 문제 발견 및 수정 시도

#### Phase 3: 올바른 Base에 재생성 시도 (라인 1983-2160)
- 사용자가 올바른 Base ID (`pqlruah70l8clo1`) 제공
- LibreChat Claude가 올바른 Base에 테이블 재생성 시도
- 테이블 ID: `mn1j2dkc8hfqy40` 생성 보고
- 뷰 ID: `vwbu4qe88u3lz6q`
- 모든 컬럼 `show: true` 설정 완료 보고
- `order: 3` 설정 완료 보고

### 2.4 실제 검증 결과

**테이블 ID 직접 조회**:
```bash
curl -H "xc-token: nc_pat_NY3NcYP46RmFDjPRBwrfb5FeRBCJmVxrEuws4vNs" \
  https://nocodb.jayjeon.net/api/v2/meta/tables/m72i8atzqylc6yw
```
결과: `404 Not Found - Table 'm72i8atzqylc6yw' not found`

**전체 테이블 목록 조회**:
```bash
curl -H "xc-token: nc_pat_NY3NcYP46RmFDjPRBwrfb5FeRBCJmVxrEuws4vNs" \
  https://nocodb.jayjeon.net/api/v2/meta/bases/pqlruah70l8clo1/tables
```
결과: Products, Expense만 존재

---

## 3. 근본 원인 분석

### 3.1 잘못된 Base ID 사용
LibreChat Claude가 초기에 Base 목록을 조회했을 때 잘못된 Base ID를 선택했습니다:
- 사용한 ID: `p8kugz1c66qjd51` (존재하지 않거나 다른 Base)
- 올바른 ID: `pqlruah70l8clo1` (UniFi Supply)

### 3.2 API 응답 검증 부족
LibreChat Claude가:
- 테이블 생성 API 호출 후 성공 응답을 받았다고 보고
- 하지만 실제로 올바른 Base에 생성되었는지 재확인하지 않음
- UI에서 보이지 않는다는 사용자 피드백에도 근본 원인(잘못된 Base) 파악 실패

### 3.3 NocoDB의 뷰 설정 문제
API로 생성된 테이블의 컬럼들이 기본적으로 `show: false`로 설정되는 것도 혼란을 가중시킴:
- 테이블은 존재하지만 UI에 표시되지 않음
- 이 문제가 Base ID 오류를 가려버림

---

## 4. 결론

**ProjectExpenses 테이블은 생성되지 않았습니다.**

LibreChat Claude가:
1. 잘못된 Base에 테이블을 생성하거나
2. 올바른 Base에 생성했다고 보고했지만 실제로는 API 오류로 생성 실패
3. 또는 생성 후 다른 이유로 삭제됨

현재 사용자의 Base (`pqlruah70l8clo1`)에는 **ProjectExpenses 테이블이 존재하지 않습니다**.

---

## 5. 권장 조치

### 5.1 테이블 재생성 필요
올바른 Base ID (`pqlruah70l8clo1`)에 ProjectExpenses 테이블을 새로 생성해야 합니다.

### 5.2 필요한 필드
LibreChat 대화에서 합의된 구조:
- Title (SingleLineText) - 비용 제목
- ProjectName (SingleLineText) - 프로젝트명
- ExpenseType (SingleSelect) - Equipment, Parts, Service, Software, Other
- Amount (Currency) - 금액
- Currency (SingleSelect) - KRW, USD, EUR, JPY, CNY
- PaymentMethod (SingleSelect) - Credit Card, Debit Card, Cash, Bank Transfer, Other
- Date (Date) - 날짜
- Notes (LongText) - 메모/설명
- Status (SingleSelect) - Planned, Paid, Refunded, Cancelled

### 5.3 생성 후 검증 절차
1. 테이블 생성 API 호출
2. 반환된 테이블 ID로 직접 조회하여 실제 존재 확인
3. Base의 전체 테이블 목록에서 확인
4. 뷰 컬럼 설정을 `show: true`로 변경
5. 테이블 `order` 값 설정
6. NocoDB UI에서 실제로 보이는지 최종 확인

---

## 6. 참고 자료

- LibreChat 대화 로그: `/Users/cheil/Desktop/LibreChat_Claude NocoDB Integration.txt`
- 조사 스크립트: `/Users/cheil/tbd/find_project_expenses_table.py`
- Expense 테이블 확인 스크립트: `/Users/cheil/tbd/check_expense_table.py`
