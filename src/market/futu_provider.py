from futu import OpenQuoteContext, RET_OK
from models import Quote

class FutuProvider:
    def __init__(self, host="127.0.0.1", port=11111):
        self._ctx = OpenQuoteContext(host=host, port=port) # Opens a connection to the Futu API

    def snapshot(self, codes):
        ret, data = self._ctx.get_market_snapshot(list(codes)) # Gets the market snapshot
        if ret != RET_OK:
            raise ConnectionError(data)
        quotes = {
            row.code: Quote(row.code, float(row.last_price), float(row.prev_close_price))
            for row in data.itertuples(index=False)
        } # Converts the data to quotes
        missing = [code for code in codes if code not in quotes] # Finds the missing codes
        if missing:
            raise ValueError(f"Unknown ticker(s): {missing}") # Raises an error if the codes are missing
        return quotes

    def close(self):
        self._ctx.close() # Closes the connection to the Futu API