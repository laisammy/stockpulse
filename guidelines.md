# StockPulse: Discord Stock-Alert Bot (Project Guidelines)

A one-day project for a 2nd-year CS student that combines **AWS**, a **Discord bot**, and **Futubull (Futu OpenAPI)**.

**Pitch:** a Discord bot that gets live stock quotes from Futubull (through Futu OpenAPI), lets users keep watchlists, track the stocks they own to see whether they've risen or dropped, and set price alerts. Everything is saved in AWS DynamoDB, and the bot runs on an AWS server (EC2) all the time.

It works well on a CV because it covers a real-time external API, async Python, a cloud database, deployment, background jobs and testing, and you can demo it live in an interview.

---

## 1. Features (keep it to these)

| Command | What it does |
|---|---|
| `/quote AAPL` | Shows price, daily change %, high/low and volume |
| `/watch add/remove/list` | Manages your personal watchlist; `list` shows a live quote for each stock, marked ▲ (risen) or ▼ (dropped) today |
| `/portfolio add AAPL 10 182.50` | Records a stock you own: ticker, number of shares and the price you paid. Adding more of the same stock updates your average cost |
| `/portfolio remove AAPL` | Removes a stock from your portfolio |
| `/portfolio view` | Shows every stock you own: current price, today's change, and whether it has **risen or dropped since you bought it** (in both % and money), plus your portfolio's total gain/loss |
| `/alert set TSLA above 250` | Creates a price alert for that stock |
| `/alert list` / `/alert remove <id>` | Shows or deletes your alerts |
| Background task | Every 60 seconds, checks all alerts and sends you a direct message when one is hit |

## 2. Tech stack

- **Language:** Python 3.11+
- **Discord:** `discord.py` 2.x, using slash commands (`app_commands`) and `tasks.loop` for the alert checker
- **Futubull:** the `futu-api` Python SDK plus **FutuOpenD**, a gateway program you download from Futu and log in to with your Futubull account
- **AWS:**
  - **DynamoDB** stores watchlists and alerts.
  - **EC2** (a free-tier `t2.micro` or `t3.micro`) runs the bot and OpenD.
  - **SSM Parameter Store** holds your Discord token so it never sits in your code.
  - **IAM role** lets EC2 use DynamoDB and SSM without access keys.
  - Optional: **CloudWatch Logs**.
- **Tooling:** `pytest`, `moto` (fakes AWS in tests), Docker, and a `.env` file for local settings

## 3. Architecture

```
Discord user ──slash cmd──> Discord Bot (EC2, Docker)
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
   FutuOpenD (localhost:11111)  DynamoDB        SSM (bot token)
              │
         Futu servers
```

Put each part behind its own small interface so they're easy to swap:

- `MarketDataProvider` has two versions: a real `FutuProvider` and a `MockProvider` that returns random-walk prices.
- `Store` has two versions: a real `DynamoStore` and an in-memory `MemoryStore`.

**Why this matters:** you can build and test everything offline before Futu or AWS are set up, and you can explain the design choice in interviews.

## 4. Suggested folder layout

```
src/stockpulse/
  bot.py              # slash commands, embeds, alert loop
  config.py           # env vars + SSM token lookup
  models.py           # Quote, Alert, Holding dataclasses
  tickers.py          # "aapl" -> "US.AAPL", "700" -> "HK.00700"
  alerts.py           # pure logic: which alerts are triggered
  portfolio.py        # pure logic: gain/loss per holding and in total
  market/futu_provider.py, mock_provider.py
  storage/dynamo.py, memory.py
tests/
infra/cloudformation.yaml   # (or just create resources in the console)
Dockerfile, README.md, .env.example
```

## 5. One-day plan (about 8 to 10 hours)

### Hour 0–1: Setup

