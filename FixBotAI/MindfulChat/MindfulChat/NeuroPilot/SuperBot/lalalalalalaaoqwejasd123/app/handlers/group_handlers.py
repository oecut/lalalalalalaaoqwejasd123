# /ErrrorBot/app/handlers/group_handlers.py

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.enums import ParseMode, ChatType
import logging
import asyncio
import html
import re

from app.services.database import db
from app.services.g4f_api import g4f_api_service
from app.handlers.common_handlers import (
    send_safe_message, validate_prompt, check_user_limits,
    run_demo_animation, run_simple_demo, format_quoted_message
)
from config import settings

router = Router()








@router.message(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]))
async def handle_group_message(message: Message, bot: Bot):
    """
    Обрабатывает сообщения в групповых чатах с поддержкой различных сценариев:
    1. Демо-триггеры (приоритет)
    2. Прямой запрос .ai <запрос>
    3. Ответ на сообщение с .ai <запрос>
    4. Ответ боту с .ai <запрос>
    5. "Тег" пользователя (ответ на сообщение пользователя с .ai)
    6. Ответ пользователю, который "тегнул" бота
    """
    if not message.text:
        return
    
    message_text = message.text.strip()
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Добавляем группу в базу данных и обновляем количество участников
    chat_title = message.chat.title or f"Группа {chat_id}"
    member_count = 0
    try:
        chat_member_count = await bot.get_chat_member_count(chat_id)
        member_count = chat_member_count
    except Exception as e:
        logging.warning(f"Не удалось получить количество участников чата {chat_id}: {e}")
    
    await db.add_group_chat(chat_id, chat_title, user_id, member_count)
    
    # 1. ПРИОРИТЕТ: Проверяем демо-режим для ЛЮБОГО текста
    demo_result = await db.get_demo_trigger(user_id, message_text)
    
    if demo_result:
        demo_responses, is_animated, entities = demo_result
        
        if is_animated:
            # Анимированное демо
            await run_demo_animation(message, bot, demo_responses, entities)
        else:
            # Простое демо (берем первый элемент из списка)
            await run_simple_demo(message, bot, demo_responses[0], entities)
        return
    
    # 2. Проверяем команды .ai или .ии только если НЕ найден демо-триггер
    if not (message_text.lower().startswith(".ai") or message_text.lower().startswith(".ии")):
        return
    
    # Проверяем лимиты
    if not await check_user_limits(message):
        return

    # Извлекаем промпт после команды
    if message_text.lower().startswith(".ии"):
        prompt = message_text[3:].strip()
    else:
        prompt = message_text[3:].strip()
    
    user_name = message.from_user.first_name or "Пользователь"
    
    # Определяем тип сообщения
    replied_message = message.reply_to_message
    context_text = ""
    original_user_name = ""
    
    if replied_message:
        # Случай 1: Ответ на сообщение другого пользователя (НЕ бота)
        if replied_message.from_user and not replied_message.from_user.is_bot and replied_message.from_user.id != user_id:
            original_user_name = replied_message.from_user.first_name or "Пользователь"
            context_text = replied_message.text or ""
            
            if context_text:
                # Комбинируем контекст с запросом пользователя
                full_prompt = f"Сообщение от {original_user_name}: '{context_text}'\n\nВопрос: {prompt}"
            else:
                full_prompt = prompt
                
                
        # Случай 2: Ответ на сообщение бота
        elif replied_message.from_user and replied_message.from_user.is_bot:
            context_text = replied_message.text or ""
            original_user_name = user_name  # Пользователь отвечает боту
            
            if context_text:
                # Убираем HTML теги из контекста бота для лучшего понимания
                clean_context = re.sub(r'<[^<]+?>', '', context_text)
                full_prompt = f"Предыдущий контекст от бота: '{clean_context}'\n\nНовый запрос: {prompt}"
            else:
                full_prompt = prompt
                
        else:
            # Обычный запрос
            full_prompt = prompt
            original_user_name = user_name
            context_text = prompt
    else:
        # Случай 3: Прямой запрос без ответа на сообщение
        full_prompt = prompt
        original_user_name = user_name
        context_text = prompt

    # Валидируем промпт
    is_valid, error_message = validate_prompt(full_prompt)
    if not is_valid:
        await send_safe_group_message(
            bot, chat_id, error_message,
            reply_to_message_id=message.message_id
        )
        return

    # Показываем статус генерации с жирным форматированием
    safe_prompt_preview = html.escape(prompt[:50])
    status_text = f'<b>⏳ Генерируется ответ для запроса "{safe_prompt_preview}..."</b>'
    
    status_message_id = await send_safe_message(
        bot, chat_id,
        status_text,
        reply_to_message_id=message.message_id
    )
    
    if not status_message_id:
        return

    try:
        # Получаем активный стиль для группы
        active_style_prompt = await db.get_active_group_style_prompt(chat_id)
        
        response = await g4f_api_service.generate_text(
            prompt=full_prompt, 
            system_prompt=active_style_prompt
        )
        
        if len(response.strip()) < 10:
            response = "Получен слишком короткий ответ. Попробуйте перефразировать запрос."
        
        # Форматируем финальный ответ в стиле группового чата
        final_text = format_quoted_message(original_user_name, context_text, response)
        
        # Редактируем статусное сообщение с финальным ответом
        success = await send_safe_message(
            bot, chat_id, final_text,
            edit=True, message_id=status_message_id
        )
        
        if success:
            await db.increment_user_requests(user_id, 'text')
            
    except Exception:
        await send_safe_message(
            bot, chat_id,
            "<b>❌ Произошла ошибка при генерации ответа. Попробуйте позже.</b>",
            edit=True, message_id=status_message_id
        )