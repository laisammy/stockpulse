# StockPulse

A Discord bot for stock quotes, watchlists, portfolio gain and loss, and price alerts. It supports US and HK tickers through [Futu OpenAPI](https://openapi.futunn.com/futu-api-doc/en/). Data is kept in memory by default, or in DynamoDB when you set `STORE=dynamo`.

## Commands

| Command | What it does |
|---|---|
| `/ping` | Checks the bot is online. |
| `/quote AAPL` | Price and today's change. `700` is read as `HK.00700`. |
| `/watch add` / `remove` / `list` | Your watchlist, with a live quote on `list`. |
| `/portfolio add AAPL 10 182.50` | Record shares and the price you paid. |
| `/portfolio remove AAPL` | Remove a holding. |
| `/portfolio view` | Gain or loss since you bought, today's move, and a total per market. |
| `/alert set TSLA above 250` | DM when the price crosses the target. `below` works too. |
| `/alert list` / `/alert remove 3` | Show or delete alerts. |

Every 60 seconds the bot checks alerts. A hit is sent as a DM, then the alert is deleted.

## How it works

`bot.py` handles slash commands and the alert loop. `service.py` talks to a price provider and a store. `MockProvider` and `MemoryStore` are the defaults, so it runs with no Futu login and no AWS account. Set `PROVIDER=futu` for live quotes from FutuOpenD on `127.0.0.1:11111`, and `STORE=dynamo` to save data in DynamoDB.

`aapl` becomes `US.AAPL`. `700` becomes `HK.00700`.

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate
pip install discord.py python-dotenv boto3 futu-api pytest moto
```

Create a `.env` file:

```
TOKEN=your-discord-bot-token
STORE=memory
PROVIDER=mock
```

If `TOKEN` is missing, the bot reads `/stockpulse/discord-token` from SSM Parameter Store. `TABLE_NAME` defaults to `stockpulse` and `AWS_REGION` to `eu-west-2`.

```bash
cd src
python bot.py
```

Or with Docker, from the project root:

```bash
docker build -t stockpulse .
docker run --env-file .env -e STORE=memory -e PROVIDER=mock stockpulse
```

On EC2, add `--network host` and set `STORE=dynamo` and `PROVIDER=futu`. Leave `TOKEN` unset so the bot reads it from SSM. FutuOpenD stays on the host.

From the project root:

```bash
pytest
```
