# /ErrrorBot/app/handlers/common_handlers.py

from aiogram import Bot
from aiogram.types import Message, MessageEntity
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.enums import ParseMode
import asyncio
import html
import re
from typing import Union, Optional

from app.services.database import db
from app.utils import format_ai_response_to_html, split_long_message
from config import settings
from messages import Errors


def convert_entities_to_telegram_entities(entities):
    """Конвертирует сохраненные entities обратно в формат Telegram"""
    if not entities:
        return None
    
    telegram_entities = []
    for entity_dict in entities:
        try:
            # Создаем MessageEntity из словаря
            entity = MessageEntity(
                type=entity_dict['type'],
                offset=entity_dict['offset'],
                length=entity_dict['length']
            )
            
            # Добавляем дополнительные поля если есть
            if 'url' in entity_dict:
                entity.url = entity_dict['url']
            if 'user_id' in entity_dict:
                # Создаем фиктивный User объект если нужно
                from aiogram.types import User
                entity.user = User(id=entity_dict['user_id'], is_bot=False, first_name="User")
            if 'language' in entity_dict:
                entity.language = entity_dict['language']
                
            telegram_entities.append(entity)
        except Exception:
            continue
    
    return telegram_entities if telegram_entities else None


async def send_safe_message(bot: Bot, chat_id: int, text: str, 
                          business_connection_id: str = None, 
                          message_id: int = None, 
                          edit: bool = False,
                          entities: list = None,
                          reply_to_message_id: int = None) -> Union[bool, int]:
    """Универсальная безопасная отправка сообщений с HTML-парсингом и разделением длинных сообщений."""
    
    # Разделяем длинное сообщение на части
    message_parts = split_long_message(text)
    
    try:
        # Если есть entities, используем их для первой части
        if entities and not edit:
            try:
                telegram_entities = convert_entities_to_telegram_entities(entities)
                if telegram_entities:
                    if business_connection_id:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=message_parts[0],
                            business_connection_id=business_connection_id,
                            entities=telegram_entities,
                            parse_mode=None
                        )
                    else:
                        sent_message = await bot.send_message(
                            chat_id=chat_id,
                            text=message_parts[0],
                            reply_to_message_id=reply_to_message_id,
                            entities=telegram_entities,
                            parse_mode=None
                        )
                        message_id = sent_message.message_id
                    
                    # Отправляем остальные части с HTML
                    for part in message_parts[1:]:
                        await asyncio.sleep(0.1)
                        if business_connection_id:
                            await bot.send_message(
                                chat_id=chat_id,
                                text=part,
                                business_connection_id=business_connection_id,
                                parse_mode=ParseMode.HTML
                            )
                        else:
                            await bot.send_message(
                                chat_id=chat_id,
                                text=part,
                                parse_mode=ParseMode.HTML
                            )
                    return True if business_connection_id else message_id
            except Exception:
                pass
        
        # Отправляем или редактируем первую часть с HTML
        if edit and message_id:
            if business_connection_id:
                await bot.edit_message_text(
                    text=message_parts[0],
                    chat_id=chat_id,
                    message_id=message_id,
                    business_connection_id=business_connection_id,
                    parse_mode=ParseMode.HTML
                )
            else:
                await bot.edit_message_text(
                    text=message_parts[0],
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode=ParseMode.HTML
                )
        else:
            if business_connection_id:
                await bot.send_message(
                    chat_id=chat_id,
                    text=message_parts[0],
                    business_connection_id=business_connection_id,
                    parse_mode=ParseMode.HTML
                )
            else:
                sent_message = await bot.send_message(
                    chat_id=chat_id,
                    text=message_parts[0],
                    reply_to_message_id=reply_to_message_id,
                    parse_mode=ParseMode.HTML
                )
                message_id = sent_message.message_id if sent_message else None
        
        # Отправляем остальные части как новые сообщения
        for part in message_parts[1:]:
            await asyncio.sleep(0.1)
            if business_connection_id:
                await bot.send_message(
                    chat_id=chat_id,
                    text=part,
                    business_connection_id=business_connection_id,
                    parse_mode=ParseMode.HTML
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=part,
                    parse_mode=ParseMode.HTML
                )
            
        return True if business_connection_id else message_id
        
    except (TelegramBadRequest, TelegramNetworkError) as e:
        error_str = str(e).lower()
                
        if "message_id_invalid" in error_str:
            # Неверный ID сообщения - отправляем все части как новые сообщения
            try:
                sent_message = None
                for i, part in enumerate(message_parts):
                    if i > 0:
                        await asyncio.sleep(0.1)
                    if business_connection_id:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=part,
                            business_connection_id=business_connection_id,
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        if i == 0:
                            sent_message = await bot.send_message(
                                chat_id=chat_id,
                                text=part,
                                reply_to_message_id=reply_to_message_id,
                                parse_mode=ParseMode.HTML
                            )
                        else:
                            await bot.send_message(
                                chat_id=chat_id,
                                text=part,
                                parse_mode=ParseMode.HTML
                            )
                return True if business_connection_id else (sent_message.message_id if sent_message else None)
            except Exception:
                return False
                
        elif "can't parse entities" in error_str:
            # Ошибка парсинга HTML - отправляем без форматирования
            try:
                # Убираем HTML теги из всех частей
                plain_parts = [re.sub('<[^<]+?>', '', part) for part in message_parts]
                
                if edit and message_id:
                    if business_connection_id:
                        await bot.edit_message_text(
                            text=plain_parts[0],
                            chat_id=chat_id,
                            message_id=message_id,
                            business_connection_id=business_connection_id,
                            parse_mode=None
                        )
                    else:
                        await bot.edit_message_text(
                            text=plain_parts[0],
                            chat_id=chat_id,
                            message_id=message_id,
                            parse_mode=None
                        )
                else:
                    if business_connection_id:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=plain_parts[0],
                            business_connection_id=business_connection_id,
                            parse_mode=None
                        )
                    else:
                        sent_message = await bot.send_message(
                            chat_id=chat_id,
                            text=plain_parts[0],
                            reply_to_message_id=reply_to_message_id,
                            parse_mode=None
                        )
                        message_id = sent_message.message_id if sent_message else None
                
                # Отправляем остальные части
                for part in plain_parts[1:]:
                    await asyncio.sleep(0.1)
                    if business_connection_id:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=part,
                            business_connection_id=business_connection_id,
                            parse_mode=None
                        )
                    else:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=part,
                            parse_mode=None
                        )
                return True if business_connection_id else message_id
            except Exception:
                return False
        else:
            return False
            
    except Exception:
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


