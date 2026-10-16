import random
from models import Quote
from dataclasses import dataclass

STARTING_PRICES = {
    "US.AAPL": 190.00,
    "US.TSLA": 250.00,
    "US.MSFT": 420.00,
    "US.NVDA": 120.00,
    "HK.00700": 380.00,
    "HK.09988": 80.00,
}


class MockProvider:
    def __init__(self, prices=None, step=0.01, seed=None):
        self._prev_close = dict(prices or STARTING_PRICES)
        self._last = dict(self._prev_close)
        self._step = step
        self._rng = random.Random(seed)

    def snapshot(self, codes):
        unknown = [c for c in codes if c not in self._last]
        if unknown:
            raise ValueError(f"Unknown ticker(s): {unknown}")
        quotes = {}
        for code in codes:
            move = self._rng.uniform(-self._step, self._step)
            self._last[code] = max(0.01, self._last[code] * (1 + move))
            quotes[code] = Quote(code, round(self._last[code], 2), self._prev_close[code])
        return quotes