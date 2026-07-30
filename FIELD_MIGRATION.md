# NocoDB 필드명 한글→영문 마이그레이션

## 개요

2026-07-30: NocoDB 필드명의 한글 인코딩 문제로 인해 대시보드에서 데이터가 0으로 표시되는 이슈 발생. 모든 가격 관련 필드를 영문으로 변경하여 해결.

## 변경된 필드명

| 기존 (한글) | 변경 후 (영문) | 설명 |
|------------|---------------|------|
| 판매금액 | `sale_price` | 네이버 스마트스토어 판매가 |
| 구매원가 | `purchase_cost` | 실제 구매 원가 (Best Price 기반) |
| 수익 | `profit` | 판매가 - 구매원가 |

## 변경된 파일

### 핵심 파일
1. **`sync_engine.py`**
   - 테이블 헤더: "Sale Price", "Purchase Cost", "Profit"
   - 데이터 조회: `f.get("sale_price")`, `f.get("purchase_cost")`, `f.get("profit")`

2. **`update_price_stock.py`**
   - 네이버 판매가 동기화 시 `sale_price` 필드 사용
   - 독스트링 업데이트

3. **`export_prices_for_naver.py`**
   - CSV 헤더: `sale_price`, `purchase_cost`, `profit`
   - 필드 조회 코드 변경

4. **`add_ps_to_excel.py`**
   - 엑셀 템플릿 생성 시 `purchase_cost` 사용

5. **`nocodb_fix_fields.py`**
   - 필드 생성 스크립트의 필드명 영문화
   - 수식은 동일 (영문 필드명 참조)

### 기타 파일 (일회성 스크립트, 업데이트 안 함)
- `fix_integrations_prices.py`
- `rename_field_to_purchase_cost.py`
- `debug_nocodb_fields.py`

## NocoDB 필드 수식

영문 필드명으로 변경되었지만, 수식 로직은 동일합니다:

### `purchase_cost` (구매원가)
```
IF({In_Stock}, 
  ROUNDUP(
    ({Best_USD} * 1.0158 * {Exchange_Rate}) 
    + IF({Best_USD} > 200, ({Best_USD} * 1.0158 * {Exchange_Rate}) * 0.188, 0) 
    + (({Best_USD} * 1.0158 * {Exchange_Rate}) * 0.057) 
    + {Shipping_KRW}, 
  -2), 
0)
```
**중요**: 재고가 없으면 (`In_Stock = False`) 0으로 계산됨

### `sale_price` (판매금액)
```
ROUNDUP((
  ({MSRP_USD} * 1.0158 * {Exchange_Rate}) 
  + IF({MSRP_USD} > 200, ({MSRP_USD} * 1.0158 * {Exchange_Rate}) * 0.188, 0) 
  + (({MSRP_USD} * 1.0158 * {Exchange_Rate}) * 0.057) 
  + {Shipping_KRW}) * 1.10, 
-2)
```

### `profit` (수익)
```
IF({In_Stock}, {sale_price} - {purchase_cost}, 0)
```
**중요**: 재고가 없으면 0으로 계산됨

## 배포 절차

### 1. 로컬 코드 변경
```bash
# 핵심 파일 5개 수정 완료
git add sync_engine.py update_price_stock.py export_prices_for_naver.py add_ps_to_excel.py nocodb_fix_fields.py
git commit -m "NocoDB 필드명을 한글에서 영문으로 변경"
git push origin main
```

### 2. NocoDB UI에서 필드명 변경
1. https://nocodb.jayjeon.net 접속
2. Products 테이블 열기
3. 각 컬럼 헤더 클릭 → Edit Column:
   - `판매금액` → `sale_price`
   - `구매원가` → `purchase_cost`
   - `수익` → `profit`

**데이터는 그대로 유지됩니다 - 필드명만 변경**

### 3. NAS 배포
```bash
# sync_engine.py를 NAS에 업로드
scp -O -i ~/.ssh/id_ed25519_tbd_nas sync_engine.py jay@192.168.50.245:/volume1/docker/nicegui/

# NAS 대시보드 재시작
sshpass -p 'JJ2120jj!!' ssh -o StrictHostKeyChecking=no jay@192.168.50.245 \
  "cd /volume1/docker/nicegui && echo 'JJ2120jj!!' | sudo -S /usr/local/bin/docker-compose restart"
```

### 4. 브라우저 캐시 클리어
- Mac: `Cmd + Shift + R`
- Windows: `Ctrl + F5`

## 검증

### 로컬 테스트
```bash
# 필드명 확인
python3 -c "
from sync_engine import safe_fetch_records
records = safe_fetch_records()
if records:
    fields = records[0]['fields']
    print('sale_price:', fields.get('sale_price'))
    print('purchase_cost:', fields.get('purchase_cost'))
    print('profit:', fields.get('profit'))
"

# 재고 있는 상품 확인
python3 -c "
from sync_engine import safe_fetch_records
records = safe_fetch_records()
in_stock = [r for r in records if r['fields'].get('In_Stock')]
if in_stock:
    f = in_stock[0]['fields']
    print(f'SKU: {f.get(\"SKU\")}')
    print(f'sale_price: {f.get(\"sale_price\"):,}')
    print(f'purchase_cost: {f.get(\"purchase_cost\"):,}')
    print(f'profit: {f.get(\"profit\"):,}')
"
```

### 예상 결과
- **재고 있는 상품**: sale_price, purchase_cost, profit 모두 정상 금액
- **재고 없는 상품**: sale_price만 표시, purchase_cost와 profit은 0 (정상)

## 주의사항

1. **재고 없으면 purchase_cost/profit이 0**: NocoDB 수식이 `IF({In_Stock}, 계산식, 0)` 형태이므로 정상 동작입니다.

2. **기존 한글 필드명 참조 코드**: 일회성 스크립트나 더 이상 사용하지 않는 파일은 업데이트하지 않았습니다. 필요 시 개별 수정 필요.

3. **네이버 API 연동**: `update_price_stock.py`가 `sale_price` 필드를 사용하므로, 가격 동기화는 정상 작동합니다.

## 트러블슈팅

### 대시보드에 여전히 "최종가격"으로 표시
- 브라우저 캐시 문제: 강력 새로고침 (Cmd+Shift+R)
- NAS 코드 미반영: sync_engine.py 재배포 후 컨테이너 재시작

### purchase_cost가 모두 0
- NocoDB에서 필드명이 제대로 변경되었는지 확인
- 재고 없는 상품인지 확인 (In_Stock = False면 0이 정상)

### NocoDB API 연결 실패
- 네트워크 연결 확인 (5G ↔ WiFi 전환 시 IP 허용 목록 재등록 필요)
- NAS가 켜져 있는지 확인

## 관련 파일

- `/Users/cheil/tbd/rename_fields_to_english.py` - 필드명 자동 변경 스크립트 (네트워크 타임아웃으로 실패, 수동 변경으로 해결)
- `CLAUDE.md` - 프로젝트 전체 문서 (이 마이그레이션 내용 반영 필요)
