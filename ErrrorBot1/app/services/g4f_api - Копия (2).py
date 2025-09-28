# /ErrrorBot/app/services/g4f_api.py

import asyncio
import logging
from typing import Optional, Dict, Any
import re
import json
import time

try:
    from g4f.client import Client
    from g4f import ChatCompletion, Provider
    import g4f
    G4F_AVAILABLE = True
except ImportError:
    G4F_AVAILABLE = False
    logging.error("g4f не установлен. Установите: pip install -U g4f")

from config import settings

class G4FAPI:
    def __init__(self):
        """Обновленный сервис для работы с g4f с приоритетом на быстрые DeepSeek модели (Сентябрь 2025)"""
        self.max_tokens = settings.max_tokens
        self.client = Client() if G4F_AVAILABLE else None
        self.last_request_time = {}
        self.request_delay = 1.5  # Минимальная задержка между запросами для DeepSeek
        
        logging.info(f"Инициализация G4F API с быстрыми DeepSeek моделями (лимит токенов: {self.max_tokens})")
        
        if not G4F_AVAILABLE:
            logging.error("G4F недоступен!")

    def _clean_response(self, text: str) -> str:
        """Очищает и форматирует ответ от ИИ"""
        if not text:
            return ""
            
        # Убираем лишние пробелы и переносы строк
        text = text.strip()
        
        # Убираем артефакты thinking процессов (на случай если попадут)
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'\[thinking\].*?\[/thinking\]', '', text, flags=re.DOTALL)
        text = re.sub(r'思考：.*?(?=\n|$)', '', text, flags=re.MULTILINE)
        text = re.sub(r'Let me think.*?(?=\n|$)', '', text, flags=re.MULTILINE)
        
        # Убираем двойные переносы строк
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Убираем лишние пробелы
        text = re.sub(r' +', ' ', text)
        
        # Исправляем проблему с повторяющимися символами в конце
        text = re.sub(r'(.)\1{2,}$', r'\1', text)
        
        return text.strip()

    async def _rate_limit_check(self, provider_name: str):
        """Проверка rate limiting для провайдеров"""
        current_time = time.time()
        last_time = self.last_request_time.get(provider_name, 0)
        
        if current_time - last_time < self.request_delay:
            wait_time = self.request_delay - (current_time - last_time)
            await asyncio.sleep(wait_time)
        
        self.last_request_time[provider_name] = time.time()

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Генерирует текстовый ответ с приоритетом на БЫСТРЫЕ DeepSeek модели (Сентябрь 2025)
        
        Быстрые модели DeepSeek (без reasoning):
        - deepseek-chat (DeepSeek-V3.1-Terminus в быстром режиме)
        - deepseek-v3 (базовая V3 модель) 
        - deepseek-coder (специализированная для кода)
        """
        
        if not G4F_AVAILABLE or not self.client:
            return "❌ Критическая ошибка модуля генерации. Обратитесь к администратору."
        
        # Подготавливаем сообщения
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # ПРИОРИТЕТНЫЕ СТРАТЕГИИ с акцентом на БЫСТРЫЕ DeepSeek модели
        strategies = [
            # ВЫСШИЙ ПРИОРИТЕТ: Быстрые DeepSeek модели
            {
                'name': 'DeepSeek Chat (V3.1-Terminus Fast)',
                'method': lambda: self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=0.7,
                    stream=False
                ),
                'rate_limit': True,
                'timeout': 20.0
            },
            
            {
                'name': 'DeepSeek V3 (Base Fast)',
                'method': lambda: self.client.chat.completions.create(
                    model="deepseek-v3",
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=0.7
                ),
                'rate_limit': True,
                'timeout': 18.0
            },
            
            {
                'name': 'DeepSeek Coder (Fast)',
                'method': lambda: self.client.chat.completions.create(
                    model="deepseek-coder",
                    messages=messages,
                    max_tokens=self.max_tokens
                ),
                'rate_limit': True,
                'timeout': 18.0
            },
            
            # ОЧЕНЬ БЫСТРЫЕ FALLBACK МОДЕЛИ 
            {
                'name': 'Gemini 2.0 Flash (Ultra Fast)',
                'method': lambda: self.client.chat.completions.create(
                    model="gemini-2.0-flash-exp",
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=0.8
                ),
                'rate_limit': False,
                'timeout': 12.0
            },
            
            {
                'name': 'GPT-4o Mini (Ultra Fast)',
                'method': lambda: self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    max_tokens=self.max_tokens
                ),
                'rate_limit': False,
                'timeout': 15.0
            },
            
            {
                'name': 'Claude 3.5 Haiku (Ultra Fast)',
                'method': lambda: self.client.chat.completions.create(
                    model="claude-3-5-haiku-20241022",
                    messages=messages,
                    max_tokens=self.max_tokens
                ),
                'rate_limit': False,
                'timeout': 15.0
            },
            
            # ЗАПАСНЫЕ БЫСТРЫЕ МОДЕЛИ
            {
                'name': 'Llama 3.1 70B (Fast)',
                'method': lambda: self.client.chat.completions.create(
                    model="llama-3.1-70b-instruct",
                    messages=messages,
                    max_tokens=self.max_tokens
                ),
                'rate_limit': False,
                'timeout': 18.0
            },
            
            {
                'name': 'Qwen 2.5 72B (Fast)',
                'method': lambda: self.client.chat.completions.create(
                    model="qwen-2.5-72b-instruct",
                    messages=messages,
                    max_tokens=self.max_tokens
                ),
                'rate_limit': False,
                'timeout': 18.0
            },
            
            # LEGACY провайдеры как последний резерв
            {
                'name': 'Legacy ChatCompletion Auto',
                'method': lambda: ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    provider=g4f.Provider.Auto
                ),
                'rate_limit': False,
                'timeout': 25.0
            },
            
            {
                'name': 'Legacy You.com (Fast)',
                'method': lambda: ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    provider=g4f.Provider.You
                ),
                'rate_limit': False,
                'timeout': 20.0
            }
        ]
        
        # Логирование начала генерации
        logging.info(f"Начинаю генерацию с приоритетом на БЫСТРЫЕ DeepSeek для запроса: {prompt[:50]}...")
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logging.info(f"Попытка {i}/{len(strategies)}: {strategy['name']}")
                
                # Применяем rate limiting для DeepSeek провайдеров
                if strategy.get('rate_limit', False):
                    await self._rate_limit_check(strategy['name'])
                
                # Используем малые таймауты для скорости
                timeout = strategy.get('timeout', 20.0)
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(strategy['method']),
                    timeout=timeout
                )
                
                # Обработка Client API ответа
                if hasattr(response, 'choices') and response.choices:
                    content = response.choices[0].message.content
                    if content and len(content.strip()) > 5:
                        cleaned_response = self._clean_response(content)
                        logging.info(f"✅ {strategy['name']} успешна (длина: {len(cleaned_response)} символов, время: {timeout}s)")
                        
                        # Специальная обработка для быстрых DeepSeek
                        if 'deepseek' in strategy['name'].lower():
                            logging.info("🚀 Использована быстрая DeepSeek модель")
                        
                        return cleaned_response
                
                # Обработка Legacy API ответа
                elif isinstance(response, str) and len(response.strip()) > 5:
                    cleaned_response = self._clean_response(response)
                    logging.info(f"✅ {strategy['name']} успешна (длина: {len(cleaned_response)} символов)")
                    return cleaned_response
                        
                logging.warning(f"❌ {strategy['name']}: Пустой или слишком короткий ответ")
                        
            except asyncio.TimeoutError:
                logging.warning(f"❌ {strategy['name']}: Таймаут ({timeout}s) - слишком медленно")
                
            except Exception as e:
                error_msg = str(e)[:200]
                logging.warning(f"❌ {strategy['name']}: {error_msg}")
                
                # Специальная обработка ошибок DeepSeek
                if "rate_limit" in error_msg.lower() or "quota" in error_msg.lower():
                    logging.warning("🚨 DeepSeek rate limit достигнут, переключаюсь на ultra-fast модели...")
                    continue
                    
                if "unavailable" in error_msg.lower() or "maintenance" in error_msg.lower():
                    logging.warning("🚨 DeepSeek временно недоступен, использую мгновенные модели...")
                    continue
                    
                # Если API ключ проблема, пропускаем похожие стратегии
                if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                    continue
                    
                continue
        
        # Если все стратегии не сработали
        logging.error("❌ Все быстрые провайдеры AI недоступны")
        return "❌ Все быстрые провайдеры AI временно недоступны. DeepSeek и резервные модели не отвечают. Попробуйте позже."

    async def test_fast_models_speed(self) -> Dict[str, Any]:
        """Тестирует скорость быстрых моделей"""
        logging.info("⚡ Тестирование скорости быстрых моделей...")
        
        test_results = {
            'deepseek_chat_speed': None,
            'deepseek_v3_speed': None,
            'deepseek_coder_speed': None,
            'fastest_overall': None,
            'test_time': time.time()
        }
        
        # Короткий тестовый запрос для проверки скорости
        test_prompt = "Hi! Reply with just 'OK'"
        
        # Тест быстрых DeepSeek моделей
        fast_models = [
            ('deepseek-chat', 'deepseek_chat_speed'),
            ('deepseek-v3', 'deepseek_v3_speed'),
            ('deepseek-coder', 'deepseek_coder_speed')
        ]
        
        fastest_time = float('inf')
        fastest_model = None
        
        for model_name, result_key in fast_models:
            try:
                start_time = time.time()
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        lambda: self.client.chat.completions.create(
                            model=model_name,
                            messages=[{"role": "user", "content": test_prompt}],
                            max_tokens=10,
                            temperature=0.1
                        )
                    ),
                    timeout=15.0
                )
                
                if hasattr(response, 'choices') and response.choices:
                    content = response.choices[0].message.content
                    if content:
                        response_time = time.time() - start_time
                        test_results[result_key] = response_time
                        
                        if response_time < fastest_time:
                            fastest_time = response_time
                            fastest_model = model_name
                        
                        logging.info(f"⚡ {model_name}: {response_time:.2f}s")
                
            except Exception as e:
                logging.warning(f"❌ {model_name} недоступен для теста скорости: {str(e)[:100]}")
        
        if fastest_model:
            test_results['fastest_overall'] = {
                'model': fastest_model,
                'time': fastest_time
            }
            logging.info(f"🏆 Самая быстрая модель: {fastest_model} ({fastest_time:.2f}s)")
        
        return test_results

    async def get_speed_status(self) -> str:
        """Возвращает статус скорости моделей"""
        try:
            speed_results = await self.test_fast_models_speed()
            
            status_lines = ["⚡ Статус скорости моделей:"]
            
            # DeepSeek скорость
            if speed_results['deepseek_chat_speed']:
                status_lines.append(f"🚀 DeepSeek Chat: {speed_results['deepseek_chat_speed']:.1f}s")
            else:
                status_lines.append("❌ DeepSeek Chat: Недоступен")
                
            if speed_results['deepseek_v3_speed']:
                status_lines.append(f"🚀 DeepSeek V3: {speed_results['deepseek_v3_speed']:.1f}s")
            else:
                status_lines.append("❌ DeepSeek V3: Недоступен")
            
            if speed_results['deepseek_coder_speed']:
                status_lines.append(f"💻 DeepSeek Coder: {speed_results['deepseek_coder_speed']:.1f}s")
            else:
                status_lines.append("❌ DeepSeek Coder: Недоступен")
            
            # Самая быстрая модель
            if speed_results['fastest_overall']:
                fastest = speed_results['fastest_overall']
                status_lines.append(f"🏆 Лидер скорости: {fastest['model']} ({fastest['time']:.1f}s)")
            else:
                status_lines.append("❌ Все модели недоступны")
            
            return "\n".join(status_lines)
            
        except Exception as e:
            return f"❌ Ошибка проверки скорости: {str(e)[:100]}"

# Создаем глобальный экземпляр
g4f_api_service = G4FAPI()