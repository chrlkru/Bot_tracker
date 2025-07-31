from aiogram.fsm.state import StatesGroup, State

class SupportRequest(StatesGroup):
    waiting_for_organization         = State()
    waiting_for_full_name            = State()
    waiting_for_phone                = State()
    waiting_for_email                = State()
    waiting_for_topic                = State()
    waiting_for_description          = State()
    waiting_for_attachments          = State()
    waiting_for_confirmation         = State()
    waiting_for_support_response     = State()   # ← здесь
    cancelled                         = State()
