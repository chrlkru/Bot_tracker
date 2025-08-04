# bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers.support_request import router as support_router

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(support_router)

    print("✅ Bot is up and running!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
