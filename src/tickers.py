# Convert user input like 'aapl' or '700' into a Futu code like 'US.AAPL' or 'HK.00700'
def normalize_ticker(raw: str) -> str:
    s = raw.strip().upper()

    if "." in s:
        market, code = s.split(".", 1)
    elif s.isdigit():
        market, code = "HK", s
    else:
        market, code = "US", s

    if code.isascii():
        if market == "HK" and code.isdigit() and len(code) <= 5:
            return f"HK.{code.zfill(5)}"
        if market == "US" and code.isalpha() and len(code) <= 5:
            return f"US.{code}"

    raise ValueError(f"Unrecognised ticker: {raw!r}")