# /ErorrBot/app/handlers/admin_handlers.py

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, MessageEntity
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import asyncio
from typing import Union

from config import bot_config
from app.services.database import db
from app.keyboards import inline as kb
from app.states.admin_states import Broadcast, DemoMode, SimpleDemoMode, GroupBroadcast

class AdminFilter:
    def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        return event.from_user.id in bot_config.admin_ids

router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

@router.callback_query(F.data == "menu_admin")
async def handle_admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    admin_text = "🖥️ <b>Админ-панель</b>"
    await callback.message.edit_text(admin_text, reply_markup=kb.get_admin_menu())
    await callback.answer()

# === РАССЫЛКИ В ЛИЧНЫЕ СООБЩЕНИЯ ===
@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Broadcast.waiting_for_message)
    broadcast_help_text = (
        "📢 <b>Создание рассылки в личные сообщения</b>\n\n"
        "<blockquote>Отправьте сообщение для рассылки. Вы можете использовать форматирование Telegram.</blockquote>\n\n"
        "<blockquote><i>Бот автоматически сохранит все форматирование и отправит его пользователям.</i></blockquote>"
    )
    await callback.message.edit_text(broadcast_help_text, reply_markup=kb.get_back_button("menu_admin"))
    await callback.answer()

@router.message(StateFilter(Broadcast.waiting_for_message))
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_ids = await db.get_all_user_ids()
    sent_count, failed_count = 0, 0
    
    broadcast_text = message.text or message.caption
    broadcast_entities = message.entities or message.caption_entities
    
    if not broadcast_text:
        await message.answer("❌ Сообщение не содержит текста!", reply_markup=kb.get_admin_menu())
        return
    
    status_message = await message.answer(
        f"<b>✅ Начинаю рассылку по личным сообщениям для {len(user_ids)} пользователей...</b>",
    )
    
    for user_id in user_ids:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=broadcast_text,
                entities=broadcast_entities,
                parse_mode=None
            )
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed_count += 1
            if "blocked" in str(e).lower():
                await db.mark_user_blocked(user_id)
    
    result_text = (
        f"✅ <b>Рассылка по личным сообщениям завершена!</b>\n\n"
        f"📤 Отправлено: <b>{sent_count}</b>\n"
        f"❌ Не удалось отправить: <b>{failed_count}</b>"
    )
    await status_message.edit_text(result_text, reply_markup=kb.get_admin_menu())

# === РАССЫЛКИ В ГРУППОВЫЕ ЧАТЫ ===
@router.callback_query(F.data == "admin_group_broadcast")
async def start_group_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GroupBroadcast.waiting_for_message)
    broadcast_help_text = (
        "📢 <b>Создание рассылки по групповым чатам</b>\n\n"
        "<blockquote>Отправьте сообщение для рассылки в групповые чаты. Вы можете использовать форматирование Telegram.</blockquote>\n\n"
        "<blockquote><i>Бот автоматически сохранит все форматирование и отправит его в группы.</i></blockquote>"
    )
    await callback.message.edit_text(broadcast_help_text, reply_markup=kb.get_back_button("menu_admin"))
    await callback.answer()

@router.message(StateFilter(GroupBroadcast.waiting_for_message))
async def process_group_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    group_ids = await db.get_all_group_chat_ids()
    sent_count, failed_count = 0, 0
    
    broadcast_text = message.text or message.caption
    broadcast_entities = message.entities or message.caption_entities
    
    if not broadcast_text:
        await message.answer("❌ Сообщение не содержит текста!", reply_markup=kb.get_admin_menu())
        return
    
    status_message = await message.answer(
        f"<b>✅ Начинаю рассылку по групповым чатам для {len(group_ids)} групп...</b>",
    )
    
    for group_id in group_ids:
        try:
            await bot.send_message(
                chat_id=group_id,
                text=broadcast_text,
                entities=broadcast_entities,
                parse_mode=None
            )
            sent_count += 1
            await asyncio.sleep(0.1)  # Больше задержка для групп
        except Exception as e:
            failed_count += 1
    
    result_text = (
        f"✅ <b>Рассылка по групповым чатам завершена!</b>\n\n"
        f"📤 Отправлено в групп: <b>{sent_count}</b>\n"
        f"❌ Не удалось отправить: <b>{failed_count}</b>"
    )
    await status_message.edit_text(result_text, reply_markup=kb.get_admin_menu())