async def check_user_limits(message: Message) -> bool:
    """Проверяет лимиты пользователя"""
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
        # Определяем тип чата для корректной отправки
        business_connection_id = getattr(message, 'business_connection_id', None)
        reply_to_message_id = None if business_connection_id else message.message_id
        
        await send_safe_message(
            message.bot, 
            message.chat.id, 
            Errors.daily_limit_reached,
            business_connection_id=business_connection_id,
            message_id=message.message_id if business_connection_id else None,
            edit=bool(business_connection_id),
            reply_to_message_id=reply_to_message_id
        )
        return False
    return True


async def run_demo_animation(message: Message, bot: Bot, demo_responses: list, entities: list = None) -> bool:
    """
    Выполняет анимированную демонстрацию, редактируя исходное сообщение.
    Поддерживает форматирование HTML в ответах и разделение длинных сообщений.
    """
    try:
        if not demo_responses:
            return False
            
        # Редактируем исходное сообщение на первый ответ
        first_response = demo_responses[0]
        business_connection_id = getattr(message, 'business_connection_id', None)
        
        # Если есть entities, используем их для первого сообщения
        if entities:
            try:
                telegram_entities = convert_entities_to_telegram_entities(entities)
                if telegram_entities:
                    if business_connection_id:
                        await bot.edit_message_text(
                            text=first_response,
                            chat_id=message.chat.id,
                            message_id=message.message_id,
                            business_connection_id=business_connection_id,
                            entities=telegram_entities,
                            parse_mode=None
                        )
                    else:
                        # Для группы отправляем новое сообщение
                        await bot.send_message(
                            chat_id=message.chat.id,
                            text=first_response,
                            reply_to_message_id=message.message_id,
                            entities=telegram_entities,
                            parse_mode=None
                        )
                else:
                    raise ValueError("Не удалось конвертировать entities")
            except Exception:
                formatted_response = format_ai_response_to_html(first_response)
                success = await send_safe_message(
                    bot, message.chat.id,
                    formatted_response,
                    business_connection_id,
                    message.message_id,
                    edit=bool(business_connection_id),
                    reply_to_message_id=None if business_connection_id else message.message_id
                )
                if not success:
                    return False
        else:
            formatted_response = format_ai_response_to_html(first_response)
            success = await send_safe_message(
                bot, message.chat.id,
                formatted_response,
                business_connection_id,
                message.message_id,
                edit=bool(business_connection_id),
                reply_to_message_id=None if business_connection_id else message.message_id
            )
            if not success:
                return False
        
        # Анимация остальных этапов с задержкой
        for response_text in demo_responses[1:]:
            await asyncio.sleep(1.0)  # Задержка между этапами
            formatted_response = format_ai_response_to_html(response_text)
            
            success = await send_safe_message(
                bot, message.chat.id,
                formatted_response,
                business_connection_id,
                message.message_id,
                edit=True
            )
            
            if not success:
                return False
        
        return True
        
    except Exception:
        return False


