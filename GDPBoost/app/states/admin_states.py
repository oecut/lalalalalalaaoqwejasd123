# /ErrrorBot/app/states/admin_states.py

from aiogram.fsm.state import State, StatesGroup

class Broadcast(StatesGroup):
    """Состояния для создания рассылки в ЛС."""
    waiting_for_message = State()

class GroupBroadcast(StatesGroup):
    """Состояния для создания рассылки по групповым чатам."""
    waiting_for_message = State()

class DemoMode(StatesGroup):
    """Состояния для добавления демо-триггера с поддержкой анимации."""
    waiting_for_user_id = State()
    waiting_for_trigger_text = State()
    waiting_for_responses = State()

class SimpleDemoMode(StatesGroup):
    """Состояния для добавления простого демо-триггера без анимации."""
    waiting_for_user_id = State()
    waiting_for_trigger_text = State()
    waiting_for_response = State()