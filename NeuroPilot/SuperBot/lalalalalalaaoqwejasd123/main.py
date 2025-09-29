#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной файл запуска Telegram бота GDPBoost
Высокопроизводительный бот с поддержкой 100k+ пользователей
"""

import asyncio
import signal
import sys
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Локальные импорты
from config import bot_config, settings
from app.services.database import db
from app.middlewares.throttling import ThrottlingMiddleware

# Хэндлеры
from app.handlers import private_handlers, group_handlers, admin_handlers, user_handlers, business_handlers


class HighPerformanceBot:
    """Высокопроизводительный бот для 100k+ пользователей"""
    
    def __init__(self):
        # Создаем бота с оптимальными настройками
        self.bot = Bot(
            token=bot_config.token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                link_preview_is_disabled=True,
                protect_content=False
            )
        )
        
        # Диспетчер с MemoryStorage для максимальной скорости
        self.dp = Dispatcher(storage=MemoryStorage())
        
        # Добавляем middleware для защиты от спама
        self.dp.message.middleware(ThrottlingMiddleware())
        
        self._setup_handlers()
        self._setup_shutdown_handler()
    
    def _setup_handlers(self):
        """Регистрация всех хэндлеров"""
        
        # Регистрируем роутеры в правильном порядке
        self.dp.include_routers(
            admin_handlers.router,      # Админские команды - высший приоритет
            user_handlers.router,       # Пользовательские команды 
            business_handlers.router,   # Business чаты
            group_handlers.router,      # Групповые чаты
            private_handlers.router     # Приватные сообщения - последний
        )
        
    
    def _setup_shutdown_handler(self):
        """Настройка корректного завершения работы"""
        def signal_handler(signum, frame):
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def startup(self):
        """Инициализация бота"""
        
        try:
            # Инициализация базы данных
            await db.initialize()
            
            # Проверка подключения к Telegram
            bot_info = await self.bot.get_me()
            
            # Уведомляем админов о запуске
            for admin_id in bot_config.admin_ids:
                try:
                    await self.bot.send_message(
                        admin_id,
                        "🚀 <b>GDPBoost Bot успешно запущен!</b>\n\n"
                        f"🤖 Бот: @{bot_info.username}\n"
                        f"⚡ Режим: Высокая производительность\n"
                        f"👥 Готов к обслуживанию 100k+ пользователей",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
            
            
        except Exception as e:
            raise
    
    async def shutdown(self):
        """Корректное завершение работы"""
        
        try:
            # Закрываем соединение с базой данных
            await db.close()
            
            # Закрываем сессию бота
            await self.bot.session.close()
            
        except Exception:
            pass
        
    
    async def run(self):
        """Основной цикл работы бота"""
        try:
            await self.startup()
            
            # Запускаем polling с оптимальными настройками для высокой нагрузки
            await self.dp.start_polling(
                self.bot,
                allowed_updates=[
                    "message", 
                    "callback_query", 
                    "my_chat_member",
                    "chat_member"
                ],
                drop_pending_updates=True  # Игнорируем старые сообщения
            )
            
        except Exception as e:
            raise
        finally:
            await self.shutdown()

@asynccontextmanager
async def lifespan():
    """Контекстный менеджер жизненного цикла приложения"""
    bot_instance = HighPerformanceBot()
    try:
        yield bot_instance
    finally:
        await bot_instance.shutdown()

async def main():
    """Основная функция запуска"""
    try:
        async with lifespan() as bot_instance:
            await bot_instance.run()
    except KeyboardInterrupt:
        pass
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    # Проверяем Python версию
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        sys.exit(1)
    
    # Устанавливаем политику event loop для Windows
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        sys.exit(1)