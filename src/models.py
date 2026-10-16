from dataclasses import dataclass

@dataclass
class Quote:
    code: str
    last_price: float
    prev_close_price: float

@dataclass
class Holding:
    code: str
    quantity: float
    avg_cost: float

@dataclass
class Alert:
    alert_id: int
    user_id: int
    code: str
    direction: str
    target: float
    channel_id: int