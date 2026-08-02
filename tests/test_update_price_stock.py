"""update_price_stock.py의 apply_price_stock() 화이트/블랙 옵션 기준가 전환
로직 테스트. 순수 함수라 네트워크/NocoDB mock 없이 바로 테스트 가능하다."""
from update_price_stock import apply_price_stock, WHITE_LABEL, BLACK_LABEL


def _body(status_type="SALE", option_combinations=None):
  origin = {
      "statusType": status_type,
      "salePrice": 10000,
      "stockQuantity": 5,
      "detailAttribute": {},
  }
  if option_combinations is not None:
    origin["detailAttribute"]["optionInfo"] = {"optionCombinations": option_combinations}
  return {"originProduct": origin}


class TestSinglePriceNoOptions:
  """옵션 없는 단일가 상품 - 균일 갱신."""

  def test_updates_price_and_stock(self):
    body = _body()
    result = apply_price_stock(body, new_price=15000, new_stock=3)
    origin = result["originProduct"]
    assert origin["salePrice"] == 15000
    assert origin["stockQuantity"] == 3

  def test_outofstock_status_normalized_to_sale(self):
    body = _body(status_type="OUTOFSTOCK")
    result = apply_price_stock(body, new_price=15000, new_stock=0)
    assert result["originProduct"]["statusType"] == "SALE"

  def test_missing_origin_product_raises(self):
    import pytest
    with pytest.raises(RuntimeError):
      apply_price_stock({}, 1000, 1)


class TestExistingOptionCombinations:
  """이미 옵션(화이트/블랙 등)이 있는 상품."""

  def test_uniform_update_without_overrides(self):
    combos = [
        {"optionName1": WHITE_LABEL, "stockQuantity": 1, "price": 0},
        {"optionName1": BLACK_LABEL, "stockQuantity": 1, "price": 5000},
    ]
    body = _body(option_combinations=combos)
    result = apply_price_stock(body, new_price=15000, new_stock=7)
    updated = result["originProduct"]["detailAttribute"]["optionInfo"]["optionCombinations"]
    assert updated[0]["stockQuantity"] == 7
    assert updated[1]["stockQuantity"] == 7
    # price(추가금액)는 건드리지 않음
    assert updated[1]["price"] == 5000

  def test_per_color_override_applied(self):
    combos = [
        {"optionName1": WHITE_LABEL, "stockQuantity": 1, "price": 0},
        {"optionName1": BLACK_LABEL, "stockQuantity": 1, "price": 5000},
    ]
    body = _body(option_combinations=combos)
    result = apply_price_stock(
        body, new_price=15000, new_stock=7,
        option_overrides={WHITE_LABEL: (0, 4), BLACK_LABEL: (6000, 2)},
    )
    updated = result["originProduct"]["detailAttribute"]["optionInfo"]["optionCombinations"]
    white = next(c for c in updated if c["optionName1"] == WHITE_LABEL)
    black = next(c for c in updated if c["optionName1"] == BLACK_LABEL)
    assert white["stockQuantity"] == 4 and white["price"] == 0
    assert black["stockQuantity"] == 2 and black["price"] == 6000


class TestNewColorOptionCreation:
  """옵션이 아직 없는 단일가 상품에 화이트/블랙 옵션을 새로 만드는 경우."""

  def test_both_colors_in_stock_creates_option_structure(self):
    body = _body()
    result = apply_price_stock(
        body, new_price=15000, new_stock=5,
        option_overrides={WHITE_LABEL: (0, 3), BLACK_LABEL: (2000, 4)},
    )
    origin = result["originProduct"]
    combos = origin["detailAttribute"]["optionInfo"]["optionCombinations"]
    white = next(c for c in combos if c["optionName1"] == WHITE_LABEL)
    black = next(c for c in combos if c["optionName1"] == BLACK_LABEL)
    assert white["stockQuantity"] == 3 and white["price"] == 0
    assert black["stockQuantity"] == 4 and black["price"] == 2000
    assert origin["salePrice"] == 15000

  def test_white_out_of_stock_rebalances_to_black_as_zero_addon(self):
    """네이버는 옵션 신규 생성 시 0원+재고>0인 옵션이 최소 1개 필요(NoZeroStock).
    화이트가 품절이면 블랙을 0원 기준으로 재계산해야 한다."""
    body = _body()
    result = apply_price_stock(
        body, new_price=15000, new_stock=5,
        option_overrides={WHITE_LABEL: (0, 0), BLACK_LABEL: (2000, 4)},
    )
    origin = result["originProduct"]
    combos = origin["detailAttribute"]["optionInfo"]["optionCombinations"]
    white = next(c for c in combos if c["optionName1"] == WHITE_LABEL)
    black = next(c for c in combos if c["optionName1"] == BLACK_LABEL)
    # salePrice 기준이 블랙 쪽으로 이동(15000+2000), 블랙 추가금액은 0으로 재계산
    assert origin["salePrice"] == 17000
    assert black["price"] == 0
    assert black["stockQuantity"] == 4
    # 화이트 추가금액은 새 기준(블랙) 대비로 재계산 (0 - 2000 = -2000)
    assert white["price"] == -2000
    assert white["stockQuantity"] == 0

  def test_both_colors_out_of_stock_falls_back_to_uniform(self):
    """화이트/블랙 둘 다 품절이면 옵션 신규 생성 자체가 네이버에 거부되므로,
    재고가 생길 때까지 기존처럼 단일가/단일재고로 반영한다."""
    body = _body()
    result = apply_price_stock(
        body, new_price=15000, new_stock=0,
        option_overrides={WHITE_LABEL: (0, 0), BLACK_LABEL: (2000, 0)},
    )
    origin = result["originProduct"]
    assert origin["stockQuantity"] == 0
    # 옵션 구조가 새로 생기지 않아야 함
    assert "optionInfo" not in origin["detailAttribute"]
