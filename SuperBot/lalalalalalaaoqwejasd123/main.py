#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной файл запуска Telegram бота GDPBoost
Высокопроизводительный бот с поддержкой 100k+ пользователей
"""

import asyncio
import logging
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

# Настройка логирования для высокой производительности
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Подавляем лишние логи для производительности
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

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
        logger.info("🔧 Регистрация хэндлеров...")
        
        # Регистрируем роутеры в правильном порядке
        self.dp.include_routers(
            admin_handlers.router,      # Админские команды - высший приоритет
            user_handlers.router,       # Пользовательские команды 
            business_handlers.router,   # Business чаты
            group_handlers.router,      # Групповые чаты
            private_handlers.router     # Приватные сообщения - последний
        )
        
        logger.info("✅ Хэндлеры зарегистрированы")
    
    def _setup_shutdown_handler(self):
        """Настройка корректного завершения работы"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Получен сигнал {signum}, завершение работы...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def startup(self):
        """Инициализация бота"""
        logger.info("🚀 Запуск GDPBoost Bot...")
        
        try:
            # Инициализация базы данных
            logger.info("📊 Инициализация базы данных...")
            await db.initialize()
            logger.info("✅ База данных инициализирована")
            
            # Проверка подключения к Telegram
            bot_info = await self.bot.get_me()
            logger.info(f"🤖 Бот запущен: @{bot_info.username} ({bot_info.full_name})")
            logger.info(f"🔧 ID бота: {bot_info.id}")
            
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
                except Exception as e:
                    logger.warning(f"Не удалось уведомить админа {admin_id}: {e}")
            
            logger.info("🎯 Бот готов к работе!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {e}")
            raise
    
    async def shutdown(self):
        """Корректное завершение работы"""
        logger.info("🛑 Завершение работы бота...")
        
        try:
            # Закрываем соединение с базой данных
            await db.close()
            logger.info("✅ База данных закрыта")
            
            # Закрываем сессию бота
            await self.bot.session.close()
            logger.info("✅ Сессия бота закрыта")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при завершении: {e}")
        
        logger.info("🔚 Бот остановлен")
    
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
            logger.error(f"❌ Критическая ошибка в основном цикле: {e}")
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
        logger.info("🛑 Получен сигнал прерывания")
    except Exception as e:
        logger.error(f"❌ Необработанная ошибка: {e}")
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
        logger.info("🔚 Программа завершена пользователем")
    except Exception as e:
        logger.error(f"❌ Фатальная ошибка: {e}")
        sys.exit(1)