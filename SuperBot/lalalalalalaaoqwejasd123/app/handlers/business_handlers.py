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
from app.utils import format_final_message_html, format_ai_response_to_html, split_long_message
from config import settings
from messages import Errors

router = Router()

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
        except Exception as e:
            logging.warning(f"Ошибка создания entity: {e}")
            continue
    
    return telegram_entities if telegram_entities else None

async def send_safe_message(bot: Bot, chat_id: int, text: str, 
                          business_connection_id: str = None, 
                          message_id: int = None, 
                          edit: bool = False,
                          entities: list = None) -> bool:
    """Безопасная отправка сообщений с HTML-парсингом и разделением длинных сообщений."""
    
    # Разделяем длинное сообщение на части
    message_parts = split_long_message(text)
    
    try:
        # Если есть entities, используем их для первой части
        if entities and not edit:
            try:
                telegram_entities = convert_entities_to_telegram_entities(entities)
                if telegram_entities:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message_parts[0],
                        business_connection_id=business_connection_id,
                        entities=telegram_entities,
                        parse_mode=None
                    )
                    
                    # Отправляем остальные части с HTML
                    for part in message_parts[1:]:
                        await asyncio.sleep(0.1)
                        await bot.send_message(
                            chat_id=chat_id,
                            text=part,
                            business_connection_id=business_connection_id,
                            parse_mode=ParseMode.HTML
                        )
                    return True
            except Exception as e:
                logging.warning(f"Не удалось отправить с entities: {e}, отправляем с HTML")
        
        # Отправляем или редактируем первую часть с HTML
        if edit and message_id:
            await bot.edit_message_text(
                text=message_parts[0],
                chat_id=chat_id,
                message_id=message_id,
                business_connection_id=business_connection_id,
                parse_mode=ParseMode.HTML
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=message_parts[0],
                business_connection_id=business_connection_id,
                parse_mode=ParseMode.HTML
            )
        
        # Отправляем остальные части как новые сообщения
        for part in message_parts[1:]:
            await asyncio.sleep(0.1)  # Небольшая задержка между сообщениями
            await bot.send_message(
                chat_id=chat_id,
                text=part,
                business_connection_id=business_connection_id,
                parse_mode=ParseMode.HTML
            )
            
        return True
        
    except (TelegramBadRequest, TelegramNetworkError) as e:
        error_str = str(e).lower()
                
        if "message_id_invalid" in error_str:
            # Неверный ID сообщения - отправляем все части как новые сообщения
            logging.warning("Неверный message_id, отправляем новые сообщения")
            try:
                for i, part in enumerate(message_parts):
                    if i > 0:
                        await asyncio.sleep(0.1)
                    await bot.send_message(
                        chat_id=chat_id,
                        text=part,
                        business_connection_id=business_connection_id,
                        parse_mode=ParseMode.HTML
                    )
                return True
            except Exception as inner_e:
                logging.error(f"Не удалось отправить новые сообщения: {inner_e}")
                return False
                
        elif "can't parse entities" in error_str:
            # Ошибка парсинга HTML - отправляем без форматирования
            logging.warning(f"Ошибка парсинга HTML. Отправка обычным текстом. Ошибка: {e}")
            try:
                # Убираем HTML теги из всех частей
                plain_parts = [re.sub('<[^<]+?>', '', part) for part in message_parts]
                
                if edit and message_id:
                    await bot.edit_message_text(
                        text=plain_parts[0],
                        chat_id=chat_id,
                        message_id=message_id,
                        business_connection_id=business_connection_id,
                        parse_mode=None
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=plain_parts[0],
                        business_connection_id=business_connection_id,
                        parse_mode=None
                    )
                
                # Отправляем остальные части
                for part in plain_parts[1:]:
                    await asyncio.sleep(0.1)
                    await bot.send_message(
                        chat_id=chat_id,
                        text=part,
                        business_connection_id=business_connection_id,
                        parse_mode=None
                    )
                return True
            except Exception as inner_e:
                logging.error(f"Критическая ошибка при отправке fallback-сообщений: {inner_e}")
                return False
        else:
            logging.error(f"Неожиданная ошибка Telegram: {e}")
            return False
            
    except Exception as e:
        logging.error(f"Неожиданная ошибка при отправке сообщения: {e}")
        return False

