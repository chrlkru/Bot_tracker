# bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.support_request import router as support_router
from polling import poll_comments

# Настроим логирование (опционально)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

async def main():
    # 1. Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # 2. Регистрация маршрутов (handlers)
    dp.include_router(support_router)

    # 3. Запуск фонового опроса комментариев
    asyncio.create_task(poll_comments(bot, storage))

    # 4. Уведомляем в консоль о старте
    print("✅ Bot is up and running!")        # простая печать
    logging.info("Bot started and polling…")  # если вы используете logging

    # 5. Старт long-polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
