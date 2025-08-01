# handlers/support_request.py

from aiogram import Router, F                                  # magic filters: F :contentReference[oaicite:0]{index=0}
from aiogram.filters import Command, StateFilter                # Command (для /support и /cancel) :contentReference[oaicite:1]{index=1}; StateFilter (для FSM) :contentReference[oaicite:2]{index=2}
from aiogram.types import Message, CallbackQuery                # типы для сообщений и callback-кворис
from aiogram.fsm.context import FSMContext                      # контекст FSM для хранения данных диалога
from aiogram.utils.keyboard import InlineKeyboardBuilder        # InlineKeyboardBuilder для динамической клавиатуры :contentReference[oaicite:3]{index=3}

from states import SupportRequest
from tracker import create_issue, upload_attachments

router = Router()
import re

PHONE_RE = re.compile(r'^\+?\d{10,15}$')               # от 10 до 15 цифр, с опциональным "+"
EMAIL_RE = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$')  # простой шаблон e-mail

def build_confirm_kb() -> InlineKeyboardBuilder:
    """
    Создаёт inline-клавиатуру с кнопками «Подтвердить» и «Отменить».
    """
    kb = InlineKeyboardBuilder()                               # см. пример использования builder :contentReference[oaicite:4]{index=4}
    kb.button(text="✅ Подтвердить", callback_data="confirm_yes")
    kb.button(text="❌ Отменить",   callback_data="confirm_no")
    kb.adjust(2)
    return kb

@router.message(Command("start"))
async def cmd_support(message: Message, state: FSMContext):
    """
    Стартовый хэндлер: очищаем предыдущие данные и переходим к сбору организации.
    """
    await state.clear()
    await state.set_state(SupportRequest.waiting_for_organization)
    await message.answer("📋 Начнём оформление обращения.\nВведите название организации:")

@router.message(StateFilter(SupportRequest.waiting_for_organization))
async def org_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        return await message.answer("Название организации не может быть пустым. Пожалуйста, введите ещё раз:")
    await state.update_data(organization=text)
    await state.set_state(SupportRequest.waiting_for_full_name)
    await message.answer("✍️ Теперь введите ваше ФИО (имя и фамилия):")

@router.message(StateFilter(SupportRequest.waiting_for_full_name))
async def name_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text.split()) < 2:
        return await message.answer("Пожалуйста, укажите как минимум имя и фамилию:")
    await state.update_data(full_name=text)
    await state.set_state(SupportRequest.waiting_for_phone)
    await message.answer("📞 Укажите номер телефона (10–15 цифр, можно с '+'):")

@router.message(StateFilter(SupportRequest.waiting_for_phone))
async def phone_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if not PHONE_RE.match(text):
        return await message.answer("Некорректный номер. Введите номер из 10–15 цифр, например +71234567890:")
    await state.update_data(phone=text)
    await state.set_state(SupportRequest.waiting_for_email)
    await message.answer("✉️ Введите ваш e-mail:")

@router.message(StateFilter(SupportRequest.waiting_for_email))
async def email_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if not EMAIL_RE.match(text):
        return await message.answer("Некорректный e-mail. Попробуйте ещё раз, например user@example.com:")
    await state.update_data(email=text)
    await state.set_state(SupportRequest.waiting_for_topic)
    await message.answer("📝 Тема обращения:")

@router.message(StateFilter(SupportRequest.waiting_for_topic))
async def topic_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 3:
        return await message.answer("Слишком короткая тема. Опишите тему хотя бы в 3 символа:")
    await state.update_data(topic=text)
    await state.set_state(SupportRequest.waiting_for_description)
    await message.answer("🖋 Опишите проблему подробно (не менее 10 символов):")

@router.message(StateFilter(SupportRequest.waiting_for_description))
async def description_entered(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 10:
        return await message.answer("Слишком короткое описание. Опишите проблему подробнее:")
    await state.update_data(description=text)
    await state.set_state(SupportRequest.waiting_for_attachments)
    await message.answer("📎 Прикрепите файлы или введите /skip, если их нет.")



@router.message(
    StateFilter(SupportRequest.waiting_for_attachments),
    F.photo | F.document | F.text
)
async def attachments_entered(message: Message, state: FSMContext):
    text = message.text or ""

    # 1) Если пользователь ввёл /skip — переходим сразу к подтверждению
    if text.strip().lower() == "/skip":
        data = await state.get_data()
        files = data.get("attachments", [])
        summary = (
            f"👀 Проверьте данные:\n"
            f"• Организация: {data['organization']}\n"
            f"• ФИО: {data['full_name']}\n"
            f"• Телефон: {data['phone']}\n"
            f"• E-mail: {data['email']}\n"
            f"• Тема: {data['topic']}\n"
            f"• Описание: {data['description']}\n"
            f"• Вложения: {len(files)} файл(ов)"
        )
        kb = build_confirm_kb().as_markup()
        await state.update_data(attachments=files)
        await state.set_state(SupportRequest.waiting_for_confirmation)
        return await message.answer(summary, reply_markup=kb)

    # 2) Если это фото или документ — сохраняем его
    if message.photo or message.document:
        attachments = (await state.get_data()).get("attachments", [])
        attachments.append(message.document or message.photo[-1])
        await state.update_data(attachments=attachments)
        return await message.answer(
            f"Файл получен. Всего вложений: {len(attachments)}.\n"
            "Если больше нет — введите /skip."
        )

    # 3) Любой другой текст
    await message.answer("Пожалуйста, прикрепите файл или введите /skip для продолжения.")


@router.callback_query(
    F.data.in_(["confirm_yes", "confirm_no"]),
    StateFilter(SupportRequest.waiting_for_confirmation)
)
async def on_confirm(call: CallbackQuery, state: FSMContext):
    """
    Обрабатывает подтверждение или отмену запроса.
    """
    await call.answer()  # убираем индикатор загрузки
    if call.data == "confirm_no":
        await state.clear()
        return await call.message.edit_text("❌ Отмена. /start для нового обращения")

    # Пользователь подтвердил создание тикета
    data = await state.get_data()
    issue_key = create_issue(data)
    if data.get("attachments"):
        await upload_attachments(issue_key, data["attachments"], call.bot)

    # Регистрируем для опроса комментариев
    from polling import issue_to_chat, last_comment_id
    issue_to_chat[issue_key] = call.from_user.id
    last_comment_id[issue_key] = None

    await call.message.edit_text(
        f"✅ Заявка создана: <b>{issue_key}</b>\n"
        "Ждите ответа техподдержки."
    )
    await state.set_state(SupportRequest.waiting_for_support_response)

@router.message(Command("cancel"), StateFilter("*"))
async def cancel(message: Message, state: FSMContext):
    """
    Прерывание сбора формы в любой момент.
    """
    await state.clear()
    await message.answer("🚫 Процесс отменён. /support для начала заново")
