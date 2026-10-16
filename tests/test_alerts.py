import pytest
from alerts import is_triggered, triggered
from models import Alert, Quote


def tsla(price):
    return Quote("US.TSLA", price, 245.0)

@pytest.mark.parametrize("price, expected", [
    (251.0, True),
    (250.0, True),
    (249.99, False),
])
def test_above(price, expected):
    alert = Alert(1, 42, "US.TSLA", "above", 250.0, 0)
    assert is_triggered(alert, tsla(price)) is expected

@pytest.mark.parametrize("price, expected", [
    (239.0, True),
    (240.0, True),
    (241.0, False),
])
def test_below(price, expected):
    alert = Alert(2, 42, "US.TSLA", "below", 240.0, 0)
    assert is_triggered(alert, tsla(price)) is expected

def test_unknown_direction_raises():
    alert = Alert(3, 42, "US.TSLA", "sideways", 240.0, 0)
    with pytest.raises(ValueError):
        is_triggered(alert, tsla(240.0))

def test_ignores_prev_close():
    alert = Alert(1, 42, "US.TSLA", "above", 250.0, 0)
    assert is_triggered(alert, Quote("US.TSLA", 249.0, 300.0)) is False

def test_triggered_example():
    a1 = Alert(1, 42, "US.TSLA", "above", 250.0, 0)
    a2 = Alert(2, 42, "US.AAPL", "above", 200.0, 0)
    a3 = Alert(3, 42, "US.TSLA", "below", 260.0, 0)
    a4 = Alert(4, 42, "US.MSFT", "above", 400.0, 0)
    quotes = {
        "US.TSLA": Quote("US.TSLA", 251.0, 245.0),
        "US.AAPL": Quote("US.AAPL", 190.0, 186.0),
    }
    assert triggered([a1, a2, a3, a4], quotes) == [a1, a3]

def test_triggered_keeps_input_order():
    a1 = Alert(1, 42, "US.TSLA", "above", 250.0, 0)
    a3 = Alert(3, 42, "US.TSLA", "below", 260.0, 0)
    quotes = {"US.TSLA": Quote("US.TSLA", 251.0, 245.0)}
    assert triggered([a3, a1], quotes) == [a3, a1]

def test_triggered_missing_quote_is_skipped():
    alert = Alert(4, 42, "US.MSFT", "above", 400.0, 0)
    assert triggered([alert], {}) == []

def test_triggered_no_alerts():
    assert triggered([], {"US.TSLA": tsla(251.0)}) == []

def test_triggered_none_hit():
    alert = Alert(1, 42, "US.TSLA", "above", 250.0, 0)
    assert triggered([alert], {"US.TSLA": tsla(200.0)}) == []