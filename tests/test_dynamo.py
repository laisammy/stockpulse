import boto3
import pytest
from moto import mock_aws

from models import Alert, Holding
from storage.dynamo import DynamoStore, create_table

@pytest.fixture
def store():
    with mock_aws():
        table = create_table(boto3.resource("dynamodb", region_name="eu-west-2"))
        yield DynamoStore(table)

def test_add_alert_returns_alert_with_first_id(store):
    assert store.add_alert(1, "US.TSLA", "above", 250.0, 555) == Alert(1, 1, "US.TSLA", "above", 250.0, 555)

def test_alert_ids_count_up_across_users(store):
    a = store.add_alert(1, "US.TSLA", "above", 250.0, 555)
    b = store.add_alert(2, "US.AAPL", "below", 180.0, 777)
    c = store.add_alert(1, "HK.00700", "above", 400.0, 555)
    assert [a.alert_id, b.alert_id, c.alert_id] == [1, 2, 3]

def test_alert_ids_are_never_reused(store):
    store.add_alert(1, "US.TSLA", "above", 250.0, 555)
    store.add_alert(2, "US.AAPL", "below", 180.0, 777)
    store.add_alert(1, "HK.00700", "above", 400.0, 555)
    store.remove_alert(2, 2)
    assert store.add_alert(2, "US.TSLA", "below", 200.0, 777).alert_id == 4

def test_get_alerts_only_returns_that_user_in_id_order(store):
    store.add_alert(1, "US.TSLA", "above", 250.0, 555)
    store.add_alert(2, "US.AAPL", "below", 180.0, 777)
    store.add_alert(1, "HK.00700", "above", 400.0, 555)
    assert [a.alert_id for a in store.get_alerts(1)] == [1, 3]
    assert [a.alert_id for a in store.get_alerts(2)] == [2]

def test_get_alerts_unknown_user_is_empty(store):
    assert store.get_alerts(99) == []

def test_remove_own_alert(store):
    store.add_alert(1, "US.TSLA", "above", 250.0, 555)
    assert store.remove_alert(1, 1) is True
    assert store.get_alerts(1) == []

def test_cannot_remove_another_users_alert(store):
    store.add_alert(2, "US.AAPL", "below", 180.0, 777)
    assert store.remove_alert(1, 1) is False
    assert [a.alert_id for a in store.get_all_alerts()] == [1]

def test_remove_alert_twice_returns_false(store):
    store.add_alert(1, "US.TSLA", "above", 250.0, 555)
    store.remove_alert(1, 1)
    assert store.remove_alert(1, 1) is False

def test_remove_unknown_alert_id_returns_false(store):
    assert store.remove_alert(1, 42) is False

def test_get_all_alerts_every_user_in_id_order(store):
    store.add_alert(1, "US.TSLA", "above", 250.0, 555)
    store.add_alert(2, "US.AAPL", "below", 180.0, 777)
    store.add_alert(1, "HK.00700", "above", 400.0, 555)
    store.remove_alert(2, 2)
    store.add_alert(2, "US.TSLA", "below", 200.0, 777)
    assert [a.alert_id for a in store.get_all_alerts()] == [1, 3, 4]

def test_get_all_alerts_empty_store(store):
    assert store.get_all_alerts() == []

def test_get_all_alerts_returns_a_copy(store):
    store.add_alert(1, "US.TSLA", "above", 250.0, 555)
    store.get_all_alerts().clear()
    assert len(store.get_all_alerts()) == 1

def test_add_watch_twice_returns_false(store):
    assert store.add_watch(1, "US.AAPL") is True
    assert store.add_watch(1, "US.AAPL") is False
    assert store.get_watch(1) == ["US.AAPL"]

def test_holding_round_trip(store):
    store.save_holding(1, Holding("US.AAPL", 10, 182.50))
    assert store.get_holding(1, "US.AAPL") == Holding("US.AAPL", 10, 182.50)

def test_alerts_separate_from_watch_and_holdings(store):
    store.add_alert(1, "US.TSLA", "above", 250.0, 555)
    assert store.get_watch(1) == []
    assert store.get_holdings(1) == []