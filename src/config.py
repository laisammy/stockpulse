import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
STORE = os.getenv("STORE", "memory").lower()
TABLE_NAME = os.getenv("TABLE_NAME", "stockpulse")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
PROVIDER = os.getenv("PROVIDER", "mock").lower()

if not TOKEN:
    import boto3
    ssm = boto3.client("ssm", region_name=AWS_REGION)
    TOKEN = ssm.get_parameter(
        Name="/stockpulse/discord-token",
        WithDecryption=True,
    )["Parameter"]["Value"]
