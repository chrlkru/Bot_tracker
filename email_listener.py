# email_listener.py
import asyncio
import imaplib
import email
import re
from email.header import decode_header
from typing import List, Tuple, Optional

from aiogram import Bot
from config import (
    EMAIL_IMAP_HOST,
    EMAIL_IMAP_PORT,
    EMAIL_IMAP_USER,
    EMAIL_IMAP_PASSWORD,
    POLL_EMAIL_INTERVAL,
)

# шаблон для извлечения chat_id из темы
CHAT_ID_RE = re.compile(r"user[:\-](\d+)", re.IGNORECASE)


def _decode_header_value(raw_val: Optional[str]) -> str:
    """Декодируем заголовки (Subject, Filename)."""
    if not raw_val:
        return ""
    parts = decode_header(raw_val)
    out = []
    for val, enc in parts:
        if isinstance(val, bytes):
            out.append(val.decode(enc or "utf-8", errors="ignore"))
        else:
            out.append(val)
    return "".join(out)


def _extract_chat_id(msg: email.message.Message) -> Optional[int]:
    """Ищем chat_id в X-Chat-Id или в теме письма."""
    x_chat = msg.get("X-Chat-Id")
    if x_chat and x_chat.isdigit():
        return int(x_chat)

    subject = _decode_header_value(msg.get("Subject"))
    m = CHAT_ID_RE.search(subject)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def _parse_email(msg: email.message.Message) -> Tuple[str, List[Tuple[str, bytes]]]:
    """Парсим тело и вложения письма."""
    body_text = ""
    attachments: List[Tuple[str, bytes]] = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition", "")).lower()

            if ctype == "text/plain" and "attachment" not in disp:
                charset = part.get_content_charset() or "utf-8"
                body_text += part.get_payload(decode=True).decode(charset, errors="ignore")
            elif "attachment" in disp:
                filename = _decode_header_value(part.get_filename() or "file")
                data = part.get_payload(decode=True) or b""
                attachments.append((filename, data))
    else:
        charset = msg.get_content_charset() or "utf-8"
        body_text = msg.get_payload(decode=True).decode(charset, errors="ignore")

    return body_text.strip(), attachments


def _check_mail_once_sync() -> List[Tuple[int, str, List[Tuple[str, bytes]]]]:
    """Синхронная проверка почты. Возвращает список (chat_id, текст, вложения)."""
    results: List[Tuple[int, str, List[Tuple[str, bytes]]]] = []

    imap = imaplib.IMAP4_SSL(EMAIL_IMAP_HOST, EMAIL_IMAP_PORT)
    imap.login(EMAIL_IMAP_USER, EMAIL_IMAP_PASSWORD)

    try:
        imap.select("INBOX")
        status, data = imap.search(None, "UNSEEN")
        if status != "OK":
            return results

        for num in data[0].split():
            _, msg_data = imap.fetch(num, "(RFC822)")
            if not msg_data or msg_data[0] is None:
                continue

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            # ⚠️ фильтр: не читаем письма, отправленные самим ботом
            from_addr = msg.get("From", "").lower()
            if EMAIL_IMAP_USER.lower() in from_addr:
                imap.store(num, "+FLAGS", "\\Seen")
                continue

            chat_id = _extract_chat_id(msg)
            body_text, attachments = _parse_email(msg)

            if chat_id:
                results.append((chat_id, body_text, attachments))

            # помечаем письмо как прочитанное
            imap.store(num, "+FLAGS", "\\Seen")

    finally:
        imap.logout()

    return results


async def poll_email_responses(bot: Bot):
    """Фоновый цикл: проверка почты каждые POLL_EMAIL_INTERVAL секунд."""
    while True:
        try:
            messages = await asyncio.to_thread(_check_mail_once_sync)
            for chat_id, body, atts in messages:
                # отправляем текст
                text = body or "(без текста)"
                await bot.send_message(chat_id, f"✉️ <b>Ответ администратора</b>:\n\n{text}", parse_mode="HTML")

                # отправляем вложения
                for filename, data in atts:
                    await bot.send_document(chat_id, (filename, data))
        except Exception as e:
            print(f"[email_listener] Ошибка: {e}")

        await asyncio.sleep(POLL_EMAIL_INTERVAL)
