# polling.py
import asyncio
from typing import Dict

from aiogram import Bot
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from tracker import get_latest_comments
from config import POLL_INTERVAL
from states import SupportRequest

# Временно: в памяти, на проде лучше Redis/DB
issue_to_chat: Dict[str, int] = {}
last_comment_id: Dict[str, int] = {}

async def poll_comments(bot: Bot, storage: MemoryStorage):
    """
    Фоновая задача: каждые POLL_INTERVAL секунд
    опрашивает комментарии по всем активным issue_key,
    отправляет новые комментарии пользователям и завершает FSM.
    """
    while True:
        for issue_key, chat_id in issue_to_chat.items():
            comments = get_latest_comments(issue_key)
            # сортируем по времени, если API не в порядке
            comments = sorted(comments, key=lambda c: c.createdAt)
            last_id = last_comment_id.get(issue_key, None)

            for comment in comments:
                # первый раз: last_id == None, шлём только самый первый новый
                if last_id is None or comment.id > last_id:
                    # Отправляем только пользователям, ждущим ответа
                    # Проверяем FSM-состояние
                    key = StorageKey(chat=chat_id, user=chat_id, bot=bot.token)
                    state = await storage.get_state(key)
                    if state == SupportRequest.waiting_for_support_response.state:
                        await bot.send_message(
                            chat_id,
                            f"📄 Ответ техподдержки по задаче {issue_key}:\n\n"
                            f"{comment.text}"
                        )
                        # После отправки сбросим FSM
                        await storage.set_state(key, None)
                    # Обновляем последний ID (даже если state был другой)
                    last_comment_id[issue_key] = comment.id

        await asyncio.sleep(POLL_INTERVAL)
