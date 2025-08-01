# tracker.py
import logging
from io import BytesIO
from typing import List

from aiogram import Bot
from yandex_tracker_client import TrackerClient
from yandex_tracker_client.exceptions import NotFound   # единственное задокументированное исключение :contentReference[oaicite:1]{index=1}

from config import YT_TOKEN, YT_ORG_ID

# Инициализация клиента
client = TrackerClient(token=YT_TOKEN, org_id=YT_ORG_ID)

def create_issue(data: dict) -> str:
    """
    Создаёт задачу в Yandex Tracker и возвращает её ключ.
    Ловит NotFound только для обращения к несуществующему ресурсу,
    а все прочие ошибки прокидывает дальше.
    """
    try:
        issue = client.issues.create(
            queue="SUPPORT",
            summary=f"{data['topic']} — {data['organization']}",
            description=data["description"],
            type={"name": "Обращение"},
            customFields={
                "fullName": data["full_name"],
                "phone":    data["phone"],
                "email":    data["email"]
            }
        )
        return issue.key
    except NotFound as e:
        logging.error("Tracker 404: issue not found — %s", e)
        raise
    except Exception:
        logging.exception("Failed to create issue in Tracker")
        raise

async def upload_attachments(issue_key: str, file_ids: List[str], bot: Bot):
    """
    Скачивает файлы из Telegram и загружает их в задачу Tracker.
    Любые сбои (сетевые, API-ошибки) логируем, но работу бота не прерываем.
    """
    for file_id in file_ids:
        try:
            tfile = await bot.get_file(file_id)
            buffer = BytesIO()
            await bot.download_file_to_memory(tfile.file_path, buffer)
            buffer.seek(0)
            client.attachments.create(issue_key, buffer, filename=f"{file_id}.dat")
        except Exception:
            logging.exception("Failed to upload attachment %s for issue %s", file_id, issue_key)

def get_latest_comments(issue_key: str):
    """
    Возвращает отсортированный по дате список комментариев задачи.
    Оборачиваем в общий Exception-блок на случай непредвиденной ошибки.
    """
    try:
        comments = client.issues[issue_key].comments.get_all()
        return sorted(comments, key=lambda c: c.createdAt)
    except NotFound:
        logging.error("Tracker 404 on comments for %s", issue_key)
        return []
    except Exception:
        logging.exception("Failed to fetch comments for %s", issue_key)
        return []
