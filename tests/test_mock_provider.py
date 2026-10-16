import pytest
from market.mock_provider import STARTING_PRICES, MockProvider
from models import Quote


def test_uses_default_prices_when_none_given():
    p = MockProvider(step=0, seed=1)
    assert p.snapshot(["HK.00700"])["HK.00700"] == Quote("HK.00700", 380.0, 380.0)

def test_knows_every_default_ticker():
    p = MockProvider(seed=1)
    assert set(p.snapshot(list(STARTING_PRICES))) == set(STARTING_PRICES)

def test_returns_models_quote():
    p = MockProvider({"US.X": 100.0}, seed=1)
    assert isinstance(p.snapshot(["US.X"])["US.X"], Quote)

def test_zero_step_never_moves():
    p = MockProvider({"US.X": 50.0}, step=0, seed=1)
    for _ in range(5):
        assert p.snapshot(["US.X"])["US.X"].last_price == 50.0

def test_moves_stay_within_step():
    p = MockProvider({"US.X": 100.0}, step=0.01, seed=7)
    prev = 100.0
    for _ in range(200):
        last = p.snapshot(["US.X"])["US.X"].last_price
        assert prev * 0.99 - 0.01 <= last <= prev * 1.01 + 0.01
        prev = last

def test_prev_close_never_changes():
    p = MockProvider({"US.X": 100.0}, seed=7)
    for _ in range(50):
        assert p.snapshot(["US.X"])["US.X"].prev_close_price == 100.0

def test_price_never_below_floor():
    p = MockProvider({"US.X": 0.02}, step=2.0, seed=3)
    for _ in range(500):
        assert p.snapshot(["US.X"])["US.X"].last_price >= 0.01

def test_same_seed_same_prices_when_interleaved():
    a = MockProvider({"US.X": 100.0, "US.Y": 20.0}, seed=99)
    b = MockProvider({"US.X": 100.0, "US.Y": 20.0}, seed=99)
    for _ in range(50):
        assert a.snapshot(["US.X", "US.Y"]) == b.snapshot(["US.X", "US.Y"])

def test_unknown_ticker_raises():
    p = MockProvider({"US.X": 100.0}, seed=5)
    with pytest.raises(ValueError):
        p.snapshot(["US.NOPE"])

def test_unknown_ticker_changes_nothing():
    a = MockProvider({"US.X": 100.0}, seed=5)
    b = MockProvider({"US.X": 100.0}, seed=5)
    with pytest.raises(ValueError):
        a.snapshot(["US.X", "US.NOPE"])
    assert a.snapshot(["US.X"]) == b.snapshot(["US.X"])

def test_duplicate_code_moves_twice():
    a = MockProvider({"US.X": 100.0}, seed=11)
    b = MockProvider({"US.X": 100.0}, seed=11)
    b.snapshot(["US.X"])
    assert a.snapshot(["US.X", "US.X"]) == b.snapshot(["US.X"])

def test_does_not_modify_callers_dict():
    original = {"US.X": 100.0}
    p = MockProvider(original, seed=2)
    for _ in range(10):
        p.snapshot(["US.X"])
    assert original == {"US.X": 100.0}