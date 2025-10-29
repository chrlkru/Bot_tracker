import os
import sys
from pathlib import Path

def load_config():
    """Загружает настройки из config.txt рядом с EXE"""
    if getattr(sys, 'frozen', False):
        # Мы в EXE - ищем config.txt рядом с EXE
        config_path = Path(sys.executable).parent / 'config.txt'
    else:
        # Мы в исходном коде - ищем config.txt в папке проекта
        config_path = Path(__file__).parent / 'config.txt'

    config = {}

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Убираем комментарии в конце строки
                if '#' in line:
                    line = line.split('#')[0].strip()

                if line and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    else:
        # Создаем пример config.txt если файла нет
        create_example_config(config_path)
        print(f"⚠️  config.txt not found! Created example file: {config_path}")
        print("📝 Please edit config.txt and restart the bot")
        sys.exit(1)

    return config

def create_example_config(config_path):
    """Создает пример config.txt"""
    example_content = """# Telegram Bot Settings
BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_ID=123456789

# Email Settings (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# IMAP Settings (optional)
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_PORT=993
POLL_EMAIL_INTERVAL=60

# Admin Email
ADMIN_EMAIL=admin@example.com

# How to get BOT_TOKEN:
# 1. Write to @BotFather in Telegram
# 2. Send /newbot command
# 3. Follow instructions
# 4. Copy the token here

# How to get ADMIN_CHAT_ID:
# 1. Start the bot once
# 2. Send any message to the bot
# 3. Check console output - your chat_id will be shown
"""
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(example_content)

# Загружаем настройки
config = load_config()

# === Telegram ===
BOT_TOKEN = config.get('BOT_TOKEN', '')
try:
    ADMIN_CHAT_ID = int(config.get('ADMIN_CHAT_ID', '0'))
except ValueError:
    ADMIN_CHAT_ID = 0

# === SMTP ===
SMTP_HOST = config.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(config.get('SMTP_PORT', '587'))
SMTP_USER = config.get('SMTP_USER', '')
SMTP_PASSWORD = config.get('SMTP_PASSWORD', '')

# === IMAP ===
EMAIL_IMAP_HOST = config.get('EMAIL_IMAP_HOST', 'imap.gmail.com')
EMAIL_IMAP_PORT = int(config.get('EMAIL_IMAP_PORT', '993'))
EMAIL_IMAP_USER = config.get('EMAIL_IMAP_USER', SMTP_USER)
EMAIL_IMAP_PASSWORD = config.get('EMAIL_IMAP_PASSWORD', SMTP_PASSWORD)
POLL_EMAIL_INTERVAL = int(config.get('POLL_EMAIL_INTERVAL', '60'))

# === Admin Email ===
ADMIN_EMAIL = config.get('ADMIN_EMAIL', SMTP_USER)

# Проверка обязательных настроек
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN is required in config.txt")
    print("💡 Get token from @BotFather in Telegram")
    sys.exit(1)

print("✅ Config loaded successfully from config.txt")