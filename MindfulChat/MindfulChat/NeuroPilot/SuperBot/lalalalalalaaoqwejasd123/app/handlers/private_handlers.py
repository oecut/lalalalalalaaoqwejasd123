# /ErrrorBot/app/handlers/private_handlers.py

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.enums import ParseMode, ChatType
import logging
import asyncio
import html

from app.services.database import db
from app.services.g4f_api import g4f_api_service
from app.handlers.common_handlers import (
    send_safe_message, validate_prompt, check_user_limits
)
from app.utils import format_ai_response_to_html
from config import settings

router = Router()




@router.message(F.chat.type == ChatType.PRIVATE)
async def handle_private_message(message: Message, bot: Bot):
    """
    Обрабатывает сообщения в приватных чатах (не business).
    Работает от лица бота, использует личные стили пользователя.
    Поддерживает команды .ai и .ии
    """
    if not message.text:
        return
    
    message_text = message.text.strip()
    
    # Проверяем команды .ai или .ии
    if not (message_text.lower().startswith(".ai") or message_text.lower().startswith(".ии")):
        return
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    
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
            bot, chat_id, error_message,
            reply_to_message_id=message.message_id
        )
        return

    # 🎬 Показываем анимацию печатания для мгновенного отклика
    user_name = message.from_user.first_name or "Пользователь"
    safe_prompt_preview = html.escape(prompt[:50])
    
    # Функция для показа анимации печатания
    async def show_typing_animation():
        await bot.send_chat_action(chat_id, "typing")
        await asyncio.sleep(0.5)  # Короткая задержка для реалистичности
    
    status_text = f'<b>⚡ errorer bot печатает ответ на "{safe_prompt_preview}..."</b>'
    
    status_message_id = await send_safe_message(
        bot, chat_id,
        status_text,
        reply_to_message_id=message.message_id
    )
    
    if not status_message_id:
        return

    try:
        # Для ЛС используем персональные стили пользователя
        active_style_prompt = await db.get_active_style_prompt(user_id)
        
        # Запускаем генерацию с анимацией печатания
        response = await g4f_api_service.generate_text(
            prompt=prompt, 
            system_prompt=active_style_prompt or "",
            show_typing=show_typing_animation
        )
        
        if len(response.strip()) < 10:
            response = "Получен слишком короткий ответ. Попробуйте перефразировать запрос."
        
        # Форматируем финальный ответ
        formatted_ai_response = format_ai_response_to_html(response)
        safe_user_name = html.escape(user_name)
        safe_prompt = html.escape(prompt)
        
        final_text = (
            f"<blockquote>{safe_user_name}: {safe_prompt}</blockquote>\n\n"
            f"💬 <b>{formatted_ai_response}</b>"
        )
        
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