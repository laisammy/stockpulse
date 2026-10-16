from models import Holding

def gain_pct(holding, quote):
    return ((quote.last_price - holding.avg_cost) / holding.avg_cost) * 100

def gain_amount(holding, quote):
    return (quote.last_price - holding.avg_cost) * holding.quantity

def day_change_pct(quote):
    return ((quote.last_price - quote.prev_close_price) / quote.prev_close_price) * 100

def merge(holding, quantity, price):
    if quantity <= 0 or price <= 0:
        raise ValueError("Quantity and price must be positive")
    return Holding(holding.code, holding.quantity + quantity, (holding.avg_cost * holding.quantity + price * quantity) / (holding.quantity + quantity))