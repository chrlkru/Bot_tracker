# handlers/support_request.py
from __future__ import annotations

# from tracker import create_issue, upload_attachments
import re
import smtplib
from email.message import EmailMessage
from io import BytesIO
from typing import List

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import (
    Message,
    CallbackQuery,
    PhotoSize,
    Document,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states import SupportRequest
from config import (
    ADMIN_CHAT_ID,
    ADMIN_EMAIL,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
)

# ──────────────────────────────────────────────
router = Router()

PHONE_RE = re.compile(r"^\+?\d{10,15}$")               # +71234567890
EMAIL_RE = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")  # user@example.com


def build_confirm_kb() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data="confirm_yes")
    kb.button(text="❌ Отменить",   callback_data="confirm_no")
    kb.adjust(2)
    return kb
# ──────────────────────────────────────────────
# 1. Сбор данных анкеты
# ──────────────────────────────────────────────
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(SupportRequest.waiting_for_organization)
    await message.answer("📋 Начнём оформление обращения.\nВведите название организации:")


@router.message(StateFilter(SupportRequest.waiting_for_organization))
async def org_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        return await message.answer("Название организации не может быть пустым. Введите ещё раз:")
    await state.update_data(organization=text)
    await state.set_state(SupportRequest.waiting_for_full_name)
    await message.answer("✍️ Укажите ваше ФИО (имя и фамилия):")


@router.message(StateFilter(SupportRequest.waiting_for_full_name))
async def name_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text.split()) < 2:
        return await message.answer("Укажите как минимум имя и фамилию:")
    await state.update_data(full_name=text)
    await state.set_state(SupportRequest.waiting_for_phone)
    await message.answer("📞 Номер телефона (10–15 цифр, можно с '+'):")


@router.message(StateFilter(SupportRequest.waiting_for_phone))
async def phone_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if not PHONE_RE.match(text):
        return await message.answer("Некорректный номер. Пример: +71234567890")
    await state.update_data(phone=text)
    await state.set_state(SupportRequest.waiting_for_email)
    await message.answer("✉️ Ваш e-mail:")


@router.message(StateFilter(SupportRequest.waiting_for_email))
async def email_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if not EMAIL_RE.match(text):
        return await message.answer("Некорректный e-mail. Пример: user@example.com")
    await state.update_data(email=text)
    await state.set_state(SupportRequest.waiting_for_topic)
    await message.answer("📝 Тема обращения:")


@router.message(StateFilter(SupportRequest.waiting_for_topic))
async def topic_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 3:
        return await message.answer("Тема слишком короткая (≥ 3 симв.).")
    await state.update_data(topic=text)
    await state.set_state(SupportRequest.waiting_for_description)
    await message.answer("🖋 Опишите проблему (≥ 10 симв.):")


@router.message(StateFilter(SupportRequest.waiting_for_description))
async def description_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 10:
        return await message.answer("Описание слишком короткое. Попробуйте подробнее:")
    await state.update_data(description=text)
    await state.set_state(SupportRequest.waiting_for_attachments)
    await message.answer("📎 Прикрепите файлы или введите /skip, если файлов нет.")
# ──────────────────────────────────────────────
# 2. Приём вложений
# ──────────────────────────────────────────────
@router.message(
    StateFilter(SupportRequest.waiting_for_attachments),
    F.photo | F.document | F.text
)
async def attachments_entered(message: Message, state: FSMContext):
    text = (message.text or "").strip().lower()

    # ── Пропуск вложений
    if text == "/skip":
        data = await state.get_data()
        files: List[PhotoSize | Document] = data.get("attachments", [])
        summary = (
            "👀 <b>Проверьте данные</b>:\n"
            f"• Организация: {data['organization']}\n"
            f"• ФИО: {data['full_name']}\n"
            f"• Телефон: {data['phone']}\n"
            f"• E-mail: {data['email']}\n"
            f"• Тема: {data['topic']}\n"
            f"• Описание: {data['description']}\n"
            f"• Вложения: {len(files)} файл(ов)"
        )
        await state.set_state(SupportRequest.waiting_for_confirmation)
        return await message.answer(summary, reply_markup=build_confirm_kb().as_markup(), parse_mode="HTML")

    # ── Сохраняем файл
    if message.photo or message.document:
        attachments = (await state.get_data()).get("attachments", [])
        attachments.append(message.document or message.photo[-1])
        await state.update_data(attachments=attachments)
        return await message.answer(
            f"Файл получен. Всего вложений: {len(attachments)}.\n"
            "Если файлов больше нет — введите /skip."
        )

    # ── Любой другой текст
    await message.answer("Пожалуйста, прикрепите файл или введите /skip, чтобы продолжить.")
