# /ErrrorBot/app/handlers/business_handlers.py

from aiogram import Router, F, Bot
from aiogram.types import Message, MessageEntity
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.enums import ParseMode
import logging
import asyncio
import re
import html
import json

from app.services.database import db
from app.services.g4f_api import g4f_api_service
from app.utils import format_final_message_html
from app.handlers.common_handlers import (
    send_safe_message, validate_prompt, check_user_limits,
    run_demo_animation, run_simple_demo
)
from config import settings

router = Router()







@router.business_message()
async def handle_any_business_message(message: Message, bot: Bot):
    """
    Обрабатывает ВСЕ бизнес-сообщения:
    1. Сначала проверяет демо-триггеры для ЛЮБОГО текста
    2. Затем проверяет команду .ai или .ии
    """
    if not message.text:
        return
    
    user_id = message.from_user.id
    message_text = message.text.strip()
    
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
    
    # 2. Проверяем команду .ai или .ии только если НЕ найден демо-триггер
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
    
    # Валидируем промпт
    is_valid, error_message = validate_prompt(prompt)
    if not is_valid:
        await send_safe_message(
            bot, message.chat.id, error_message,
            message.business_connection_id, message.message_id, edit=True
        )
        return

    # Показываем статус генерации
    user_name = message.from_user.first_name or "Пользователь"
    safe_prompt_preview = html.escape(prompt[:50])
    status_text = f'<blockquote>⏳ Генерируется ответ для запроса "{safe_prompt_preview}..."</blockquote>'
    
    status_sent = await send_safe_message(
        bot, message.chat.id,
        status_text,
        message.business_connection_id, message.message_id, edit=True
    )
    
    if not status_sent:
        logging.error("Не удалось показать статус генерации")
        return

    try:
        # Получаем активный стиль
        active_style_prompt = await db.get_active_style_prompt(message.from_user.id)
        
        response = await g4f_api_service.generate_text(
            prompt=prompt, 
            system_prompt=active_style_prompt
        )
        
        if len(response.strip()) < 10:
            response = "Получен слишком короткий ответ. Попробуйте перефразировать запрос."
        
        # Форматируем финальный ответ
        final_text = format_final_message_html(user_name, prompt, response)
        
        # Отправляем финальный ответ (может быть разделен на несколько сообщений)
        success = await send_safe_message(
            bot, message.chat.id, final_text,
            message.business_connection_id, message.message_id, edit=True
        )
        
        if success:
            await db.increment_user_requests(user_id, 'text')
            
    except Exception:
        await send_safe_message(
            bot, message.chat.id,
            "❌ Произошла ошибка при генерации ответа. Попробуйте позже.",
            message.business_connection_id, message.message_id, edit=True
        )