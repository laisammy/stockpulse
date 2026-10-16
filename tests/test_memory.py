from models import Holding, Alert
from storage.memory import MemoryStore

def test_add_new_returns_true():
    s = MemoryStore()
    assert s.add_watch(1, "US.AAPL") is True
    assert s.get_watch(1) == ["US.AAPL"]

def test_add_duplicate_returns_false():
    s = MemoryStore()
    s.add_watch(1, "US.AAPL")
    assert s.add_watch(1, "US.AAPL") is False
    assert s.get_watch(1) == ["US.AAPL"]

def test_remove_existing_returns_true():
    s = MemoryStore()
    s.add_watch(1, "US.AAPL")
    assert s.remove_watch(1, "US.AAPL") is True
    assert s.get_watch(1) == []

def test_remove_missing_returns_false():
    s = MemoryStore()
    assert s.remove_watch(1, "US.AAPL") is False

def test_get_unknown_user_is_empty():
    assert MemoryStore().get_watch(99) == []

def test_get_is_sorted():
    s = MemoryStore()
    s.add_watch(1, "US.TSLA")
    s.add_watch(1, "HK.00700")
    s.add_watch(1, "US.AAPL")
    assert s.get_watch(1) == ["HK.00700", "US.AAPL", "US.TSLA"]

def test_users_are_separate():
    s = MemoryStore()
    s.add_watch(1, "US.AAPL")
    assert s.get_watch(2) == []

def test_get_returns_a_copy():
    s = MemoryStore()
    s.add_watch(1, "US.AAPL")
    s.get_watch(1).append("US.HACK")
    assert s.get_watch(1) == ["US.AAPL"]

def test_stores_do_not_share_state():
    a, b = MemoryStore(), MemoryStore()
    a.add_watch(1, "US.AAPL")
    assert b.get_watch(1) == []

def test_get_holding_unknown_user_is_none():
    assert MemoryStore().get_holding(99, "US.AAPL") is None

def test_get_holding_unknown_code_is_none():
    s = MemoryStore()
    s.save_holding(1, Holding("US.AAPL", 10, 100.0))
    assert s.get_holding(1, "US.TSLA") is None

def test_save_then_get_holding():
    s = MemoryStore()
    s.save_holding(1, Holding("US.AAPL", 10, 100.0))
    assert s.get_holding(1, "US.AAPL") == Holding("US.AAPL", 10, 100.0)

def test_save_replaces_existing_holding():
    s = MemoryStore()
    s.save_holding(1, Holding("US.AAPL", 10, 100.0))
    s.save_holding(1, Holding("US.AAPL", 20, 110.0))
    assert s.get_holding(1, "US.AAPL") == Holding("US.AAPL", 20, 110.0)
    assert len(s.get_holdings(1)) == 1

def test_remove_holding_existing_returns_true():
    s = MemoryStore()
    s.save_holding(1, Holding("US.AAPL", 10, 100.0))
    assert s.remove_holding(1, "US.AAPL") is True
    assert s.get_holding(1, "US.AAPL") is None

def test_remove_holding_twice_returns_false():
    s = MemoryStore()
    s.save_holding(1, Holding("US.AAPL", 10, 100.0))
    s.remove_holding(1, "US.AAPL")
    assert s.remove_holding(1, "US.AAPL") is False

def test_remove_holding_unknown_user_returns_false():
    assert MemoryStore().remove_holding(99, "US.AAPL") is False

def test_get_holdings_unknown_user_is_empty():
    assert MemoryStore().get_holdings(99) == []

def test_get_holdings_is_sorted_by_code():
    s = MemoryStore()
    s.save_holding(1, Holding("US.TSLA", 5, 250.0))
    s.save_holding(1, Holding("HK.00700", 100, 400.0))
    s.save_holding(1, Holding("US.AAPL", 10, 100.0))
    assert [h.code for h in s.get_holdings(1)] == ["HK.00700", "US.AAPL", "US.TSLA"]

def test_holdings_users_are_separate():
    s = MemoryStore()
    s.save_holding(1, Holding("US.AAPL", 10, 100.0))
    assert s.get_holdings(2) == []

