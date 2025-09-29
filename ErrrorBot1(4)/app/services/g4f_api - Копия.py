# /ErrrorBot/app/services/g4f_api.py

import asyncio
import logging
from typing import Optional
import re

# Импортируем g4f компоненты
try:
    import g4f
    from g4f import ChatCompletion, Provider
    from g4f.client import Client
    G4F_AVAILABLE = True
except ImportError:
    G4F_AVAILABLE = False
    logging.error("g4f не установлен. Установите: pip install -U g4f")

from config import settings

class G4FAPI:
    def __init__(self):
        """Обновленный сервис для работы с g4f с актуальными провайдерами"""
        self.max_tokens = settings.max_tokens
        logging.info(f"Инициализация G4F API (лимит токенов: {self.max_tokens})")
        
        if not G4F_AVAILABLE:
            logging.error("G4F недоступен!")

    def _clean_response(self, text: str) -> str:
        """Очищает и форматирует ответ от ИИ"""
        if not text:
            return ""
            
        # Убираем лишние пробелы и переносы строк
        text = text.strip()
        
        # Убираем двойные переносы строк, которые вызывают проблемы форматирования
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Убираем лишние пробелы
        text = re.sub(r' +', ' ', text)
        
        # Исправляем проблему с двойными символами в конце
        text = re.sub(r'(.)\1{2,}$', r'\1', text)
        
        return text

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Генерирует текстовый ответ с использованием актуальных провайдеров g4f"""
        
        if not G4F_AVAILABLE:
            return "❌ Критическая ошибка модуля генерации. Обратитесь к администратору."
        
        # Подготавливаем сообщения
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Обновленный список рабочих стратегий
        strategies = [
            # Стратегия 1: Новый Client API без указания модели (автовыбор)
            {
                'name': 'Client API - Auto Model',
                'method': lambda: Client().chat.completions.create(
                    model="",  # Пустая строка для автовыбора
                    messages=messages,
                    max_tokens=self.max_tokens
                )
            },
            
            # Стратегия 2: Client API с gpt-4
            {
                'name': 'Client API - GPT-4',
                'method': lambda: Client().chat.completions.create(
                    model="gpt-4",
                    messages=messages
                )
            },
            
            # Стратегия 3: Client API с gpt-3.5-turbo
            {
                'name': 'Client API - GPT-3.5-turbo',
                'method': lambda: Client().chat.completions.create(
                    model="gpt-3.5-turbo", 
                    messages=messages
                )
            },
            
            # Стратегия 4: Legacy ChatCompletion с автовыбором провайдера
            {
                'name': 'ChatCompletion - Auto Provider',
                'method': lambda: ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    provider=g4f.Provider.Auto
                )
            },
            
            # Стратегия 5: ChatCompletion с конкретными провайдерами
            {
                'name': 'ChatCompletion - Bing',
                'method': lambda: ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    provider=g4f.Provider.Bing
                )
            },
            
            # Стратегия 6: ChatCompletion с You.com
            {
                'name': 'ChatCompletion - You',
                'method': lambda: ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    provider=g4f.Provider.You
                )
            },
            
            # Стратегия 7: Простой вызов без провайдера
            {
                'name': 'Simple ChatCompletion',
                'method': lambda: ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages
                )
            },
            
            # Стратегия 8: Только пользовательское сообщение
            {
                'name': 'User Only',
                'method': lambda: ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
            },
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logging.info(f"Попытка {i}: {strategy['name']}")
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(strategy['method']),
                    timeout=30.0
                )
                
                # Обработка нового Client API
                if hasattr(response, 'choices') and response.choices:
                    content = response.choices[0].message.content
                    if content and len(content.strip()) > 3:
                        cleaned_response = self._clean_response(content)
                        logging.info(f"✅ {strategy['name']} успешна (длина: {len(cleaned_response)})")
                        return cleaned_response
                
                # Обработка Legacy API (строка)
                elif isinstance(response, str) and len(response.strip()) > 3:
                    cleaned_response = self._clean_response(response)
                    logging.info(f"✅ {strategy['name']} успешна (длина: {len(cleaned_response)})")
                    return cleaned_response
                        
                logging.warning(f"{strategy['name']} дала пустой ответ")
                        
            except asyncio.TimeoutError:
                logging.warning(f"❌ {strategy['name']}: Таймаут (30 сек)")
            except Exception as e:
                error_msg = str(e)[:200]
                logging.warning(f"❌ {strategy['name']}: {error_msg}")
                
                # Если это проблема с API ключом, пропускаем похожие стратегии
                if "api_key" in error_msg.lower() or "key" in error_msg.lower():
                    continue
                    
                # Если модель не найдена, пробуем другие
                if "not found" in error_msg.lower():
                    continue
                    
                continue
        
        return "❌ Все провайдеры AI временно недоступны. Попробуйте позже."

    async def test_providers(self):
        """Тест работоспособности провайдеров"""
        logging.info("=== ТЕСТ G4F ПРОВАЙДЕРОВ ===")
        
        try:
            response = await self.generate_text("Hello, say 'test successful' please")
            logging.info(f"Тест результат: {response[:100]}")
        except Exception as e:
            logging.error(f"❌ Тест не прошел: {e}")

# Создаем глобальный экземпляр
g4f_api_service = G4FAPI()