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
from app.utils import format_ai_response_to_html, split_long_message
from config import settings
from messages import Errors

router = Router()

def convert_entities_to_telegram_entities(entities):
    """Конвертирует сохраненные entities обратно в формат Telegram"""
    if not entities:
        return None
    
    telegram_entities = []
    for entity_dict in entities:
        from aiogram.types import MessageEntity
        
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
    
    return telegram_entities

async def send_safe_group_message(bot: Bot, chat_id: int, text: str, 
                                 reply_to_message_id: int = None,
                                 edit_message_id: int = None) -> bool:
    """Безопасная отправка сообщений в группу с HTML-парсингом и разделением длинных сообщений."""
    
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
            logging.warning(f"Ошибка парсинга HTML в группе. Отправка обычным текстом. Ошибка: {e}")
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
                logging.error(f"Критическая ошибка при отправке fallback-сообщений в группу: {inner_e}")
                return False
        else:
            logging.error(f"Неожиданная ошибка Telegram в группе: {e}")
            return False
            
    except Exception as e:
        logging.error(f"Неожиданная ошибка при отправке сообщения в группу: {e}")
        return False

async def run_demo_animation_group(message: Message, bot: Bot, demo_responses: list, entities: list = None) -> bool:
    """
    Выполняет анимированную демонстрацию в группе, отправляя новые сообщения.
    Поддерживает сохранение entities (спойлеры, курсив и т.д.).
    """
    try:
        if not demo_responses:
            return False
            
        logging.info(f"Запуск групповой анимации для пользователя {message.from_user.id} с {len(demo_responses)} этапами")
        
        # Отправляем первое сообщение как ответ на команду
        first_response = demo_responses[0]
        
        # Если есть entities, используем их для первого сообщения
        if entities:
            try:
                # Конвертируем entities обратно в формат Telegram
                telegram_entities = convert_entities_to_telegram_entities(entities)
                sent_message = await bot.send_message(
                    chat_id=message.chat.id,
                    text=first_response,
                    reply_to_message_id=message.message_id,
                    entities=telegram_entities,
                    parse_mode=None
                )
                message_id = sent_message.message_id
            except Exception as e:
                logging.warning(f"Не удалось отправить с entities: {e}, отправляем с HTML")
                formatted_response = format_ai_response_to_html(first_response)
                message_id = await send_safe_group_message(
                    bot, message.chat.id, formatted_response,
                    reply_to_message_id=message.message_id
                )
        else:
            formatted_response = format_ai_response_to_html(first_response)
            message_id = await send_safe_group_message(
                bot, message.chat.id, formatted_response,
                reply_to_message_id=message.message_id
            )
        
        if not message_id:
            logging.error("Не удалось отправить первый этап анимации")
            return False
        
        # Анимация остальных этапов с задержкой
        for i, response_text in enumerate(demo_responses[1:], 1):
            await asyncio.sleep(1.0)  # Задержка между этапами
            formatted_response = format_ai_response_to_html(response_text)
            
            success = await send_safe_group_message(
                bot, message.chat.id, formatted_response,
                edit_message_id=message_id
            )
            
            if success:
                logging.info(f"Этап групповой анимации {i+1}/{len(demo_responses)} выполнен")
            else:
                logging.warning(f"Ошибка этапа групповой анимации {i+1}")
        
        return True
        
    except Exception as e:
        logging.error(f"Ошибка выполнения групповой демо-анимации: {e}")
        return False

async def run_simple_demo_group(message: Message, bot: Bot, demo_response: str, entities: list = None) -> bool:
    """
    Выполняет простую демонстрацию в группе без анимации.
    Поддерживает сохранение entities.
    """
    try:
        logging.info(f"Запуск простого группового демо для пользователя {message.from_user.id}")
        
        # Если есть entities, используем их
        if entities:
            try:
                telegram_entities = convert_entities_to_telegram_entities(entities)
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=demo_response,
                    reply_to_message_id=message.message_id,
                    entities=telegram_entities,
                    parse_mode=None
                )
                logging.info("Простое групповое демо с entities успешно выполнено")
                return True
            except Exception as e:
                logging.warning(f"Не удалось отправить с entities: {e}, отправляем с HTML")
        
        # Форматируем ответ с поддержкой HTML
        formatted_response = format_ai_response_to_html(demo_response)
        
        success = await send_safe_group_message(
            bot, message.chat.id, formatted_response,
            reply_to_message_id=message.message_id
        )
        
        if success:
            logging.info("Простое групповое демо успешно выполнено")
            return True
        else:
            logging.error("Не удалось выполнить простое групповое демо")
            return False
        
    except Exception as e:
        logging.error(f"Ошибка выполнения простого группового демо: {e}")
        return False

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

