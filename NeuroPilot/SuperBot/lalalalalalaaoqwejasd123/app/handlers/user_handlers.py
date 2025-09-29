# /ErorrBot/app/handlers/user_handlers.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from messages import Greetings, Menus, Help, Buttons
from app.keyboards import inline as kb
from app.services.database import db
from app.states.user_states import StyleInput, GroupStyleInput, GroupStyleSelection
from config import settings

router = Router()

@router.message(CommandStart())
async def handle_start_command(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await db.add_or_update_user(user_id=user.id, username=user.username, first_name=user.first_name)
    await message.answer(text=Greetings.start_message, reply_markup=kb.get_main_menu(user.id))

@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text=Greetings.start_message, reply_markup=kb.get_main_menu(callback.from_user.id))
    await callback.answer()

@router.callback_query(F.data == "menu_help")
async def handle_help_menu(callback: CallbackQuery):
    await callback.message.edit_text(text=Help.help_message, reply_markup=kb.get_back_button("back_to_main"), disable_web_page_preview=True)
    await callback.answer()

@router.callback_query(F.data == "menu_faq")
async def handle_faq_menu(callback: CallbackQuery):
    await callback.message.edit_text(text=Help.faq_message, reply_markup=kb.get_back_button("back_to_main"), disable_web_page_preview=True)
    await callback.answer()

@router.callback_query(F.data == "menu_stats")
async def handle_stats_menu(callback: CallbackQuery):
    try:
        stats_data = await db.get_user_stats(callback.from_user.id)
        if stats_data:
            remaining_requests = max(0, settings.daily_request_limit - stats_data.get('user_today_total', 0))
            
            stats_text = f"""📈 <b>Личная аналитика</b>

💯 <b>Ваша активность</b>
<blockquote>📅 Сегодня: <b>{stats_data.get('user_today_total', 0)}</b> запросов
📈 Всего: <b>{stats_data.get('total_text', 0)}</b> ответов ИИ
💎 Общие запросы: <b>{stats_data.get('total_requests_all_time', 0)}</b></blockquote>

⚡ <b>Осталось на сегодня</b>
<blockquote>🔥 <b>{remaining_requests}</b> запросов из {settings.daily_request_limit}</blockquote>

🌍 <b>Общая статистика</b>
<blockquote>👤 Активные пользователи: <b>{stats_data.get('active_users', 0)}</b>
👥 Групповые чаты: <b>{stats_data.get('total_groups', 0)}</b></blockquote>"""
        else:
            stats_text = "📊 <b>Статистика недоступна</b>\n\n<blockquote>🚀 Начните использовать бота, чтобы увидеть свою аналитику!</blockquote>"
    except Exception as e:
        stats_text = "⚠️ <b>Ошибка загрузки</b>\n\n<blockquote>🔄 Попробуйте обновить через несколько моментов</blockquote>"
        
    await callback.message.edit_text(text=stats_text, reply_markup=kb.get_back_button("back_to_main"))
    await callback.answer()

@router.callback_query(F.data == "menu_settings")
async def handle_settings_menu(callback: CallbackQuery):
    await callback.message.edit_text(text=Menus.settings_menu, reply_markup=kb.get_settings_menu())
    await callback.answer()

@router.callback_query(F.data == "back_to_settings")
async def handle_back_to_settings(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text=Menus.settings_menu, reply_markup=kb.get_settings_menu())
    await callback.answer()

@router.callback_query(F.data == "settings_styles")
async def handle_styles_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text=Menus.styles_menu, reply_markup=kb.get_styles_menu())
    await callback.answer()

# === ЛИЧНЫЕ СТИЛИ ===
@router.callback_query(F.data == "styles_personal")
async def handle_personal_styles_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text=Menus.personal_styles_menu, reply_markup=kb.get_personal_styles_menu())
    await callback.answer()

@router.callback_query(F.data == "personal_styles_add")
async def handle_add_personal_style_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StyleInput.waiting_for_style_name)
    await callback.message.edit_text(text=Menus.add_style_prompt_name, reply_markup=kb.get_back_button("styles_personal"))
    await callback.answer()

@router.message(StateFilter(StyleInput.waiting_for_style_name), F.text)
async def process_personal_style_name(message: Message, state: FSMContext):
    await state.update_data(style_name=message.text)
    await state.set_state(StyleInput.waiting_for_style_prompt)
    await message.answer(
        "✅ Название стиля сохранено.\n\n"
        "<blockquote>Теперь введите описание стиля (системный промпт). Например: \"Отвечай всегда в стиле пирата\" или \"Будь максимально кратким\"</blockquote>"
    )

