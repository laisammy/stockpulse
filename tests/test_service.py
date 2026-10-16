import pytest
from fakes import FixedProvider
from service import StockPulse
from storage.memory import MemoryStore

PRICES = {
    "US.AAPL":  (190.00, 186.00),
    "US.TSLA":  (240.00, 250.00),
    "HK.00700": (380.00, 380.00),
}

@pytest.fixture
def pulse():
    return StockPulse(FixedProvider(PRICES), MemoryStore())

def test_quote_up(pulse):
    assert pulse.quote("aapl") == "US.AAPL 190.00 ▲ +2.15%"
def test_quote_down(pulse):
    assert pulse.quote("tsla") == "US.TSLA 240.00 ▼ -4.00%"
def test_quote_unchanged(pulse):
    assert pulse.quote("700") == "HK.00700 380.00 • +0.00%"
def test_quote_unknown_ticker(pulse):
    with pytest.raises(ValueError):
        pulse.quote("msft")
def test_quote_invalid_ticker(pulse):
    with pytest.raises(ValueError):
        pulse.quote("toolong")

def test_watch_add(pulse):
    assert pulse.watch_add(1, "aapl") == "Added US.AAPL to your watchlist."

def test_watch_add_duplicate(pulse):
    pulse.watch_add(1, "aapl")
    assert pulse.watch_add(1, "AAPL") == "US.AAPL is already on your watchlist."

def test_watch_add_unknown(pulse):
    with pytest.raises(ValueError):
        pulse.watch_add(1, "msft")

def test_watch_remove(pulse):
    pulse.watch_add(1, "aapl")
    assert pulse.watch_remove(1, "aapl") == "Removed US.AAPL from your watchlist."
    assert pulse.watch_list(1) == "Your watchlist is empty."

def test_watch_remove_missing(pulse):
    assert pulse.watch_remove(1, "aapl") == "US.AAPL is not on your watchlist."

def test_watch_list_sorted_and_single_call(pulse):
    pulse.watch_add(1, "aapl")
    pulse.watch_add(1, "700")
    pulse.provider.calls = 0
    assert pulse.watch_list(1) == "HK.00700 380.00 • +0.00%\nUS.AAPL 190.00 ▲ +2.15%"
    assert pulse.provider.calls == 1

def test_watch_list_empty_no_provider_call(pulse):
    assert pulse.watch_list(1) == "Your watchlist is empty."
    assert pulse.provider.calls == 0

def test_watchlists_are_per_user(pulse):
    pulse.watch_add(1, "aapl")
    assert pulse.watch_list(2) == "Your watchlist is empty."

PORTFOLIO_PRICES = {
    "US.AAPL":  (110.00, 125.00),
    "HK.00700": (380.00, 380.00),
}

@pytest.fixture
def pf():
    return StockPulse(FixedProvider(PORTFOLIO_PRICES), MemoryStore())

def test_portfolio_add_new(pf):
    assert pf.portfolio_add(1, "aapl", 10, 100.0) == "Added 10 US.AAPL at 100.00."

def test_portfolio_add_again_merges(pf):
    pf.portfolio_add(1, "aapl", 10, 100.0)
    assert pf.portfolio_add(1, "AAPL", 10, 120.0) == \
        "Bought 10 more US.AAPL. You now hold 20 at an average cost of 110.00."

@pytest.mark.parametrize("quantity, price", [(0, 100.0), (-5, 100.0), (10, 0), (10, -1.0)])
def test_portfolio_add_rejects_non_positive(pf, quantity, price):
    assert pf.portfolio_add(1, "aapl", quantity, price) == "Quantity and price must be positive."
    assert pf.portfolio_view(1) == "Your portfolio is empty."

def test_portfolio_add_checks_numbers_before_ticker(pf):
    assert pf.portfolio_add(1, "12345678", -5, 100.0) == "Quantity and price must be positive."

def test_portfolio_add_unknown_ticker(pf):
    with pytest.raises(ValueError):
        pf.portfolio_add(1, "goog", 1, 100.0)

def test_portfolio_remove(pf):
    pf.portfolio_add(1, "700", 100, 400.0)
    assert pf.portfolio_remove(1, "700") == "Removed HK.00700 from your portfolio."
    assert pf.portfolio_view(1) == "Your portfolio is empty."

def test_portfolio_remove_missing(pf):
    assert pf.portfolio_remove(1, "msft") == "US.MSFT is not in your portfolio."

def test_portfolio_view_empty_no_provider_call(pf):
    assert pf.portfolio_view(1) == "Your portfolio is empty."
    assert pf.provider.calls == 0

def test_portfolio_view_both_markets_single_call(pf):
    pf.portfolio_add(1, "aapl", 10, 100.0)
    pf.portfolio_add(1, "700", 100, 400.0)
    pf.provider.calls = 0
    assert pf.portfolio_view(1) == (
        "HK.00700 100 @ 400.00 | now 380.00 ▼ -5.00% (-2000.00) | today • +0.00%\n"
        "US.AAPL 10 @ 100.00 | now 110.00 ▲ +10.00% (+100.00) | today ▼ -12.00%\n"
        "HK total: ▼ -2000.00 (-5.00%)\n"
        "US total: ▲ +100.00 (+10.00%)"
    )
    assert pf.provider.calls == 1

def test_portfolio_view_after_merge_is_flat(pf):
    pf.portfolio_add(1, "aapl", 10, 100.0)
    pf.portfolio_add(1, "aapl", 10, 120.0)
    assert pf.portfolio_view(1) == (
        "US.AAPL 20 @ 110.00 | now 110.00 • +0.00% (+0.00) | today ▼ -12.00%\n"
        "US total: • +0.00 (+0.00%)"
    )

def test_portfolios_are_per_user(pf):
    pf.portfolio_add(1, "aapl", 10, 100.0)
    assert pf.portfolio_view(2) == "Your portfolio is empty."