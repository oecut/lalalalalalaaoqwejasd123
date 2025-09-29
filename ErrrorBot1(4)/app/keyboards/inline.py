# /ErrrorBot/app/keyboards/inline.py

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Tuple

from messages import Buttons
from config import bot_config

# --- Принудительная подписка ---
def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для принудительной подписки"""
    builder = InlineKeyboardBuilder()
    builder.button(text=Buttons.subscribed, callback_data="check_subscription")
    return builder.as_markup()

# --- Пользовательские клавиатуры ---
def get_main_menu(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=Buttons.help, callback_data="menu_help")
    builder.button(text=Buttons.faq, callback_data="menu_faq")
    builder.button(text=Buttons.settings, callback_data="menu_settings")
    builder.button(text=Buttons.stats, callback_data="menu_stats")
    if user_id in bot_config.admin_ids:
        builder.button(text=Buttons.admin_panel, callback_data="menu_admin")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def get_settings_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=Buttons.answer_styles, callback_data="settings_styles")
    builder.button(text=Buttons.back, callback_data="back_to_main")
    builder.adjust(1, 1)
    return builder.as_markup()

def get_styles_menu() -> InlineKeyboardMarkup:
    """Главное меню стилей с выбором между личными и групповыми"""
    builder = InlineKeyboardBuilder()
    builder.button(text=Buttons.personal_styles, callback_data="styles_personal")
    builder.button(text=Buttons.group_styles, callback_data="styles_group")
    builder.button(text=Buttons.back, callback_data="back_to_settings")
    builder.adjust(1, 1, 1)
    return builder.as_markup()

# === ЛИЧНЫЕ СТИЛИ ===
def get_personal_styles_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=Buttons.add_style, callback_data="personal_styles_add")
    builder.button(text=Buttons.select_style, callback_data="personal_styles_select")
    builder.button(text=Buttons.list_styles, callback_data="personal_styles_list")
    builder.button(text=Buttons.back, callback_data="settings_styles")
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()

def get_select_personal_style_keyboard(styles: List[Tuple[int, str, bool]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for style_id, style_name, is_active in styles:
        text = f"✅ {style_name}" if is_active else style_name
        builder.button(text=text, callback_data=f"personal_style_select_{style_id}")
    builder.button(text=Buttons.back, callback_data="styles_personal")
    builder.adjust(1)
    return builder.as_markup()

# === ГРУППОВЫЕ СТИЛИ ===
def get_group_styles_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=Buttons.add_group_style, callback_data="group_styles_add")
    builder.button(text=Buttons.select_group_style, callback_data="group_styles_select")
    builder.button(text=Buttons.list_group_styles, callback_data="group_styles_list")
    builder.button(text=Buttons.back, callback_data="settings_styles")
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()

def get_group_selection_keyboard(groups: List[Tuple[int, str]], action: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора группы.
    action: "add_style" или "select_style"
    """
    builder = InlineKeyboardBuilder()
    
    for chat_id, chat_title in groups:
        # Обрезаем длинные названия групп
        display_title = chat_title[:25] + "..." if len(chat_title) > 25 else chat_title
        callback_data = f"group_{action}_{chat_id}"
        builder.button(text=f"👥 {display_title}", callback_data=callback_data)
    
    if action == "add_style":
        builder.button(text=Buttons.back, callback_data="styles_group")
    else:
        builder.button(text=Buttons.back, callback_data="styles_group")
    
    builder.adjust(1)
    return builder.as_markup()

def get_select_group_style_keyboard(styles: List[Tuple[int, str, bool]], chat_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for style_id, style_name, is_active in styles:
        text = f"✅ {style_name}" if is_active else style_name
        builder.button(text=text, callback_data=f"group_style_select_{style_id}")
    
    builder.button(text=Buttons.back, callback_data="group_styles_select")
    builder.adjust(1)
    return builder.as_markup()

# === ОБЩИЕ ФУНКЦИИ ===
def get_back_button(callback_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=Buttons.back, callback_data=callback_data)
    return builder.as_markup()

# === ОБРАТНАЯ СОВМЕСТИМОСТЬ ===
def get_select_style_keyboard(styles: List[Tuple[int, str, bool]]) -> InlineKeyboardMarkup:
    """Для обратной совместимости - перенаправляем на личные стили"""
    return get_select_personal_style_keyboard(styles)

# --- Админские клавиатуры ---
def get_admin_menu() -> InlineKeyboardMarkup:
    """Создает главную клавиатуру админ-панели."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Рассылка в ЛС", callback_data="admin_broadcast")
    builder.button(text="📢 Рассылка в группы", callback_data="admin_group_broadcast")
    builder.button(text="🎬 Анимированное демо", callback_data="admin_demo_mode")
    builder.button(text="📝 Простое демо", callback_data="admin_simple_demo_mode")
    builder.button(text="📊 Статистика", callback_data="admin_global_stats")
    builder.button(text="👥 Список групп", callback_data="admin_group_list")  # ИСПРАВЛЕНО
    builder.button(text=Buttons.back, callback_data="back_to_main")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def get_demo_mode_menu(triggers: List[Tuple[int, int, str, bool]]) -> InlineKeyboardMarkup:
    """Создает клавиатуру управления демо-режимом с анимацией."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить анимированный триггер", callback_data="admin_demo_add")
    if triggers:
        builder.button(text="❌ Удалить триггер", callback_data="admin_demo_delete_list")
    builder.button(text=Buttons.back, callback_data="menu_admin")
    builder.adjust(1)
    return builder.as_markup()

def get_simple_demo_mode_menu(triggers: List[Tuple[int, int, str, bool]]) -> InlineKeyboardMarkup:
    """Создает клавиатуру управления простым демо-режимом."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить простой триггер", callback_data="admin_simple_demo_add")
    if triggers:
        builder.button(text="❌ Удалить триггер", callback_data="admin_simple_demo_delete_list")
    builder.button(text=Buttons.back, callback_data="menu_admin")
    builder.adjust(1)
    return builder.as_markup()

def get_demo_delete_keyboard(triggers: List[Tuple[int, int, str, bool]]) -> InlineKeyboardMarkup:
    """Создает клавиатуру для удаления демо-триггеров."""
    builder = InlineKeyboardBuilder()
    for trigger_id, user_id, trigger_text, is_animated in triggers:
        # Обрезаем длинный текст триггера для отображения
        display_text = trigger_text[:20] + "..." if len(trigger_text) > 20 else trigger_text
        animation_type = "🎬" if is_animated else "📝"
        button_text = f"{animation_type} '{display_text}' (ID: {user_id})"
        builder.button(text=button_text, callback_data=f"admin_demo_delete_{trigger_id}")
    builder.button(text=Buttons.back, callback_data="admin_demo_mode")
    builder.adjust(1)
    return builder.as_markup()

def get_simple_demo_delete_keyboard(triggers: List[Tuple[int, int, str, bool]]) -> InlineKeyboardMarkup:
    """Создает клавиатуру для удаления простых демо-триггеров."""
    builder = InlineKeyboardBuilder()
    for trigger_id, user_id, trigger_text, is_animated in triggers:
        if not is_animated:  # Показываем только простые триггеры
            display_text = trigger_text[:20] + "..." if len(trigger_text) > 20 else trigger_text
            button_text = f"📝 '{display_text}' (ID: {user_id})"
            builder.button(text=button_text, callback_data=f"admin_simple_demo_delete_{trigger_id}")
    builder.button(text=Buttons.back, callback_data="admin_simple_demo_mode")
    builder.adjust(1)
    return builder.as_markup()