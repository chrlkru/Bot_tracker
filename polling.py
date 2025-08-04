# polling.py
# Интеграция с Яндекс.Трекером отключена.
# Файл оставлен как заглушка, чтобы существующие импорты не падали.

# Плейсхолдеры для совместимости с текущим кодом
issue_to_chat: dict[str, int] = {}
last_comment_id: dict[str, int] = {}

async def poll_comments(*args, **kwargs):
    """No-op: фоновый опрос комментариев отключён."""
    return
