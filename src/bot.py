# slash commands, embeds, alert loop
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.app_commands import Choice

from config import TOKEN

from market.mock_provider import MockProvider
from service import StockPulse
from storage.memory import MemoryStore

pulse = StockPulse(MockProvider(), MemoryStore())

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.tree.command(name="ping", description="Test the bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! ({round(bot.latency * 1000)} ms)")

@bot.tree.command(name="quote", description="Get a stock quote")
@app_commands.describe(ticker="e.g. AAPL or 700")
async def quote(interaction: discord.Interaction, ticker: str):
    try:
        msg = pulse.quote(ticker)
    except ValueError:
        msg = f"Unknown ticker: {ticker}"
    await interaction.response.send_message(msg)

watch = app_commands.Group(name="watch", description="Manage your watchlist")

@watch.command(name="add", description="Add a stock to your watchlist")
@app_commands.describe(ticker="e.g. AAPL or 700")
async def watch_add(interaction: discord.Interaction, ticker: str):
    try:
        msg = pulse.watch_add(interaction.user.id, ticker)
    except ValueError:
        msg = f"Unknown ticker: {ticker}"
    await interaction.response.send_message(msg)

@watch.command(name="remove", description="Remove a stock from your watchlist")
@app_commands.describe(ticker="e.g. AAPL or 700")
async def watch_remove(interaction: discord.Interaction, ticker: str):
    try:
        msg = pulse.watch_remove(interaction.user.id, ticker)
    except ValueError:
        msg = f"Unknown ticker: {ticker}"
    await interaction.response.send_message(msg)

@watch.command(name="list", description="Shows your watchlist")
async def watch_list(interaction: discord.Interaction):
    msg = pulse.watch_list(interaction.user.id)
    await interaction.response.send_message(msg)

bot.tree.add_command(watch)

portfolio = app_commands.Group(name="portfolio", description="Track the stocks you own")


@portfolio.command(name="add", description="Record a stock you own")
@app_commands.describe(
    ticker="e.g. AAPL or 700",
    quantity="Number of shares",
    price="Price paid per share",
)
async def portfolio_add(interaction: discord.Interaction, ticker: str, quantity: int, price: float):
    try:
        msg = pulse.portfolio_add(interaction.user.id, ticker, quantity, price)
    except ValueError:
        msg = f"Unknown ticker: {ticker}"
    await interaction.response.send_message(msg)


@portfolio.command(name="remove", description="Remove a stock from your portfolio")
@app_commands.describe(ticker="e.g. AAPL or 700")
async def portfolio_remove(interaction: discord.Interaction, ticker: str):
    try:
        msg = pulse.portfolio_remove(interaction.user.id, ticker)
    except ValueError:
        msg = f"Unknown ticker: {ticker}"
    await interaction.response.send_message(msg)


@portfolio.command(name="view", description="Show your portfolio with gains and losses")
async def portfolio_view(interaction: discord.Interaction):
    msg = pulse.portfolio_view(interaction.user.id)
    await interaction.response.send_message(msg)

bot.tree.add_command(portfolio)

alert = app_commands.Group(name="alert", description="Get notified when a stock hits your target price.")

@alert.command(name="set", description="Get a DM when a stock crosses a price")
@app_commands.describe(
    ticker="e.g. AAPL or 700",
    target="e.g. 250"
    )
@app_commands.choices(direction=[
    Choice(name="above", value="above"),
    Choice(name="below", value="below"),
])
async def alert_set(interaction: discord.Interaction, ticker: str, direction: Choice[str], target: float):
    try:
        msg = pulse.alert_set(interaction.user.id, ticker, direction.value, target, interaction.channel_id)
    except ValueError:
        msg = f"Unknown ticker: {ticker}"
    await interaction.response.send_message(msg)\

@alert.command(name="list", description="Show your alerts")
async def alert_list(interaction: discord.Interaction):
    msg = pulse.alert_list(interaction.user.id)
    await interaction.response.send_message(msg)

@alert.command(name="remove", description="Delete an alert")
@app_commands.describe(alert_id="The number shown in /alert list")
async def alert_remove(interaction: discord.Interaction, alert_id: int):
    msg = pulse.alert_remove(interaction.user.id, alert_id)
    await interaction.response.send_message(msg)

bot.tree.add_command(alert)

@tasks.loop(seconds=60)
async def alert_loop():
    try:
        fired = pulse.check_alerts()
    except ValueError as e:
        print(f"Alert check failed: {e}")
        return
    for a, msg in fired:
        try:
            user = await bot.fetch_user(a.user_id)
            await user.send(msg)
        except discord.HTTPException:
            channel = bot.get_channel(a.channel_id)
            if channel:
                await channel.send(f"<@{a.user_id}> {msg}")

@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    if not alert_loop.is_running():
        alert_loop.start()
    print(f"Logged in as {bot.user} ({len(synced)} slash commands synced)")

bot.run(TOKEN)