async def run_demo_animation(message: Message, bot: Bot, demo_responses: list, entities: list = None) -> bool:
    """
    Выполняет анимированную демонстрацию, редактируя исходное сообщение.
    Поддерживает форматирование HTML в ответах и разделение длинных сообщений.
    """
    try:
        if not demo_responses:
            return False
            
        logging.info(f"Запуск анимации для пользователя {message.from_user.id} с {len(demo_responses)} этапами")
        
        # Редактируем исходное сообщение на первый ответ
        first_response = demo_responses[0]
        
        # Если есть entities, используем их для первого сообщения
        if entities:
            try:
                telegram_entities = convert_entities_to_telegram_entities(entities)
                if telegram_entities:
                    await bot.edit_message_text(
                        text=first_response,
                        chat_id=message.chat.id,
                        message_id=message.message_id,
                        business_connection_id=message.business_connection_id,
                        entities=telegram_entities,
                        parse_mode=None
                    )
                else:
                    raise ValueError("Не удалось конвертировать entities")
            except Exception as e:
                logging.warning(f"Не удалось использовать entities для первого этапа: {e}")
                formatted_response = format_ai_response_to_html(first_response)
                success = await send_safe_message(
                    bot, message.chat.id,
                    formatted_response,
                    message.business_connection_id,
                    message.message_id,
                    edit=True
                )
                if not success:
                    logging.error("Не удалось отправить первый этап анимации")
                    return False
        else:
            formatted_response = format_ai_response_to_html(first_response)
            success = await send_safe_message(
                bot, message.chat.id,
                formatted_response,
                message.business_connection_id,
                message.message_id,
                edit=True
            )
            if not success:
                logging.error("Не удалось отправить первый этап анимации")
                return False
        
        # Анимация остальных этапов с задержкой
        for i, response_text in enumerate(demo_responses[1:], 1):
            await asyncio.sleep(1.0)  # Задержка между этапами
            formatted_response = format_ai_response_to_html(response_text)
            
            success = await send_safe_message(
                bot, message.chat.id,
                formatted_response,
                message.business_connection_id,
                message.message_id,
                edit=True
            )
            
            if success:
                logging.info(f"Этап анимации {i+1}/{len(demo_responses)} выполнен")
            else:
                logging.warning(f"Ошибка этапа анимации {i+1}")
        
        return True
        
    except Exception as e:
        logging.error(f"Ошибка выполнения демо-анимации: {e}")
        return False

async def run_simple_demo(message: Message, bot: Bot, demo_response: str, entities: list = None) -> bool:
    """
    Выполняет простую демонстрацию без анимации.
    Поддерживает форматирование HTML в ответе и разделение длинных сообщений.
    """
    try:
        logging.info(f"Запуск простого демо для пользователя {message.from_user.id}")
        
        # Если есть entities, используем их
        if entities:
            try:
                telegram_entities = convert_entities_to_telegram_entities(entities)
                if telegram_entities:
                    await bot.edit_message_text(
                        text=demo_response,
                        chat_id=message.chat.id,
                        message_id=message.message_id,
                        business_connection_id=message.business_connection_id,
                        entities=telegram_entities,
                        parse_mode=None
                    )
                    logging.info("Простое демо с entities успешно выполнено")
                    return True
                else:
                    raise ValueError("Не удалось конвертировать entities")
            except Exception as e:
                logging.warning(f"Не удалось использовать entities: {e}")
        
        # Форматируем ответ с поддержкой HTML
        formatted_response = format_ai_response_to_html(demo_response)
        
        success = await send_safe_message(
            bot, message.chat.id,
            formatted_response,
            message.business_connection_id,
            message.message_id,
            edit=True
        )
        
        if success:
            logging.info("Простое демо успешно выполнено")
            return True
        else:
            logging.error("Не удалось выполнить простое демо")
            return False
        
    except Exception as e:
        logging.error(f"Ошибка выполнения простого демо: {e}")
        return False

async def check_limits(message: Message) -> bool:
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
        await send_safe_message(
            message.bot, 
            message.chat.id, 
            Errors.daily_limit_reached,
            message.business_connection_id,
            message.message_id,
            edit=True
        )
        return False
    return True

def validate_prompt(prompt: str) -> tuple[bool, str]:
    """Валидация пользовательского ввода"""
    if not prompt or not prompt.strip():
        return False, "❌ Пустой запрос. Напишите что-нибудь после .ai"
    
    if len(prompt) > 1000:
        return False, "❌ Запрос слишком длинный. Максимум 1000 символов."
    
    suspicious_patterns = ['system:', 'override:', 'ignore previous', 'new instructions']
    if any(pattern in prompt.lower() for pattern in suspicious_patterns):
        return False, "❌ Подозрительный запрос отклонен."
    
    return True, ""

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
    logging.info(f"Проверка демо-триггера для пользователя {user_id}: '{message_text}'")
    demo_result = await db.get_demo_trigger(user_id, message_text)
    
    if demo_result:
        demo_responses, is_animated, entities = demo_result  # ИСПРАВЛЕНО: правильная распаковка
        logging.info(f"✅ Найден {'анимированный' if is_animated else 'простой'} демо-триггер для пользователя {user_id}")
        
        if is_animated:
            # Анимированное демо
            success = await run_demo_animation(message, bot, demo_responses, entities)
        else:
            # Простое демо (берем первый элемент из списка)
            success = await run_simple_demo(message, bot, demo_responses[0], entities)
            
        if success:
            logging.info(f"✅ Демо завершено для пользователя {user_id}")
        else:
            logging.error(f"❌ Ошибка демо для пользователя {user_id}")
        return
    
    # 2. Проверяем команду .ai или .ии только если НЕ найден демо-триггер
    if not (message_text.lower().startswith(".ai") or message_text.lower().startswith(".ии")):
        return
    
    logging.info(f"Обработка .ai/.ии команды от пользователя {user_id}")
    
    # Проверяем лимиты
    if not await check_limits(message):
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
        
        logging.info(f"Генерация текста для пользователя {user_id}: {prompt[:50]}")
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
            logging.info(f"✅ Успешно обработан .ai/.ии запрос пользователя {user_id}")
        else:
            logging.error("Не удалось отправить финальный ответ")
            
    except Exception as e:
        logging.error(f"Ошибка в handle_any_business_message: {e}")
        await send_safe_message(
            bot, message.chat.id,
            "❌ Произошла ошибка при генерации ответа. Попробуйте позже.",
            message.business_connection_id, message.message_id, edit=True
        )