# ──────────────────────────────────────────────
# 3. Подтверждение
# ──────────────────────────────────────────────
@router.callback_query(
    F.data.in_(["confirm_yes", "confirm_no"]),
    StateFilter(SupportRequest.waiting_for_confirmation)
)
async def on_confirm(call: CallbackQuery, state: FSMContext):
    await call.answer()  # убрать "часики"

    if call.data == "confirm_no":
        await state.clear()
        return await call.message.edit_text("❌ Отмена. /start для нового обращения")

    # Пользователь подтвердил
    data = await state.get_data()
    attachments: List[PhotoSize | Document] = data.get("attachments", [])

    # ─── Блок Яндекс.Трекера (пока выключен) ───
    # issue_key = create_issue(data)
    # if attachments:
    #     await upload_attachments(issue_key, attachments, call.bot)
    #
    # from polling import issue_to_chat, last_comment_id
    # issue_to_chat[issue_key] = call.from_user.id
    # last_comment_id[issue_key] = None
    # ───────────────────────────────────────────
    # ── 1. Сообщение в Telegram-группу
    summary_html = (
        "🆕 <b>Новая заявка</b>\n\n"
        f"• Организация: {data['organization']}\n"
        f"• ФИО: {data['full_name']}\n"
        f"• Телефон: {data['phone']}\n"
        f"• E-mail: {data['email']}\n"
        f"• Тема: {data['topic']}\n"
        f"• Описание:\n{data['description']}\n\n"
        f"Вложений: {len(attachments)}"
    )
    await call.bot.send_message(ADMIN_CHAT_ID, summary_html, parse_mode="HTML")

    for att in attachments:
        if isinstance(att, PhotoSize):
            await call.bot.send_photo(ADMIN_CHAT_ID, att.file_id)
        else:  # Document
            await call.bot.send_document(ADMIN_CHAT_ID, att.file_id)

    # ── 2. Письмо на почту (с файлами)
    msg = EmailMessage()
    msg["Subject"] = f"Новая заявка: {data['topic']}"
    msg["From"] = SMTP_USER
    msg["To"] = ADMIN_EMAIL
    msg.set_content(summary_html.replace("<b>", "").replace("</b>", ""))

    for att in attachments:
        tg_file = await call.bot.get_file(att.file_id)
        file_io: BytesIO = await call.bot.download_file(tg_file.file_path)
        file_bytes = file_io.getvalue()
        filename = getattr(att, "file_name", None) or f"{att.file_id}.jpg"
        mime = getattr(att, "mime_type", None) or "application/octet-stream"
        maintype, subtype = mime.split("/", 1)
        msg.add_attachment(file_bytes, maintype=maintype, subtype=subtype, filename=filename)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception as err:
        # Если письмо не ушло, выводим в лог/чат (упрощённо)
        await call.bot.send_message(ADMIN_CHAT_ID, f"⚠️ Ошибка отправки письма:\n{err}")

    # ── 3. Уведомляем пользователя
    await call.message.edit_text("✅ Ваша заявка отправлена администраторам. Спасибо!")
    await state.clear()
# ──────────────────────────────────────────────
# 4. Отмена в любой момент
# ──────────────────────────────────────────────
@router.message(Command("cancel"), StateFilter("*"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚫 Процесс отменён. /start для начала заново")
