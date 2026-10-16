from models import Holding
from models import Alert


class MemoryStore:
    def __init__(self) -> None:
        self._watch: dict[int, set[str]] = {}
        self._holdings: dict[int, dict[str, Holding]] = {}
        self._alerts: dict[int, Alert] = {}
        self._next_alert_id: int = 1

    def add_watch(self, user_id: int, code: str) -> bool:
        if user_id not in self._watch:
            self._watch[user_id] = set()
        codes = self._watch[user_id]
        if code in codes:
            return False
        else:
            codes.add(code)
            return True

    def remove_watch(self, user_id: int, code: str) -> bool:
        if user_id not in self._watch:
            return False
        codes = self._watch[user_id]
        if code not in codes:
            return False
        codes.remove(code)
        return True

    def get_watch(self, user_id: int) -> list[str]:
        return sorted(self._watch.get(user_id, ()))

    def get_holding(self, user_id: int, code: str) -> Holding | None:
        holdings = self._holdings.get(user_id, {})
        return holdings.get(code) # Return the holding for the user and code if it exists

    def save_holding(self, user_id: int, holding: Holding) -> None:
        if user_id not in self._holdings:
            self._holdings[user_id] = {} # Creates a new dictionary for the user if it doesn't exist
        self._holdings[user_id][holding.code] = holding 

    def remove_holding(self, user_id: int, code: str) -> bool:
        if user_id not in self._holdings:
            return False
        holdings = self._holdings[user_id]
        if code not in holdings:
            return False
        del holdings[code]
        return True

    def get_holdings(self, user_id: int) -> list[Holding]:
        holdings = self._holdings.get(user_id, {})
        result = []
        for code in sorted(holdings):
            result.append(holdings[code])
        return result # Returns the list of holdings

    def add_alert(self, user_id: int, code: str, direction: str, target: float, channel_id: int):
        alert_id = self._next_alert_id
        self._next_alert_id += 1
        alert = Alert(alert_id, user_id, code, direction, target, channel_id)
        self._alerts[alert_id] = alert
        return alert

    def get_alerts(self, user_id: int) -> list[Alert]:
        alerts = []
        for alert in self._alerts.values():
            if alert.user_id == user_id:
                alerts.append(alert)
        return alerts

    def remove_alert(self, user_id: int, alert_id: int):
        if alert_id not in self._alerts:
            return False
        if self._alerts[alert_id].user_id != user_id:
            return False
        del self._alerts[alert_id]
        return True

    def get_all_alerts(self) -> list[Alert]:
        return list(self._alerts.values())