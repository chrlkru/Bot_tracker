import PyInstaller.__main__
import os
import shutil

print("🏗 Building Telegram Bot EXE...")

# Очистка предыдущих сборок
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        shutil.rmtree(folder)

# Удаляем старые .spec файлы
for spec_file in ['TelegramSupportBot.spec', 'bot.spec']:
    if os.path.exists(spec_file):
        os.remove(spec_file)

print("📦 Building EXE file...")

# Аргументы для PyInstaller
args = [
    'bot.py',
    '--onefile',
    '--console',
    '--name=TelegramSupportBot',
    '--add-data=handlers;handlers',
    '--hidden-import=aiogram',
    '--hidden-import=aiogram.fsm',
    '--hidden-import=aiogram.fsm.state',
    '--hidden-import=aiogram.fsm.storage',
    '--hidden-import=aiogram.filters',
    '--hidden-import=aiohttp',
    '--hidden-import=aiohttp.client',
    '--hidden-import=email',
    '--hidden-import=email.mime',
    '--hidden-import=imaplib',
    '--hidden-import=config',
    '--hidden-import=states',
    '--hidden-import=email_listener',
    '--hidden-import=polling',
]

try:
    PyInstaller.__main__.run(args)
    print("✅ EXE created successfully!")

    # Копируем ваш готовый config.txt
    shutil.copy2('config.txt', 'dist/')
    print("✅ Your config.txt copied to dist folder")

    # Показываем результат
    print("\n📁 Files in dist folder:")
    for file in os.listdir('dist'):
        file_path = os.path.join('dist', file)
        size = os.path.getsize(file_path)
        print(f"   📄 {file} ({size:,} bytes)")

    print("\n🎉 Build completed!")
    print("📋 Ready to send: TelegramSupportBot.exe + config.txt")

except Exception as e:
    print(f"❌ Error: {e}")

print("\nPress Enter to exit...")
input()