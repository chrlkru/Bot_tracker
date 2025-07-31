import os
from dotenv import load_dotenv

load_dotenv()  # загружает .env :contentReference[oaicite:3]{index=3}

BOT_TOKEN   = os.getenv("BOT_TOKEN")
YT_TOKEN    = os.getenv("YT_TOKEN")
YT_ORG_ID   = os.getenv("YT_ORG_ID")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))  # секундах