@router.message(StateFilter(StyleInput.waiting_for_style_prompt), F.text)
async def process_personal_style_prompt(message: Message, state: FSMContext):
    data = await state.get_data()
    style_name = data.get("style_name")
    style_prompt = message.text
    
    try:
        await db.add_user_style(message.from_user.id, style_name, style_prompt)
        await state.clear()
        await message.answer(f"✅ <b>Личный стиль '{style_name}' успешно сохранен!</b>")
        await message.answer(text=Menus.personal_styles_menu, reply_markup=kb.get_personal_styles_menu())
    except Exception as e:
        await message.answer(
            "❌ Ошибка при сохранении стиля. Попробуйте позже.",
            reply_markup=kb.get_personal_styles_menu()
        )

@router.callback_query(F.data == "personal_styles_select")
async def handle_select_personal_style(callback: CallbackQuery):
    styles = await db.get_user_styles(callback.from_user.id)
    if not styles:
        await callback.answer("У вас еще нет сохраненных личных стилей. Сначала добавьте один.", show_alert=True)
        return
    await callback.message.edit_text(text=Menus.select_personal_style_menu, reply_markup=kb.get_select_personal_style_keyboard(styles))
    await callback.answer()

@router.callback_query(F.data.startswith("personal_style_select_"))
async def process_personal_style_selection(callback: CallbackQuery):
    try:
        style_id = int(callback.data.split("_")[-1])
        await db.set_active_style(callback.from_user.id, style_id)
        styles = await db.get_user_styles(callback.from_user.id)
        await callback.message.edit_text(text=Menus.select_personal_style_menu, reply_markup=kb.get_select_personal_style_keyboard(styles))
        await callback.answer("✅ Личный стиль применен!", show_alert=True)
    except (ValueError, TypeError):
        await callback.answer("❌ Ошибка выбора стиля.", show_alert=True)

@router.callback_query(F.data == "personal_styles_list")
async def handle_list_personal_styles(callback: CallbackQuery):
    styles = await db.get_user_styles(callback.from_user.id)
    if not styles:
        await callback.answer("У вас еще нет сохраненных личных стилей.", show_alert=True)
        return
    
    styles_text = "📋 <b>Список ваших личных стилей</b>\n\n"
    for _, style_name, is_active in styles:
        status = " ✅ (активен)" if is_active else ""
        styles_text += f"• <b>{style_name}</b>{status}\n"
        
    await callback.message.edit_text(text=styles_text, reply_markup=kb.get_back_button("styles_personal"))
    await callback.answer()

# === ГРУППОВЫЕ СТИЛИ ===
@router.callback_query(F.data == "styles_group")
async def handle_group_styles_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_groups = await db.get_user_group_chats(callback.from_user.id)
    if not user_groups:
        await callback.answer("У вас нет групповых чатов с ботом. Сначала добавьте бота в группу.", show_alert=True)
        return
    
    await callback.message.edit_text(text=Menus.group_styles_menu, reply_markup=kb.get_group_styles_menu())
    await callback.answer()

@router.callback_query(F.data == "group_styles_add")
async def handle_add_group_style_start(callback: CallbackQuery, state: FSMContext):
    user_groups = await db.get_user_group_chats(callback.from_user.id)
    if not user_groups:
        await callback.answer("У вас нет групповых чатов с ботом. Сначала добавьте бота в группу.", show_alert=True)
        return
    
    await state.set_state(GroupStyleInput.waiting_for_chat_selection)
    await callback.message.edit_text(
        text=Menus.select_group_for_style, 
        reply_markup=kb.get_group_selection_keyboard(user_groups, "add_style")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("group_add_style_"))
async def process_group_selection_for_add(callback: CallbackQuery, state: FSMContext):
    try:
        chat_id = int(callback.data.split("_")[-1])
        await state.update_data(chat_id=chat_id)
        await state.set_state(GroupStyleInput.waiting_for_style_name)
        await callback.message.edit_text(
            text="✅ Группа выбрана.\n\n<blockquote>Теперь введите название стиля для этой группы:</blockquote>",
            reply_markup=kb.get_back_button("styles_group")
        )
        await callback.answer()
    except (ValueError, TypeError):
        await callback.answer("❌ Ошибка выбора группы.", show_alert=True)

@router.message(StateFilter(GroupStyleInput.waiting_for_style_name), F.text)
async def process_group_style_name(message: Message, state: FSMContext):
    await state.update_data(style_name=message.text)
    await state.set_state(GroupStyleInput.waiting_for_style_prompt)
    await message.answer(
        "✅ Название стиля сохранено.\n\n"
        "<blockquote>Теперь введите описание стиля (системный промпт) для группового чата. Например: \"Отвечай всегда в стиле пирата\" или \"Будь максимально кратким\"</blockquote>"
    )

