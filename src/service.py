import tickers
from models import Holding, Alert
import portfolio
import alerts

class StockPulse:
    def __init__(self, provider, store):
        self.provider = provider
        self.store = store

    def _format_quote(self, q):
        percentage_change = ((q.last_price - q.prev_close_price) / q.prev_close_price) * 100
        if percentage_change > 0:
            arrow = "▲"
        elif percentage_change < 0:
            arrow = "▼"
        else:
            arrow = "•"
        return f"{q.code} {q.last_price:.2f} {arrow} {percentage_change:+.2f}%"

    def _arrow(self, value):
        if value > 0:
            return "▲"
        if value < 0:
            return "▼"
        return "•"

    def quote(self, raw_ticker):
        code = tickers.normalize_ticker(raw_ticker)
        quotes = self.provider.snapshot([code])  # raises ValueError if unknown
        return self._format_quote(quotes[code])

    def watch_add(self, user_id, raw_ticker):
        code = tickers.normalize_ticker(raw_ticker)
        self.provider.snapshot([code])  # raises ValueError if unknown
        status = self.store.add_watch(user_id, code)
        if status:
            return f"Added {code} to your watchlist."
        return f"{code} is already on your watchlist."

    def watch_remove(self, user_id, raw_ticker):
        code = tickers.normalize_ticker(raw_ticker)
        status = self.store.remove_watch(user_id, code)
        if status:
            return f"Removed {code} from your watchlist."
        return f"{code} is not on your watchlist."

    def watch_list(self, user_id):
        codes = self.store.get_watch(user_id)
        if not codes:
            return "Your watchlist is empty."
        quotes = self.provider.snapshot(codes)
        lines = []
        for code in codes:
            lines.append(self._format_quote(quotes[code]))
        return "\n".join(lines)

    def portfolio_add(self, user_id, raw_ticker, quantity, price) -> str:
        if quantity <= 0 or price <= 0:
            return "Quantity and price must be positive."
        code = tickers.normalize_ticker(raw_ticker)
        self.provider.snapshot([code])
        existing = self.store.get_holding(user_id, code)
        if existing is None:
            self.store.save_holding(user_id, Holding(code, quantity, price))
            return f"Added {quantity} {code} at {price:.2f}."
        else:
            new = portfolio.merge(existing, quantity, price)
            self.store.save_holding(user_id, new)
            return f"Bought {quantity} more {code}. You now hold {new.quantity} at an average cost of {new.avg_cost:.2f}."

    def portfolio_remove(self, user_id, raw_ticker) -> str:
        code = tickers.normalize_ticker(raw_ticker)
        status = self.store.remove_holding(user_id, code)
        if status:
            return f"Removed {code} from your portfolio."
        return f"{code} is not in your portfolio."

    def portfolio_view(self, user_id) -> str:
        holdings = self.store.get_holdings(user_id)
        if not holdings:
            return "Your portfolio is empty."
        quotes = self.provider.snapshot([h.code for h in holdings])
        lines = []
        cost = {}
        gain = {}
        for holding in holdings:
            q = quotes[holding.code]
            market = holding.code.split(".")[0]
            if market not in cost:
                cost[market] = 0
                gain[market] = 0
            pct = portfolio.gain_pct(holding, q)
            amount = portfolio.gain_amount(holding, q)
            cost[market] += holding.quantity * holding.avg_cost
            gain[market] += amount
            day = portfolio.day_change_pct(q)
            lines.append(f"{holding.code} {holding.quantity} @ {holding.avg_cost:.2f} | now {q.last_price:.2f} {self._arrow(pct)} {pct:+.2f}% ({amount:+.2f}) | today {self._arrow(day)} {day:+.2f}%")
        for market in sorted(cost):
            total_pct = gain[market] / cost[market] * 100
            lines.append(f"{market} total: {self._arrow(gain[market])} {gain[market]:+.2f} ({total_pct:+.2f}%)")
        return "\n".join(lines)

    def alert_set(self, user_id, raw_ticker, direction, target, channel_id) -> str:
        if (direction != "above" and direction != "below"):
            return "Direction must be above or below."
        if target <= 0:
            return "Target price must be positive."
        code = tickers.normalize_ticker(raw_ticker)
        self.provider.snapshot([code])
        alert = self.store.add_alert(user_id, code, direction, target, channel_id)
        return f"Alert #{alert.alert_id} set: {code} {direction} {target:.2f}"
    
    def alert_list(self, user_id) -> str:
        _alerts = self.store.get_alerts(user_id)
        if _alerts == []:
            return "You have no alerts."
        lines = []
        for alert in _alerts:
            lines.append(f"#{alert.alert_id} {alert.code} {alert.direction} {alert.target:.2f}")
        return "\n".join(lines)
    
    def check_alerts(self) -> list[tuple[Alert, str]]:
        _alerts = self.store.get_all_alerts()
        if _alerts == []:
            return []
        uniqueCodes = sorted({a.code for a in _alerts})
        quotes = self.provider.snapshot(uniqueCodes)

        results = []
        for alert in alerts.triggered(_alerts, quotes):
            self.store.remove_alert(alert.user_id, alert.alert_id)
            price = quotes[alert.code].last_price
            msg = (f"Alert #{alert.alert_id}: {alert.code} is now {price:.2f} "
                f"({alert.direction} your target of {alert.target:.2f})")
            results.append((alert, msg))
        return results

    def alert_remove(self, user_id, alert_id) -> str:
        if self.store.remove_alert(user_id, alert_id):
            return f"Removed alert #{alert_id}."
        return f"Alert #{alert_id} not found."

        