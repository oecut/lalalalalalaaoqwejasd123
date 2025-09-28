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
from app.utils import format_ai_response_to_html, split_long_message
from config import settings
from messages import Errors

router = Router()

async def send_safe_private_message(bot: Bot, chat_id: int, text: str, 
                                   reply_to_message_id: int = None,
                                   edit_message_id: int = None) -> bool:
    """Безопасная отправка сообщений в ЛС с HTML-парсингом и разделением длинных сообщений."""
    
    # Разделяем длинное сообщение на части
    message_parts = split_long_message(text)
    
    try:
        # Если нужно редактировать сообщение
        if edit_message_id:
            await bot.edit_message_text(
                text=message_parts[0],
                chat_id=chat_id,
                message_id=edit_message_id,
                parse_mode=ParseMode.HTML
            )
            
            # Отправляем остальные части как новые сообщения
            for part in message_parts[1:]:
                await asyncio.sleep(0.1)
                await bot.send_message(
                    chat_id=chat_id,
                    text=part,
                    parse_mode=ParseMode.HTML
                )
        else:
            # Отправляем первую часть как ответ на оригинальное сообщение
            sent_message = await bot.send_message(
                chat_id=chat_id,
                text=message_parts[0],
                reply_to_message_id=reply_to_message_id,
                parse_mode=ParseMode.HTML
            )
            
            # Отправляем остальные части как обычные сообщения
            for part in message_parts[1:]:
                await asyncio.sleep(0.1)
                await bot.send_message(
                    chat_id=chat_id,
                    text=part,
                    parse_mode=ParseMode.HTML
                )
            
            return sent_message.message_id if sent_message else None
            
        return True
        
    except (TelegramBadRequest, TelegramNetworkError) as e:
        error_str = str(e).lower()
        
        if "can't parse entities" in error_str:
            # Ошибка парсинга HTML - отправляем без форматирования
            logging.warning(f"Ошибка парсинга HTML в ЛС. Отправка обычным текстом. Ошибка: {e}")
            try:
                # Убираем HTML теги из всех частей
                plain_parts = [html.unescape(part) for part in message_parts]
                for part in plain_parts:
                    part = part.replace('<b>', '').replace('</b>', '')
                    part = part.replace('<i>', '').replace('</i>', '')
                    part = part.replace('<code>', '').replace('</code>', '')
                    part = part.replace('<blockquote>', '').replace('</blockquote>', '')
                
                if edit_message_id:
                    await bot.edit_message_text(
                        text=plain_parts[0],
                        chat_id=chat_id,
                        message_id=edit_message_id,
                        parse_mode=None
                    )
                    for part in plain_parts[1:]:
                        await asyncio.sleep(0.1)
                        await bot.send_message(
                            chat_id=chat_id,
                            text=part,
                            parse_mode=None
                        )
                else:
                    sent_message = await bot.send_message(
                        chat_id=chat_id,
                        text=plain_parts[0],
                        reply_to_message_id=reply_to_message_id,
                        parse_mode=None
                    )
                    for part in plain_parts[1:]:
                        await asyncio.sleep(0.1)
                        await bot.send_message(
                            chat_id=chat_id,
                            text=part,
                            parse_mode=None
                        )
                    return sent_message.message_id if sent_message else None
                return True
            except Exception as inner_e:
                logging.error(f"Критическая ошибка при отправке fallback-сообщений в ЛС: {inner_e}")
                return False
        else:
            logging.error(f"Неожиданная ошибка Telegram в ЛС: {e}")
            return False
            
    except Exception as e:
        logging.error(f"Неожиданная ошибка при отправке сообщения в ЛС: {e}")
        return False

def validate_prompt(prompt: str) -> tuple[bool, str]:
    """Валидация пользовательского ввода"""
    if not prompt or not prompt.strip():
        return False, "❌ Пустой запрос. Напишите что-нибудь после .ai/.ии"
    
    if len(prompt) > 1000:
        return False, "❌ Запрос слишком длинный. Максимум 1000 символов."
    
    suspicious_patterns = ['system:', 'override:', 'ignore previous', 'new instructions']
    if any(pattern in prompt.lower() for pattern in suspicious_patterns):
        return False, "❌ Подозрительный запрос отклонен."
    
    return True, ""

async def check_private_limits(message: Message) -> bool:
    """Проверяет лимиты пользователя для ЛС"""
    user_id = message.from_user.id
    
    requests_today = await db.get_user_requests_count(user_id)
    if requests_today is None:
        await db.add_or_update_user(
            user_id, 
            message.from_user.username, 
            message.from_user.first_name
        )
        requests_today = 0
        
    if requests_today >= settings.daily_request_limit:
        await send_safe_private_message(
            message.bot, 
            message.chat.id, 
            Errors.daily_limit_reached,
            reply_to_message_id=message.message_id
        )
        return False
    return True

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
    
    logging.info(f"Обработка .ai/.ии команды в ЛС от пользователя {user_id}")
    
    # Проверяем лимиты
    if not await check_private_limits(message):
        return

    # Извлекаем промпт после команды
    if message_text.lower().startswith(".ии"):
        prompt = message_text[3:].strip()
    else:
        prompt = message_text[3:].strip()
    
    # Валидируем промпт
    is_valid, error_message = validate_prompt(prompt)
    if not is_valid:
        await send_safe_private_message(
            bot, chat_id, error_message,
            reply_to_message_id=message.message_id
        )
        return

    # Показываем статус генерации с жирным форматированием
    user_name = message.from_user.first_name or "Пользователь"
    safe_prompt_preview = html.escape(prompt[:50])
    status_text = f'<b>⏳ Генерируется ответ для запроса "{safe_prompt_preview}..."</b>'
    
    status_message_id = await send_safe_private_message(
        bot, chat_id,
        status_text,
        reply_to_message_id=message.message_id
    )
    
    if not status_message_id:
        logging.error("Не удалось показать статус генерации в ЛС")
        return

    try:
        # Для ЛС используем персональные стили пользователя
        active_style_prompt = await db.get_active_style_prompt(user_id)
        
        logging.info(f"Генерация текста для ЛС, пользователь {user_id}: {prompt[:50]}")
        response = await g4f_api_service.generate_text(
            prompt=prompt, 
            system_prompt=active_style_prompt or ""
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
        success = await send_safe_private_message(
            bot, chat_id, final_text,
            edit_message_id=status_message_id
        )
        
        if success:
            await db.increment_user_requests(user_id, 'text')
            logging.info(f"✅ Успешно обработан .ai/.ии запрос в ЛС от пользователя {user_id}")
        else:
            logging.error("Не удалось отредактировать сообщение с финальным ответом в ЛС")
            
    except Exception as e:
        logging.error(f"Ошибка в handle_private_message: {e}")
        await send_safe_private_message(
            bot, chat_id,
            "<b>❌ Произошла ошибка при генерации ответа. Попробуйте позже.</b>",
            edit_message_id=status_message_id
        )