# === АНИМИРОВАННОЕ ДЕМО ===
@router.callback_query(F.data == "admin_demo_mode")
async def demo_mode_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    all_triggers = await db.get_all_demo_triggers()
    animated_triggers = [(t[0], t[1], t[2], t[3]) for t in all_triggers if t[3]]
    
    text = "🎬 <b>Анимированное демо</b>\n\n<blockquote>Здесь вы можете настроить анимированные ответы на определенные фразы для конкретных пользователей.</blockquote>"
    
    if animated_triggers:
        text += "\n\n<b>Существующие анимированные триггеры:</b>\n"
        for _, user_id, trigger_text, _ in animated_triggers:
            text += f"• <code>{trigger_text}</code> для пользователя <code>{user_id}</code>\n"
    else:
        text += "\n\n<i>Анимированные триггеры пока не созданы.</i>"
        
    await callback.message.edit_text(text, reply_markup=kb.get_demo_mode_menu(animated_triggers))
    await callback.answer()

@router.callback_query(F.data == "admin_demo_add")
async def add_demo_trigger_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DemoMode.waiting_for_user_id)
    help_text = (
        "🎬 <b>Создание нового анимированного триггера</b>\n\n"
        "<blockquote>Введите Telegram ID пользователя для которого создается триггер.\n\n"
        "Триггер будет работать только для указанного пользователя.</blockquote>"
    )
    await callback.message.edit_text(help_text, reply_markup=kb.get_back_button("admin_demo_mode"))
    await callback.answer()

@router.message(StateFilter(DemoMode.waiting_for_user_id))
async def process_demo_user_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "❌ ID пользователя должен быть числом. Попробуйте снова.",
            reply_markup=kb.get_back_button("admin_demo_mode")
        )
        return
    
    user_id = int(message.text)
    await state.update_data(user_id=user_id)
    await state.set_state(DemoMode.waiting_for_trigger_text)
    
    await message.answer(
        f"✅ ID пользователя: <b>{user_id}</b>\n\n"
        "<blockquote>Теперь введите точный текст-триггер.\n\n"
        "Примеры:\n"
        "• <code>test тест</code>\n"
        "• <code>привет</code>\n"
        "• <code>.ai demo</code>\n\n"
        "Когда пользователь напишет этот текст, запустится анимация.</blockquote>",
        reply_markup=kb.get_back_button("admin_demo_mode")
    )

@router.message(StateFilter(DemoMode.waiting_for_trigger_text))
async def process_demo_trigger_text(message: Message, state: FSMContext):
    trigger_text = message.text.strip()
    await state.update_data(trigger_text=trigger_text)
    await state.set_state(DemoMode.waiting_for_responses)
    
    await message.answer(
        f"✅ Триггер: <code>{trigger_text}</code>\n\n"
        "<blockquote>Теперь отправьте анимационную последовательность.\n\n"
        "<b>Каждое сообщение должно быть с новой строки.</b>\n"
        "Бот будет последовательно показывать каждое сообщение с интервалом 1 секунда.\n\n"
        "Пример:\n"
        "<code>Загрузка...\n"
        "Загрузка 50%...\n"
        "Готово!</code>\n\n"
        "Можете использовать любое форматирование Telegram (жирный, курсив, <tg-spoiler>спойлеры</tg-spoiler>, код).</blockquote>",
        reply_markup=kb.get_back_button("admin_demo_mode")
    )

def convert_entities_to_dict(entities):
    """Конвертирует entities в словари для JSON сериализации"""
    if not entities:
        return None
    
    entities_list = []
    for entity in entities:
        entity_dict = {
            'type': entity.type,
            'offset': entity.offset,
            'length': entity.length
        }
        
        # Добавляем дополнительные поля если они есть
        if hasattr(entity, 'url') and entity.url:
            entity_dict['url'] = entity.url
        if hasattr(entity, 'user') and entity.user:
            entity_dict['user_id'] = entity.user.id
        if hasattr(entity, 'language') and entity.language:
            entity_dict['language'] = entity.language
            
        entities_list.append(entity_dict)
    
    return entities_list

