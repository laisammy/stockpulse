def is_triggered(alert, quote):
    if alert.direction == "above":
        return quote.last_price >= alert.target
    if alert.direction == "below":
        return quote.last_price <= alert.target
    raise ValueError(f"Unknown direction: {alert.direction}")

def triggered(alerts, quotes):
    result = []
    for alert in alerts:
        if alert.code in quotes and is_triggered(alert, quotes[alert.code]):
            result.append(alert)
    return result