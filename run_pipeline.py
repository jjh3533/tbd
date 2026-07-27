"""
'상품 등록 -> 네이버 상품ID를 NocoDB에 동기화 -> 판매가/재고 최신화'를
한 번에 순서대로 실행하는 오케스트레이터.

내부적으로 main.py / sync_naver_ids_to_nocodb.py / update_price_stock.py를
그대로 순서대로 호출한다 (각 스크립트를 따로 수정하지 않고 그대로 재사용).

사용법:
    python3 run_pipeline.py                  # 전체 파이프라인 실행
    python3 run_pipeline.py --dry-run         # 등록/가격단계를 dry-run으로만 확인 (동기화는 건너뜀)
    python3 run_pipeline.py --limit 3         # main.py 등록 단계에만 --limit 전달 (소량 테스트)
    python3 run_pipeline.py --skip-register   # 등록은 건너뛰고 동기화+가격/재고만 실행
    python3 run_pipeline.py --skip-price      # 가격/재고 갱신은 건너뛰고 등록+동기화만 실행

각 단계는 순서대로 실행되며, 한 단계가 실패해도(returncode != 0) 다음 단계를 계속 진행한다
(예: 등록 단계에서 일부 상품만 실패해도 나머지 등록된 상품의 ID 동기화/가격갱신은 의미가 있으므로).
"""
import argparse
import subprocess
import sys


def run_step(title: str, cmd: list) -> int:
    print(f"\n{'=' * 60}\n[{title}] {' '.join(cmd)}\n{'=' * 60}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[경고] '{title}' 단계가 0이 아닌 종료코드({result.returncode})를 반환했습니다. 위 로그를 확인하세요.")
    return result.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="등록/가격 단계를 dry-run으로 실행 (동기화 단계는 자동 생략)")
    parser.add_argument("--limit", type=int, default=None, help="등록 단계(main.py)에만 전달할 --limit")
    parser.add_argument("--skip-register", action="store_true", help="1단계(상품 등록) 건너뛰기")
    parser.add_argument("--skip-sync", action="store_true", help="2단계(NocoDB ID 동기화) 건너뛰기")
    parser.add_argument("--skip-price", action="store_true", help="3단계(가격/재고 갱신) 건너뛰기")
    args = parser.parse_args()

    py = sys.executable

    if not args.skip_register:
        cmd = [py, "main.py"]
        if args.dry_run:
            cmd.append("--dry-run")
        if args.limit is not None:
            cmd += ["--limit", str(args.limit)]
        run_step("1/3 상품 등록 (main.py)", cmd)
    else:
        print("\n[건너뜀] 1단계 상품 등록")

    if args.dry_run:
        print("\n[건너뜀] dry-run 모드에서는 2단계(NocoDB ID 동기화)를 실행하지 않습니다 (실제 등록 결과가 없으므로).")
    elif not args.skip_sync:
        run_step("2/3 네이버 상품ID -> NocoDB 동기화 (sync_naver_ids_to_nocodb.py)", [py, "sync_naver_ids_to_nocodb.py"])
    else:
        print("\n[건너뜀] 2단계 NocoDB ID 동기화")

    if not args.skip_price:
        cmd = [py, "update_price_stock.py"]
        if args.dry_run:
            cmd.append("--dry-run")
        run_step("3/3 판매가/재고 갱신 (update_price_stock.py)", cmd)
    else:
        print("\n[건너뜀] 3단계 판매가/재고 갱신")

    print("\n파이프라인 완료.")


if __name__ == "__main__":
    main()