@router.message(StateFilter(DemoMode.waiting_for_responses))
async def process_demo_responses(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(
            "❌ Отправьте текстовое сообщение с анимационной последовательностью.",
            reply_markup=kb.get_back_button("admin_demo_mode")
        )
        return
    
    responses = [msg.strip() for msg in message.text.split('\n') if msg.strip()]
    
    if not responses:
        await message.answer(
            "❌ Не удалось разобрать ответы. Попробуйте снова.",
            reply_markup=kb.get_back_button("admin_demo_mode")
        )
        return
    
    if len(responses) < 1:
        await message.answer(
            "❌ Нужен хотя бы один ответ для анимации.",
            reply_markup=kb.get_back_button("admin_demo_mode")
        )
        return
    
    data = await state.get_data()
    user_id = data['user_id']
    trigger_text = data['trigger_text']
    
    # Сохраняем entities для корректного отображения форматирования
    entities_dict = convert_entities_to_dict(message.entities)
    
    try:
        await db.add_demo_trigger(user_id, trigger_text, responses, is_animated=True, entities=entities_dict)
        await state.clear()
        
        preview = "\n".join([f"{i+1}. {resp[:50]}..." if len(resp) > 50 else f"{i+1}. {resp}" 
                           for i, resp in enumerate(responses)])
        
        success_text = (
            f"✅ <b>Анимированный демо-триггер успешно создан!</b>\n\n"
            f"👤 Пользователь: <code>{user_id}</code>\n"
            f"🎯 Триггер: <code>{trigger_text}</code>\n"
            f"🎬 Этапов анимации: <b>{len(responses)}</b>\n\n"
            f"<b>Последовательность:</b>\n{preview}"
        )
        
        await message.answer(success_text, reply_markup=kb.get_admin_menu())
        
    except Exception as e:
        await message.answer(
            "❌ Ошибка при сохранении триггера. Попробуйте позже.",
            reply_markup=kb.get_admin_menu()
        )

# === ПРОСТОЕ ДЕМО ===
@router.callback_query(F.data == "admin_simple_demo_mode")
async def simple_demo_mode_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    all_triggers = await db.get_all_demo_triggers()
    simple_triggers = [(t[0], t[1], t[2], t[3]) for t in all_triggers if not t[3]]
    
    text = "📝 <b>Простое демо</b>\n\n<blockquote>Здесь вы можете настроить простые ответы на определенные фразы для конкретных пользователей без анимации.</blockquote>"
    
    if simple_triggers:
        text += "\n\n<b>Существующие простые триггеры:</b>\n"
        for _, user_id, trigger_text, _ in simple_triggers:
            text += f"• <code>{trigger_text}</code> для пользователя <code>{user_id}</code>\n"
    else:
        text += "\n\n<i>Простые триггеры пока не созданы.</i>"
        
    await callback.message.edit_text(text, reply_markup=kb.get_simple_demo_mode_menu(simple_triggers))
    await callback.answer()

@router.callback_query(F.data == "admin_simple_demo_add")
async def add_simple_demo_trigger_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SimpleDemoMode.waiting_for_user_id)
    help_text = (
        "📝 <b>Создание нового простого триггера</b>\n\n"
        "<blockquote>Введите Telegram ID пользователя для которого создается триггер.\n\n"
        "Триггер будет работать только для указанного пользователя.</blockquote>"
    )
    await callback.message.edit_text(help_text, reply_markup=kb.get_back_button("admin_simple_demo_mode"))
    await callback.answer()

@router.message(StateFilter(SimpleDemoMode.waiting_for_user_id))
async def process_simple_demo_user_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "❌ ID пользователя должен быть числом. Попробуйте снова.",
            reply_markup=kb.get_back_button("admin_simple_demo_mode")
        )
        return
    
    user_id = int(message.text)
    await state.update_data(user_id=user_id)
    await state.set_state(SimpleDemoMode.waiting_for_trigger_text)
    
    await message.answer(
        f"✅ ID пользователя: <b>{user_id}</b>\n\n"
        "<blockquote>Теперь введите точный текст-триггер.\n\n"
        "Примеры:\n"
        "• <code>привет</code>\n"
        "• <code>как дела</code>\n"
        "• <code>demo</code>\n\n"
        "Когда пользователь напишет этот текст, бот ответит простым сообщением.</blockquote>",
        reply_markup=kb.get_back_button("admin_simple_demo_mode")
    )