async def check_group_limits(message: Message) -> bool:
    """Проверяет лимиты пользователя для группового чата"""
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
        await send_safe_group_message(
            message.bot, 
            message.chat.id, 
            Errors.daily_limit_reached,
            reply_to_message_id=message.message_id
        )
        return False
    return True

def format_quoted_message(user_name: str, original_text: str, ai_response: str) -> str:
    """Форматирует сообщение с цитатой пользователя и ответом ИИ"""
    safe_user_name = html.escape(user_name or "Пользователь")
    safe_original_text = html.escape(original_text or "")
    formatted_ai_response = format_ai_response_to_html(ai_response)
    
    return (
        f"<blockquote>{safe_user_name}: {safe_original_text}</blockquote>\n\n"
        f"💬 <b>{formatted_ai_response}</b>"
    )

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
    logging.info(f"Проверка демо-триггера в группе для пользователя {user_id}: '{message_text}'")
    demo_result = await db.get_demo_trigger(user_id, message_text)
    
    if demo_result:
        demo_responses, is_animated, entities = demo_result
        logging.info(f"✅ Найден {'анимированный' if is_animated else 'простой'} демо-триггер в группе для пользователя {user_id}")
        
        if is_animated:
            # Анимированное демо
            success = await run_demo_animation_group(message, bot, demo_responses, entities)
        else:
            # Простое демо (берем первый элемент из списка)
            success = await run_simple_demo_group(message, bot, demo_responses[0], entities)
            
        if success:
            logging.info(f"✅ Групповое демо завершено для пользователя {user_id}")
        else:
            logging.error(f"❌ Ошибка группового демо для пользователя {user_id}")
        return
    
    # 2. Проверяем команды .ai или .ии только если НЕ найден демо-триггер
    if not (message_text.lower().startswith(".ai") or message_text.lower().startswith(".ии")):
        return
    
    logging.info(f"Обработка .ai/.ии команды в группе {chat_id} от пользователя {user_id}")
    
    # Проверяем лимиты
    if not await check_group_limits(message):
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
                
            logging.info(f"Ответ на сообщение пользователя {replied_message.from_user.id} в группе {chat_id}")
            
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
                
            logging.info(f"Ответ на сообщение бота в группе {chat_id}")
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
    
    status_message_id = await send_safe_group_message(
        bot, chat_id,
        status_text,
        reply_to_message_id=message.message_id
    )
    
    if not status_message_id:
        logging.error("Не удалось показать статус генерации в группе")
        return

    try:
        # Получаем активный стиль для группы
        active_style_prompt = await db.get_active_group_style_prompt(chat_id)
        
        logging.info(f"Генерация текста для группы {chat_id}, пользователь {user_id}: {full_prompt[:50]}")
        response = await g4f_api_service.generate_text(
            prompt=full_prompt, 
            system_prompt=active_style_prompt
        )
        
        if len(response.strip()) < 10:
            response = "Получен слишком короткий ответ. Попробуйте перефразировать запрос."
        
        # Форматируем финальный ответ в стиле группового чата
        final_text = format_quoted_message(original_user_name, context_text, response)
        
        # Редактируем статусное сообщение с финальным ответом
        success = await send_safe_group_message(
            bot, chat_id, final_text,
            edit_message_id=status_message_id
        )
        
        if success:
            await db.increment_user_requests(user_id, 'text')
            logging.info(f"✅ Успешно обработан .ai запрос в группе {chat_id} от пользователя {user_id}")
        else:
            logging.error("Не удалось отредактировать сообщение с финальным ответом")
            
    except Exception as e:
        logging.error(f"Ошибка в handle_group_message: {e}")
        await send_safe_group_message(
            bot, chat_id,
            "<b>❌ Произошла ошибка при генерации ответа. Попробуйте позже.</b>",
            edit_message_id=status_message_id
        )