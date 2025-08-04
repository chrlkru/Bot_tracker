import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# === Telegram ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

# === SMTP (отправка писем) ===
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# === IMAP (чтение ответов) ===
EMAIL_IMAP_HOST = os.getenv("EMAIL_IMAP_HOST", "imap.gmail.com")
EMAIL_IMAP_PORT = int(os.getenv("EMAIL_IMAP_PORT", "993"))
EMAIL_IMAP_USER = os.getenv("EMAIL_IMAP_USER", SMTP_USER)
EMAIL_IMAP_PASSWORD = os.getenv("EMAIL_IMAP_PASSWORD", SMTP_PASSWORD)
POLL_EMAIL_INTERVAL = int(os.getenv("POLL_EMAIL_INTERVAL", "60"))

# === Куда шлём письма админам ===
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", SMTP_USER)
