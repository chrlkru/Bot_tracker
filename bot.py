# bot.py
import asyncio
from aiogram import Bot, Dispatcher    # core Aiogram classes :contentReference[oaicite:0]{index=0}
from aiogram.fsm.storage.memory import MemoryStorage  # простое хранилище FSM
from config import BOT_TOKEN
from handlers.support_request import router as support_router
from polling import poll_comments

async def main():
    # 1. Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # 2. Регистрация маршрутов (handlers)
    dp.include_router(support_router)

    # 3. Запуск фонового опроса комментариев из Яндекс.Трекера
    asyncio.create_task(poll_comments(bot, storage))

    # 4. Старт long-polling
    # Используем метод start_polling() из Dispatcher :contentReference[oaicite:1]{index=1}
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
