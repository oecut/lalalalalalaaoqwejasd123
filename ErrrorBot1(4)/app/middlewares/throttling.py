# /ErrrorBot/app/middlewares/throttling.py

from typing import Any, Awaitable, Callable, Dict, Union
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery
from cachetools import TTLCache
from aiogram.exceptions import TelegramBadRequest

from messages import Errors
from config import settings

cache = TTLCache(maxsize=10_000, ttl=settings.request_timeout_seconds)

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, cache: TTLCache):
        self.cache = cache

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        if not hasattr(event, 'from_user') or not event.from_user:
             return await handler(event, data)

        user_id = event.from_user.id
        
        if user_id in self.cache:
            if isinstance(event, CallbackQuery):
                await event.answer(Errors.timeout_not_expired, show_alert=True)
            elif isinstance(event, Message) and event.business_connection_id:
                try:
                    bot: Bot = data['bot']
                    await bot.edit_message_text(
                        text=Errors.timeout_not_expired,
                        chat_id=event.chat.id,
                        message_id=event.message_id,
                        business_connection_id=event.business_connection_id,
                        parse_mode=None
                    )
                except (TelegramBadRequest, KeyError):
                    pass
            return

        self.cache[user_id] = None
        
        return await handler(event, data)