@router.message(StateFilter(SimpleDemoMode.waiting_for_trigger_text))
async def process_simple_demo_trigger_text(message: Message, state: FSMContext):
    trigger_text = message.text.strip()
    await state.update_data(trigger_text=trigger_text)
    await state.set_state(SimpleDemoMode.waiting_for_response)
    
    await message.answer(
        f"✅ Триггер: <code>{trigger_text}</code>\n\n"
        "<blockquote>Теперь отправьте ответ на этот триггер.\n\n"
        "<b>Можете использовать любое форматирование Telegram:</b>\n"
        "• <b>Жирный текст</b>\n"
        "• <i>Курсив</i>\n"
        "• <code>Код</code>\n"
        "• <blockquote>Цитата</blockquote>\n"
        "• <s>Зачеркнутый</s>\n"
        "• <u>Подчеркнутый</u>\n"
        "• <tg-spoiler>Спойлер</tg-spoiler></blockquote>",
        reply_markup=kb.get_back_button("admin_simple_demo_mode")
    )

@router.message(StateFilter(SimpleDemoMode.waiting_for_response))
async def process_simple_demo_response(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(
            "❌ Отправьте текстовое сообщение с ответом.",
            reply_markup=kb.get_back_button("admin_simple_demo_mode")
        )
        return
    
    response_text = message.text.strip()
    
    if not response_text:
        await message.answer(
            "❌ Ответ не может быть пустым.",
            reply_markup=kb.get_back_button("admin_simple_demo_mode")
        )
        return
    
    data = await state.get_data()
    user_id = data['user_id']
    trigger_text = data['trigger_text']
    
    # Сохраняем entities для корректного отображения форматирования
    entities_dict = convert_entities_to_dict(message.entities)
    
    try:
        # Сохраняем как массив с одним элементом для совместимости
        await db.add_demo_trigger(user_id, trigger_text, [response_text], is_animated=False, entities=entities_dict)
        await state.clear()
        
        success_text = (
            f"✅ <b>Простой демо-триггер успешно создан!</b>\n\n"
            f"👤 Пользователь: <code>{user_id}</code>\n"
            f"🎯 Триггер: <code>{trigger_text}</code>\n"
            f"📝 Ответ: <code>{response_text[:100]}{'...' if len(response_text) > 100 else ''}</code>"
        )
        
        await message.answer(success_text, reply_markup=kb.get_admin_menu())
        
    except Exception as e:
        await message.answer(
            "❌ Ошибка при сохранении триггера. Попробуйте позже.",
            reply_markup=kb.get_admin_menu()
        )

# === УДАЛЕНИЕ ТРИГГЕРОВ ===
@router.callback_query(F.data == "admin_demo_delete_list")
async def list_triggers_to_delete(callback: CallbackQuery):
    all_triggers = await db.get_all_demo_triggers()
    animated_triggers = [(t[0], t[1], t[2], t[3]) for t in all_triggers if t[3]]
    
    if not animated_triggers:
        await callback.answer("Нет созданных анимированных триггеров для удаления.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "<b>Выберите анимированный триггер для удаления:</b>", 
        reply_markup=kb.get_demo_delete_keyboard(animated_triggers)
    )
    await callback.answer()

@router.callback_query(F.data == "admin_simple_demo_delete_list")
async def list_simple_triggers_to_delete(callback: CallbackQuery):
    all_triggers = await db.get_all_demo_triggers()
    simple_triggers = [(t[0], t[1], t[2], t[3]) for t in all_triggers if not t[3]]
    
    if not simple_triggers:
        await callback.answer("Нет созданных простых триггеров для удаления.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "<b>Выберите простой триггер для удаления:</b>", 
        reply_markup=kb.get_simple_demo_delete_keyboard(simple_triggers)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_demo_delete_"))
async def delete_trigger(callback: CallbackQuery, state: FSMContext):
    try:
        trigger_id = int(callback.data.split("_")[-1])
        await db.delete_demo_trigger(trigger_id)
        await callback.answer("✅ Анимированный триггер удален!", show_alert=True)
        await demo_mode_menu(callback, state)
    except (ValueError, TypeError):
        await callback.answer("❌ Ошибка удаления триггера.", show_alert=True)
    except Exception as e:
        await callback.answer("❌ Ошибка удаления триггера.", show_alert=True)

@router.callback_query(F.data.startswith("admin_simple_demo_delete_"))
async def delete_simple_trigger(callback: CallbackQuery, state: FSMContext):
    try:
        trigger_id = int(callback.data.split("_")[-1])
        await db.delete_demo_trigger(trigger_id)
        await callback.answer("✅ Простой триггер удален!", show_alert=True)
        await simple_demo_mode_menu(callback, state)
    except (ValueError, TypeError):
        await callback.answer("❌ Ошибка удаления триггера.", show_alert=True)
    except Exception as e:
        await callback.answer("❌ Ошибка удаления триггера.", show_alert=True)

# === СТАТИСТИКА ===
@router.callback_query(F.data == "admin_global_stats")
async def show_global_stats(callback: CallbackQuery):
    try:
        stats = await db.get_extended_stats()
        all_triggers = await db.get_all_demo_triggers()
        animated_triggers = len([t for t in all_triggers if t[3]])
        simple_triggers = len([t for t in all_triggers if not t[3]])
        
        text = f"""📊 <b>Расширенная статистика</b>

👥 <b>Пользователи:</b>
• Всего пользователей: <b>{stats.get('total_users', 0)}</b>
• Активных (за неделю): <b>{stats.get('active_users', 0)}</b>
• Заблокировали бота: <b>{stats.get('blocked_users', 0)}</b>

🏠 <b>Групповые чаты:</b>
• Всего групп с ботом: <b>{stats.get('total_groups', 0)}</b>
• Общее кол-во участников: <b>{stats.get('total_group_members', 0)}</b>

💬 <b>Активность:</b>
• Всего запросов к ИИ: <b>{stats.get('total_text', 0)}</b>
• Всего запросов (за все время): <b>{stats.get('total_requests_all_time', 0)}</b>

🎬 <b>Демо-режим:</b>
• Анимированных триггеров: <b>{animated_triggers}</b>
• Простых триггеров: <b>{simple_triggers}</b>"""
        
        await callback.message.edit_text(text, reply_markup=kb.get_back_button("menu_admin"))
        await callback.answer()
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ Ошибка загрузки статистики.", 
            reply_markup=kb.get_back_button("menu_admin")
        )
        await callback.answer()

@router.callback_query(F.data == "admin_group_list")
async def show_group_list(callback: CallbackQuery):
    try:
        groups = await db.get_all_group_chats()
        
        if not groups:
            await callback.answer("Бот не добавлен ни в одну группу.", show_alert=True)
            return
        
        text = "🏠 <b>Список групповых чатов с ботом:</b>\n\n"
        
        for i, (chat_id, chat_title, member_count, last_updated) in enumerate(groups[:20], 1):  # Ограничиваем 20 группами
            # Обрезаем длинные названия
            display_title = chat_title[:30] + "..." if len(chat_title) > 30 else chat_title
            text += f"{i}. <b>{display_title}</b>\n"
            text += f"   ID: <code>{chat_id}</code>\n"
            text += f"   Участников: <b>{member_count}</b>\n"
            text += f"   Обновлено: <i>{last_updated[:16] if last_updated else 'неизвестно'}</i>\n\n"
        
        if len(groups) > 20:
            text += f"<i>... и еще {len(groups) - 20} групп</i>"
        
        await callback.message.edit_text(text, reply_markup=kb.get_back_button("menu_admin"))
        await callback.answer()
        
    except Exception as e:
        await callback.message.edit_text(
            "❌ Ошибка загрузки списка групп.", 
            reply_markup=kb.get_back_button("menu_admin")
        )
        await callback.answer()