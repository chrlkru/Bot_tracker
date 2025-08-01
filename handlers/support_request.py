# handlers/support_request.py

from aiogram import Router, F                                  # magic filters: F :contentReference[oaicite:0]{index=0}
from aiogram.filters import Command, StateFilter                # Command (для /support и /cancel) :contentReference[oaicite:1]{index=1}; StateFilter (для FSM) :contentReference[oaicite:2]{index=2}
from aiogram.types import Message, CallbackQuery                # типы для сообщений и callback-кворис
from aiogram.fsm.context import FSMContext                      # контекст FSM для хранения данных диалога
from aiogram.utils.keyboard import InlineKeyboardBuilder        # InlineKeyboardBuilder для динамической клавиатуры :contentReference[oaicite:3]{index=3}

from states import SupportRequest
from tracker import create_issue, upload_attachments

router = Router()

def build_confirm_kb() -> InlineKeyboardBuilder:
    """
    Создаёт inline-клавиатуру с кнопками «Подтвердить» и «Отменить».
    """
    kb = InlineKeyboardBuilder()                               # см. пример использования builder :contentReference[oaicite:4]{index=4}
    kb.button(text="✅ Подтвердить", callback_data="confirm_yes")
    kb.button(text="❌ Отменить",   callback_data="confirm_no")
    kb.adjust(2)
    return kb

@router.message(Command("support"))
async def cmd_support(message: Message, state: FSMContext):
    """
    Стартовый хэндлер: очищаем предыдущие данные и переходим к сбору организации.
    """
    await state.clear()
    await state.set_state(SupportRequest.waiting_for_organization)
    await message.answer("📋 Начнём оформление обращения.\nВведите название организации:")

@router.message(StateFilter(SupportRequest.waiting_for_organization))
async def org_entered(message: Message, state: FSMContext):
    await state.update_data(organization=message.text)
    await state.set_state(SupportRequest.waiting_for_full_name)
    await message.answer("✍️ Введите ваше ФИО:")

@router.message(StateFilter(SupportRequest.waiting_for_full_name))
async def name_entered(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(SupportRequest.waiting_for_phone)
    await message.answer("📞 Укажите номер телефона:")

@router.message(StateFilter(SupportRequest.waiting_for_phone))
async def phone_entered(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(SupportRequest.waiting_for_email)
    await message.answer("✉️ Введите e-mail:")

@router.message(StateFilter(SupportRequest.waiting_for_email))
async def email_entered(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(SupportRequest.waiting_for_topic)
    await message.answer("📝 Тема обращения:")

@router.message(StateFilter(SupportRequest.waiting_for_topic))
async def topic_entered(message: Message, state: FSMContext):
    await state.update_data(topic=message.text)
    await state.set_state(SupportRequest.waiting_for_description)
    await message.answer("🖋 Опишите проблему подробно:")

@router.message(StateFilter(SupportRequest.waiting_for_description))
async def description_entered(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(SupportRequest.waiting_for_attachments)
    await message.answer("📎 Прикрепите файлы (скриншоты) или введите /skip, если их нет.")

@router.message(
    StateFilter(SupportRequest.waiting_for_attachments),
    F.photo | F.document | (F.text & (~F.text.startswith("/")))  # принимаем фото, документы или любой текст, не начинающийся с "/"
)
async def attachments_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    files = data.get("attachments", [])
    if message.photo or message.document:
        file_id = message.photo[-1].file_id if message.photo else message.document.file_id
        files.append(file_id)
        await state.update_data(attachments=files)
        await message.answer("Файл получен. Можете добавить ещё или введите /done.")
        return

    # любой ввод, не файл, обрабатываем ниже
    text = message.text or ""
    if text.lower() in ("/skip", "/done"):
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
        await message.answer(summary, reply_markup=kb)
        return

    await message.answer("ℹ️ Прикрепите файл или введите /skip /done для продолжения.")

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
        return await call.message.edit_text("❌ Отмена. /support для нового обращения")

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