def test_holdings_and_watchlist_are_separate():
    s = MemoryStore()
    s.save_holding(1, Holding("US.AAPL", 10, 100.0))
    s.add_watch(1, "US.TSLA")
    assert s.get_watch(1) == ["US.TSLA"]
    assert [h.code for h in s.get_holdings(1)] == ["US.AAPL"]

def test_add_alert_returns_alert_with_first_id():
    s = MemoryStore()
    assert s.add_alert(1, "US.TSLA", "above", 250.0, 555) == \
        Alert(1, 1, "US.TSLA", "above", 250.0, 555)

def test_alert_ids_count_up_across_users():
    s = MemoryStore()
    a = s.add_alert(1, "US.TSLA", "above", 250.0, 555)
    b = s.add_alert(2, "US.AAPL", "below", 180.0, 777)
    c = s.add_alert(1, "HK.00700", "above", 400.0, 555)
    assert [a.alert_id, b.alert_id, c.alert_id] == [1, 2, 3]

def test_alert_ids_are_never_reused():
    s = MemoryStore()
    s.add_alert(1, "US.TSLA", "above", 250.0, 555)
    s.add_alert(2, "US.AAPL", "below", 180.0, 777)
    s.add_alert(1, "HK.00700", "above", 400.0, 555)
    s.remove_alert(2, 2)
    assert s.add_alert(2, "US.TSLA", "below", 200.0, 777).alert_id == 4

def test_get_alerts_only_returns_that_user_in_id_order():
    s = MemoryStore()
    s.add_alert(1, "US.TSLA", "above", 250.0, 555)
    s.add_alert(2, "US.AAPL", "below", 180.0, 777)
    s.add_alert(1, "HK.00700", "above", 400.0, 555)
    assert [a.alert_id for a in s.get_alerts(1)] == [1, 3]
    assert [a.alert_id for a in s.get_alerts(2)] == [2]

def test_get_alerts_unknown_user_is_empty():
    assert MemoryStore().get_alerts(99) == []

def test_remove_own_alert():
    s = MemoryStore()
    s.add_alert(1, "US.TSLA", "above", 250.0, 555)
    assert s.remove_alert(1, 1) is True
    assert s.get_alerts(1) == []

def test_cannot_remove_another_users_alert():
    s = MemoryStore()
    s.add_alert(2, "US.AAPL", "below", 180.0, 777)
    assert s.remove_alert(1, 1) is False
    assert [a.alert_id for a in s.get_all_alerts()] == [1]

def test_remove_alert_twice_returns_false():
    s = MemoryStore()
    s.add_alert(1, "US.TSLA", "above", 250.0, 555)
    s.remove_alert(1, 1)
    assert s.remove_alert(1, 1) is False

def test_remove_unknown_alert_id_returns_false():
    assert MemoryStore().remove_alert(1, 42) is False

def test_get_all_alerts_every_user_in_id_order():
    s = MemoryStore()
    s.add_alert(1, "US.TSLA", "above", 250.0, 555)
    s.add_alert(2, "US.AAPL", "below", 180.0, 777)
    s.add_alert(1, "HK.00700", "above", 400.0, 555)
    s.remove_alert(2, 2)
    s.add_alert(2, "US.TSLA", "below", 200.0, 777)
    assert [a.alert_id for a in s.get_all_alerts()] == [1, 3, 4]

def test_get_all_alerts_empty_store():
    assert MemoryStore().get_all_alerts() == []

def test_get_all_alerts_returns_a_copy():
    s = MemoryStore()
    s.add_alert(1, "US.TSLA", "above", 250.0, 555)
    s.get_all_alerts().clear()
    assert len(s.get_all_alerts()) == 1

def test_alert_counters_are_per_store():
    a, b = MemoryStore(), MemoryStore()
    a.add_alert(1, "US.TSLA", "above", 250.0, 555)
    a.add_alert(1, "US.TSLA", "above", 260.0, 555)
    assert b.add_alert(1, "US.TSLA", "above", 250.0, 555).alert_id == 1

def test_alerts_separate_from_watch_and_holdings():
    s = MemoryStore()
    s.add_alert(1, "US.TSLA", "above", 250.0, 555)
    assert s.get_watch(1) == []
    assert s.get_holdings(1) == []