async def run_simple_demo(message: Message, bot: Bot, demo_response: str, entities: list = None) -> bool:
    """
    Выполняет простую демонстрацию без анимации.
    Поддерживает форматирование HTML в ответе и разделение длинных сообщений.
    """
    try:
        business_connection_id = getattr(message, 'business_connection_id', None)
        
        # Если есть entities, используем их
        if entities:
            try:
                telegram_entities = convert_entities_to_telegram_entities(entities)
                if telegram_entities:
                    if business_connection_id:
                        await bot.edit_message_text(
                            text=demo_response,
                            chat_id=message.chat.id,
                            message_id=message.message_id,
                            business_connection_id=business_connection_id,
                            entities=telegram_entities,
                            parse_mode=None
                        )
                    else:
                        await bot.send_message(
                            chat_id=message.chat.id,
                            text=demo_response,
                            reply_to_message_id=message.message_id,
                            entities=telegram_entities,
                            parse_mode=None
                        )
                    return True
                else:
                    raise ValueError("Не удалось конвертировать entities")
            except Exception:
                pass
        
        # Форматируем ответ с поддержкой HTML
        formatted_response = format_ai_response_to_html(demo_response)
        
        success = await send_safe_message(
            bot, message.chat.id,
            formatted_response,
            business_connection_id,
            message.message_id,
            edit=bool(business_connection_id),
            reply_to_message_id=None if business_connection_id else message.message_id
        )
        
        return bool(success)
        
    except Exception:
        return False


def format_quoted_message(user_name: str, original_text: str, ai_response: str) -> str:
    """Форматирует сообщение с цитатой пользователя и ответом ИИ"""
    safe_user_name = html.escape(user_name or "Пользователь")
    safe_original_text = html.escape(original_text or "")
    formatted_ai_response = format_ai_response_to_html(ai_response)
    
    return (
        f"<blockquote>{safe_user_name}: {safe_original_text}</blockquote>\n\n"
        f"💬 <b>{formatted_ai_response}</b>"
    )