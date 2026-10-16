import pytest
from models import Holding, Quote
from portfolio import day_change_pct, gain_amount, gain_pct, merge


def test_up_since_bought_down_today():
    h = Holding("US.AAPL", 10, 100.0)
    q = Quote("US.AAPL", 110.0, 125.0)
    assert gain_pct(h, q) == pytest.approx(10.0)
    assert gain_amount(h, q) == pytest.approx(100.0)
    assert day_change_pct(q) == pytest.approx(-12.0)

def test_down_since_bought_flat_today():
    h = Holding("HK.00700", 100, 400.0)
    q = Quote("HK.00700", 380.0, 380.0)
    assert gain_pct(h, q) == pytest.approx(-5.0)
    assert gain_amount(h, q) == pytest.approx(-2000.0)
    assert day_change_pct(q) == pytest.approx(0.0)

def test_no_change_since_bought():
    h = Holding("US.AAPL", 10, 100.0)
    q = Quote("US.AAPL", 100.0, 100.0)
    assert gain_pct(h, q) == pytest.approx(0.0)
    assert gain_amount(h, q) == pytest.approx(0.0)

def test_merge_same_size_purchases():
    h = merge(Holding("US.AAPL", 10, 100.0), 10, 120.0)
    assert h.code == "US.AAPL"
    assert h.quantity == 20
    assert h.avg_cost == pytest.approx(110.0)

def test_merge_is_weighted_by_quantity():
    h = merge(Holding("US.AAPL", 10, 100.0), 30, 120.0)
    assert h.quantity == 40
    assert h.avg_cost == pytest.approx(115.0)

def test_merge_does_not_change_original():
    original = Holding("US.AAPL", 10, 100.0)
    merge(original, 10, 120.0)
    assert original == Holding("US.AAPL", 10, 100.0)

@pytest.mark.parametrize("quantity, price", [
    (0, 120.0),
    (10, 0),
    (5, -1),
    (-10, 120.0),
])
def test_merge_rejects_non_positive_input(quantity, price):
    with pytest.raises(ValueError):
        merge(Holding("US.AAPL", 10, 100.0), quantity, price)