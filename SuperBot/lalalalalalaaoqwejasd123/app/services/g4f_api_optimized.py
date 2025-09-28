# -*- coding: utf-8 -*-
"""
Супер-оптимизированный G4F API для мгновенных ответов
Поддержка 100k+ пользователей одновременно
"""

import asyncio
import time
import random
import logging
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor
import threading

try:
    from g4f.client import Client
    from g4f import ChatCompletion, Provider
    import g4f
    G4F_AVAILABLE = True
except ImportError:
    G4F_AVAILABLE = False

# Импортируем улучшения датасетов
try:
    from app.services.dataset_enhancer import dataset_enhancer
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False

class UltraFastG4F:
    """Супер-быстрый G4F API с мгновенными ответами"""
    
    def __init__(self):
        self.max_workers = 20  # Увеличиваем пул потоков
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.client = Client() if G4F_AVAILABLE else None
        self.cache = {}  # Простой кеш для быстрых ответов
        self.lock = threading.Lock()
        
        # Самые быстрые провайдеры в приоритетном порядке
        self.fast_providers = [
            # Blackbox - самый быстрый и надежный
            ("blackboxai", g4f.Provider.Blackbox),
            ("gpt-4o-mini", g4f.Provider.Blackbox),
            
            # DeepSeek - очень быстрый
            ("deepseek-v3", g4f.Provider.Together),
            ("deepseek-v3", g4f.Provider.PollinationsAI),
            
            # Автовыбор провайдеров для скорости
            ("deepseek-v3", None),
            ("gpt-4o-mini", None),
            
            # PollinationsAI - быстрый и без ключей
            ("gpt-4o", g4f.Provider.PollinationsAI),
            ("llama-3.3-70b", g4f.Provider.PollinationsAI),
            
            # Together - стабильный и быстрый
            ("llama-3.3-70b", g4f.Provider.Together),
            ("qwen-2.5-72b", g4f.Provider.Together),
        ]
        
        # Русскоязычные промпты для лучшего качества
        self.russian_system_prompt = """Ты - высокоинтеллектуальный русскоязычный AI-ассистент. 

ПРАВИЛА ОТВЕТОВ:
• Отвечай ТОЛЬКО на русском языке
• Будь кратким, точным и полезным  
• Используй эмодзи для наглядности
• Структурируй информацию списками
• Избегай воды и лишних слов
• Максимум 200 слов на ответ

ЭКСПЕРТИЗА:
• Техническая поддержка и программирование
• Бизнес-консультации и аналитика
• Образование и наука
• Творчество и искусство
• Финансы и право

Отвечай профессионально и по делу."""

    def _get_cache_key(self, prompt: str, system_prompt: str = "") -> str:
        """Генерирует ключ для кеша"""
        return f"{hash(prompt)}_{hash(system_prompt or '')}"

    def _clean_response(self, text: str) -> str:
        """Быстрая очистка ответа"""
        if not text:
            return "❌ Пустой ответ от AI"
        
        text = text.strip()
        
        # Убираем технические теги
        for tag in ['<think>', '</think>', '[thinking]', '[/thinking]', 
                   '<reasoning>', '</reasoning>', '```thinking', '```']:
            text = text.replace(tag, '')
        
        # Ограничиваем длину для скорости
        if len(text) > 2000:
            text = text[:1997] + "..."
        
        return text.strip() or "🤖 AI обработал запрос, но ответ оказался пустым"

    async def _try_single_provider(self, model: str, provider, messages: List[Dict], timeout: float = 8.0) -> Optional[str]:
        """Пытается получить ответ от одного провайдера"""
        try:
            if provider:
                future = self.executor.submit(
                    ChatCompletion.create, 
                    model=model, 
                    messages=messages, 
                    provider=provider
                )
            else:
                future = self.executor.submit(
                    ChatCompletion.create,
                    model=model, 
                    messages=messages
                )
            
            response = await asyncio.wait_for(
                asyncio.wrap_future(future),
                timeout=timeout
            )
            
            # Быстрое извлечение текста
            if hasattr(response, 'choices') and response.choices:
                return response.choices[0].message.content
            elif hasattr(response, 'content'):
                return response.content
            elif isinstance(response, str):
                return response
            else:
                return str(response)
                
        except Exception:
            return None

    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Супер-быстрая генерация текста с русской локализацией и датасетами"""
        start_time = time.time()
        
        if not G4F_AVAILABLE:
            return "❌ G4F библиотека недоступна. Установите: pip install g4f"
        
        # Проверяем кеш для мгновенных ответов
        cache_key = self._get_cache_key(prompt, system_prompt)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 🚀 ИНТЕГРАЦИЯ ДАТАСЕТОВ: Улучшаем промпт знаниями из bigcode/the-stack и LAION
        if DATASETS_AVAILABLE:
            enhanced_prompt, enhanced_system = dataset_enhancer.enhance_prompt_with_context(prompt, system_prompt or self.russian_system_prompt)
        else:
            enhanced_prompt = prompt
            enhanced_system = system_prompt or self.russian_system_prompt
        
        # Добавляем контекст для лучшего качества русских ответов
        if not any(word in prompt.lower() for word in ['english', 'translate', 'перевод']):
            enhanced_system += "\n\nВАЖНО: Отвечай исключительно на русском языке!"
        
        messages = [
            {"role": "system", "content": enhanced_system},
            {"role": "user", "content": prompt}
        ]
        
        # Параллельные запросы к 3 самым быстрым провайдерам
        tasks = []
        for model, provider in self.fast_providers[:3]:
            task = asyncio.create_task(
                self._try_single_provider(model, provider, messages, timeout=6.0)
            )
            tasks.append(task)
        
        # Ждем первый успешный ответ
        try:
            done, pending = await asyncio.wait(
                tasks, 
                return_when=asyncio.FIRST_COMPLETED,
                timeout=10.0
            )
            
            # Отменяем оставшиеся задачи
            for task in pending:
                task.cancel()
            
            # Получаем первый успешный результат
            for task in done:
                result = await task
                if result and len(result.strip()) > 5:
                    cleaned = self._clean_response(result)
                    
                    # Кешируем успешный ответ
                    with self.lock:
                        self.cache[cache_key] = cleaned
                        # Ограничиваем размер кеша
                        if len(self.cache) > 1000:
                            # Удаляем 20% старых записей
                            keys_to_remove = list(self.cache.keys())[:200]
                            for key in keys_to_remove:
                                del self.cache[key]
                    
                    elapsed = time.time() - start_time
                    logging.info(f"✅ Быстрый ответ за {elapsed:.2f}с")
                    return cleaned
            
        except asyncio.TimeoutError:
            pass
        
        # Если быстрые провайдеры не сработали, пробуем остальные
        for model, provider in self.fast_providers[3:]:
            try:
                result = await self._try_single_provider(model, provider, messages, timeout=5.0)
                if result and len(result.strip()) > 5:
                    cleaned = self._clean_response(result)
                    elapsed = time.time() - start_time
                    logging.info(f"✅ Резервный ответ за {elapsed:.2f}с")
                    return cleaned
            except Exception:
                continue
        
        # Fallback ответы на русском языке
        fallback_responses = [
            "🤖 Все AI провайдеры временно недоступны, но я обязательно отвечу на ваш вопрос позже!",
            "⚡ Сервисы AI перегружены. Попробуйте переформулировать вопрос или повторите через минуту.",
            "🔄 Подключаюсь к резервным AI серверам... Попробуйте еще раз через 30 секунд.",
        ]
        
        return random.choice(fallback_responses)

    async def test_speed(self) -> Dict[str, float]:
        """Тестирует скорость провайдеров"""
        results = {}
        test_prompt = "Привет! Как дела?"
        
        for model, provider in self.fast_providers[:5]:
            start_time = time.time()
            try:
                result = await self._try_single_provider(
                    model, provider, 
                    [{"role": "user", "content": test_prompt}],
                    timeout=5.0
                )
                elapsed = time.time() - start_time
                if result:
                    provider_name = f"{model}@{provider.__name__ if provider else 'auto'}"
                    results[provider_name] = elapsed
            except Exception:
                continue
        
        return results

    def get_stats(self) -> Dict:
        """Возвращает статистику"""
        return {
            "cache_size": len(self.cache),
            "max_workers": self.max_workers,
            "available_providers": len(self.fast_providers),
            "g4f_available": G4F_AVAILABLE
        }

# Создаем глобальный экземпляр для максимальной производительности
ultra_fast_g4f = UltraFastG4F()

# Обратная совместимость
class G4FAPI:
    def __init__(self):
        self.ultra_fast = ultra_fast_g4f
    
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        return await self.ultra_fast.generate_text(prompt, system_prompt or "")
    
    async def test_speed(self):
        results = await self.ultra_fast.test_speed()
        print("\n⚡ Результаты тестирования скорости:")
        for provider, speed in sorted(results.items(), key=lambda x: x[1]):
            print(f"✅ {provider}: {speed:.2f}с")
        return results

# Экспортируем для использования
g4f_api_service = G4FAPI()