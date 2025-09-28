# /ErrrorBot/main.py

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import bot_config
from app.services.database import db
from app.handlers import user_handlers, business_handlers, admin_handlers, group_handlers, private_handlers
from app.middlewares.throttling import ThrottlingMiddleware, cache

async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    
    # Создание папки для базы данных
    db_dir = 'database'
    if not os.path.exists(db_dir): 
        os.makedirs(db_dir)

    # Инициализация базы данных
    await db.initialize()

    # Настройка хранилища состояний
    storage = MemoryStorage()
    
    # Создание бота с HTML-парсером по умолчанию
    bot = Bot(
        token=bot_config.token, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Создание диспетчера
    dp = Dispatcher(storage=storage)

    # Применение middleware для предотвращения спама
    dp.update.middleware(ThrottlingMiddleware(cache=cache))

    # Подключение роутеров (порядок важен!)
    dp.include_router(admin_handlers.router)        # Админские команды (высший приоритет)
    dp.include_router(user_handlers.router)         # Пользовательские команды и меню
    dp.include_router(business_handlers.router)     # Бизнес-сообщения (личные чаты через бизнес)
    dp.include_router(group_handlers.router)        # Групповые чаты
    dp.include_router(private_handlers.router)      # Личные чаты бота (последний приоритет)

    # Удаление вебхука если есть
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        logging.info("👾 Запуск бота...")
        await dp.start_polling(bot)
    finally:
        logging.info("⛔ Остановка бота...")
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Бот остановлен вручную.")