from futu import OpenQuoteContext, RET_OK

ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
ret, df = ctx.get_market_snapshot(["US.AAPL", "HK.00700"])
print(df[["code", "name", "last_price", "prev_close_price"]] if ret == RET_OK else df)
ctx.close()