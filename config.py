import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN   = os.getenv("BOT_TOKEN")
YT_TOKEN    = os.getenv("YT_TOKEN")
YT_ORG_ID   = os.getenv("YT_ORG_ID")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 60))  # секундах


SMTP_HOST     = os.getenv("SMTP_HOST")
SMTP_PORT     = int(os.getenv("SMTP_PORT"))
SMTP_USER     = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ADMIN_EMAIL   = os.getenv("ADMIN_EMAIL")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
