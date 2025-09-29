# /ErrrorBot/app/states/user_states.py

from aiogram.fsm.state import State, StatesGroup

class StyleInput(StatesGroup):
    """Состояния для добавления нового стиля для личных чатов."""
    waiting_for_style_name = State()
    waiting_for_style_prompt = State()

class GroupStyleInput(StatesGroup):
    """Состояния для добавления нового стиля для групповых чатов."""
    waiting_for_chat_selection = State()
    waiting_for_style_name = State()
    waiting_for_style_prompt = State()

class GroupStyleSelection(StatesGroup):
    """Состояния для выбора группового чата и его стилей."""
    waiting_for_chat_selection = State()
    waiting_for_style_selection = State()
