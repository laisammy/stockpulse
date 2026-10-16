import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise RuntimeError("TOKEN is not set. Add TOKEN=your-bot-token to the .env file.")
