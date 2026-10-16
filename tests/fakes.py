from models import Quote


class FixedProvider:
    def __init__(self, prices: dict[str, tuple[float, float]]):
        self.prices = prices          # code -> (last, prev_close)
        self.calls = 0

    def snapshot(self, codes: list[str]) -> dict[str, Quote]:
        self.calls += 1
        unknown = [c for c in codes if c not in self.prices]
        if unknown:
            raise ValueError(f"Unknown ticker(s): {unknown}")
        return {c: Quote(c, *self.prices[c]) for c in codes}