@router.message(StateFilter(GroupStyleInput.waiting_for_style_prompt), F.text)
async def process_group_style_prompt(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data.get("chat_id")
    style_name = data.get("style_name")
    style_prompt = message.text
    
    try:
        await db.add_group_style(chat_id, style_name, style_prompt, message.from_user.id)
        await state.clear()
        await message.answer(f"✅ <b>Групповой стиль '{style_name}' успешно сохранен!</b>")
        await message.answer(text=Menus.group_styles_menu, reply_markup=kb.get_group_styles_menu())
    except Exception as e:
        await message.answer(
            "❌ Ошибка при сохранении группового стиля. Попробуйте позже.",
            reply_markup=kb.get_group_styles_menu()
        )

@router.callback_query(F.data == "group_styles_select")
async def handle_select_group_style_start(callback: CallbackQuery, state: FSMContext):
    user_groups = await db.get_user_group_chats(callback.from_user.id)
    if not user_groups:
        await callback.answer("У вас нет групповых чатов с ботом.", show_alert=True)
        return
    
    await state.set_state(GroupStyleSelection.waiting_for_chat_selection)
    await callback.message.edit_text(
        text=Menus.select_group_for_style_selection,
        reply_markup=kb.get_group_selection_keyboard(user_groups, "select_style")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("group_select_style_"))
async def process_group_selection_for_select(callback: CallbackQuery, state: FSMContext):
    try:
        chat_id = int(callback.data.split("_")[-1])
        styles = await db.get_group_styles(chat_id)
        if not styles:
            await callback.answer("В этой группе еще нет стилей. Сначала добавьте один.", show_alert=True)
            return
        
        await state.update_data(chat_id=chat_id)
        await state.set_state(GroupStyleSelection.waiting_for_style_selection)
        await callback.message.edit_text(
            text=Menus.select_group_style_menu, 
            reply_markup=kb.get_select_group_style_keyboard(styles, chat_id)
        )
        await callback.answer()
    except (ValueError, TypeError):
        await callback.answer("❌ Ошибка выбора группы.", show_alert=True)

@router.callback_query(F.data.startswith("group_style_select_"))
async def process_group_style_selection(callback: CallbackQuery, state: FSMContext):
    try:
        parts = callback.data.split("_")
        style_id = int(parts[-1])
        chat_id_from_state = (await state.get_data()).get("chat_id")
        
        if not chat_id_from_state:
            await callback.answer("❌ Ошибка: группа не выбрана.", show_alert=True)
            return
        
        await db.set_active_group_style(chat_id_from_state, style_id)
        
        # Обновляем клавиатуру с новым активным стилем
        styles = await db.get_group_styles(chat_id_from_state)
        await callback.message.edit_text(
            text=Menus.select_group_style_menu, 
            reply_markup=kb.get_select_group_style_keyboard(styles, chat_id_from_state)
        )
        await callback.answer("✅ Групповой стиль применен!", show_alert=True)
    except (ValueError, TypeError):
        await callback.answer("❌ Ошибка выбора стиля.", show_alert=True)

@router.callback_query(F.data == "group_styles_list")
async def handle_list_group_styles(callback: CallbackQuery):
    user_groups = await db.get_user_group_chats(callback.from_user.id)
    if not user_groups:
        await callback.answer("У вас нет групповых чатов с ботом.", show_alert=True)
        return
    
    styles_text = "📋 <b>Список групповых стилей</b>\n\n"
    
    for chat_id, chat_title in user_groups:
        styles = await db.get_group_styles(chat_id)
        styles_text += f"<b>🏠 {chat_title}</b>\n"
        
        if styles:
            for _, style_name, is_active in styles:
                status = " ✅ (активен)" if is_active else ""
                styles_text += f"  • <b>{style_name}</b>{status}\n"
        else:
            styles_text += "  <i>Стилей пока нет</i>\n"
        styles_text += "\n"
        
    await callback.message.edit_text(text=styles_text, reply_markup=kb.get_back_button("styles_group"))
    await callback.answer()

# Возвращение к меню групповых стилей
@router.callback_query(F.data == "back_to_group_styles")
async def handle_back_to_group_styles(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text=Menus.group_styles_menu, reply_markup=kb.get_group_styles_menu())
    await callback.answer()

# Возвращение к меню личных стилей
@router.callback_query(F.data == "back_to_personal_styles")
async def handle_back_to_personal_styles(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text=Menus.personal_styles_menu, reply_markup=kb.get_personal_styles_menu())
    await callback.answer()

# Старые обработчики для обратной совместимости
@router.callback_query(F.data == "styles_add")
async def handle_add_style_start(callback: CallbackQuery, state: FSMContext):
    # Перенаправляем на личные стили
    await handle_add_personal_style_start(callback, state)

@router.callback_query(F.data == "styles_select")
async def handle_select_style(callback: CallbackQuery):
    # Перенаправляем на личные стили
    await handle_select_personal_style(callback)

@router.callback_query(F.data == "styles_list")
async def handle_list_styles(callback: CallbackQuery):
    # Перенаправляем на личные стили
    await handle_list_personal_styles(callback)