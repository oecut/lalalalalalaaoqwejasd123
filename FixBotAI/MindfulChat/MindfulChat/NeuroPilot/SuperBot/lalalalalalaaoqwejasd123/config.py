# /ErrrorBot/config.py

from dataclasses import dataclass, field
from typing import List

try:
    from keys import BOT_TOKEN, ADMIN_IDS
except ImportError:
    raise ImportError("Файл keys.py не найден или не содержит необходимые переменные: BOT_TOKEN, ADMIN_IDS")

@dataclass(frozen=True)
class BotConfig:
    """Конфигурация бота"""
    token: str = BOT_TOKEN or 'YOUR_BOT_TOKEN_HERE'
    admin_ids: List[int] = field(default_factory=lambda: ADMIN_IDS)

@dataclass(frozen=True)
class Settings:
    """Общие настройки приложения"""
    daily_request_limit: int = 100
    request_timeout_seconds: int = 10
    # Лимит токенов для генерации (предотвращает слишком длинные ответы)
    max_tokens: int = 1000

# Создаем неизменяемые экземпляры конфигураций для импорта в другие части приложения.
bot_config = BotConfig()
settings = Settings()