- Create a Discord app at [discord.com/developers](https://discord.com/developers/applications), add a bot, copy its token, and invite it to a test server with the `bot` and `applications.commands` scopes.
- Set up a Python virtual environment and install `discord.py futu-api boto3 python-dotenv`.
- Get a `/ping` slash command working. Sync commands to your test server (guild) so they show up immediately; global sync can take up to an hour.

### Hour 1–2: Futu

- Download FutuOpenD, log in, and check that it's listening on port `11111`.
- Test it with a small script:

```python
from futu import OpenQuoteContext, RET_OK

ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
ret, df = ctx.get_market_snapshot(["US.AAPL", "HK.00700"])
print(df[["code", "name", "last_price", "prev_close_price"]] if ret == RET_OK else df)
ctx.close()
```

- Write a ticker normalizer that turns `aapl` into `US.AAPL` and `700` into `HK.00700`.
- **Watch out:** the futu SDK is blocking. In async code, call it with `await asyncio.to_thread(...)`, or it will freeze the bot.

### Hour 2–4: Bot commands

- Build `/quote`, `/watch`, `/portfolio` and `/alert` first, using the in-memory store.
- Show results as Discord embeds: green when the stock is up, red when it's down. Put ▲ or ▼ next to each change so it's readable without colour.
- For `/portfolio view`, fetch all of the user's tickers in one `get_market_snapshot` call. For each holding, show:
  - **Since bought:** `(last_price - avg_cost) / avg_cost`, and the money gained or lost, `(last_price - avg_cost) * quantity`
  - **Today:** `(last_price - prev_close_price) / prev_close_price`
  - A footer with the total value, total cost and overall gain/loss. Colour the embed by the overall result.
- Keep the gain/loss maths in `portfolio.py` as plain functions (no Discord or Futu code) so it's easy to test.
- Handle errors: unknown ticker, OpenD offline, empty watchlist or portfolio, and a zero or negative quantity or price in `/portfolio add`.
- Note: US and HK stocks are priced in different currencies (USD vs HKD). Either show totals per currency or keep it simple and only total within one market.

### Hour 4–5: DynamoDB

- Use one table named `stockpulse`. The partition key is `PK` and the sort key is `SK`:

| Item | PK | SK | Other attributes |
|---|---|---|---|
| Watchlist entry | `USER#<id>` | `WATCH#US.AAPL` | |
| Holding | `USER#<id>` | `HOLD#US.AAPL` | `quantity`, `avg_cost` |
| Alert | `USER#<id>` | `ALERT#<alertId>` | `ticker`, `direction`, `target`, `channel_id`, `GSI1PK="ALERT"` |

- A user's watchlist, holdings and alerts all share the same `PK`, so a single query with `begins_with(SK, "HOLD#")` loads their whole portfolio.
- Store `quantity` and `avg_cost` as `Decimal`, because DynamoDB doesn't accept Python floats.
- Add a GSI (secondary index) on `GSI1PK` so the alert loop can fetch every alert with one query. This also gives you something to talk about in interviews.
- Use on-demand (`PAY_PER_REQUEST`) billing, which is effectively free at this size.

### Hour 5–6: Alert loop

- Every 60 seconds: load all alerts, find the unique tickers, fetch them all in one `get_market_snapshot` call, then check each alert.
- When an alert triggers, send the user a direct message (or post in the original channel if DMs fail), then delete the alert so it doesn't fire repeatedly.
- Put the "is it triggered?" check in a plain function so it's easy to unit test.

### Hour 6–7: Tests

- Ticker normalizer
- Alert trigger logic, using the mock provider
- Portfolio maths: a rise, a drop, no change, and the average cost after buying the same stock twice
- DynamoDB store, using the `@mock_aws` decorator from `moto` (no real AWS needed)

### Hour 7–9: Deploy to AWS

1. Create the DynamoDB table.
2. Store the token:

   ```bash
   aws ssm put-parameter --name /stockpulse/discord-token --type SecureString --value "<your-token>"
   ```

3. Create an IAM role with access to `dynamodb:*` on your table only and `ssm:GetParameter` on that parameter, and attach it to the EC2 instance.
4. Launch EC2 with Ubuntu, install Docker, and run FutuOpenD on the instance. Login is a one-time phone verification step.
5. Run the bot with `docker run --restart unless-stopped` or a `systemd` service.
6. Security group: allow inbound SSH from your IP only. The bot only makes outbound connections, and OpenD stays on localhost.

### Hour 9–10: README and demo

- Include an architecture diagram, screenshots or a GIF, setup steps, and the design decisions you made.

## 6. Common problems

- **Futu market data permissions:** a free account may only get delayed or limited US quotes. HK quotes are usually easier to access. Mention this in your README.
- **OpenD must be logged in** or every call fails. Catch the error and show users something like "Market data is temporarily unavailable."
- **Never commit your Discord token.** Add `.env` to `.gitignore` and use SSM in production.
- **AWS costs:** set a $1 billing alarm. Stay on a free-tier instance and stop it when you're not using it.
- **Discord intents:** slash commands don't need the privileged Message Content intent, so leave it off.

## 7. CV bullets (adjust to what you actually build)

- Built a Python Discord bot that gives real-time stock quotes, portfolio gain/loss tracking and price alerts using **Futu OpenAPI**, supporting US and HK markets.
- Designed a single-table **AWS DynamoDB** schema with a secondary index (GSI) so all alerts can be scanned in one query.
- Deployed it on **AWS EC2** with Docker. Used an **IAM role** with minimal permissions and **SSM Parameter Store** for secrets, so no credentials are hard-coded.
- Separated market data and storage behind swappable interfaces, which allowed offline development and **pytest/moto** tests with no cloud dependencies.

## 8. Stretch goals (only if you finish early)

- A `/chart AAPL` command that draws a candlestick chart with `matplotlib`, using Futu's `request_history_kline`.
- A daily market summary posted to a channel on a schedule (EventBridge + Lambda).
- GitHub Actions CI that runs the tests on every push.
- Futu's paper-trading API (`OpenSecTradeContext` with `TrdEnv.SIMULATE`) for a `/papertrade` command.
