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
        """Обновленный сервис для работы с g4f - реальные работающие провайдеры (Сентябрь 2025)"""
        self.max_tokens = settings.max_tokens
        self.client = Client() if G4F_AVAILABLE else None
        self.last_request_time = {}
        self.request_delay = 2.0
        
        logging.info(f"Инициализация G4F API с реальными работающими провайдерами (лимит токенов: {self.max_tokens})")
        
        if not G4F_AVAILABLE:
            logging.error("G4F недоступен!")

    def _clean_response(self, text: str) -> str:
        """Очищает и форматирует ответ от ИИ"""
        if not text:
            return ""
            
        text = text.strip()
        
        # Убираем артефакты thinking процессов
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'\[thinking\].*?\[/thinking\]', '', text, flags=re.DOTALL)
        text = re.sub(r'思考：.*?(?=\n|$)', '', text, flags=re.MULTILINE)
        text = re.sub(r'Let me think.*?(?=\n|$)', '', text, flags=re.MULTILINE)
        
        # Убираем двойные переносы строк
        text = re.sub(r'\n\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
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
        Генерирует текстовый ответ с реальными работающими провайдерами (Сентябрь 2025)
        Использует только проверенные модели и провайдеры
        """
        
        if not G4F_AVAILABLE or not self.client:
            return "❌ Критическая ошибка модуля генерации. Обратитесь к администратору."
        
        # Подготавливаем сообщения
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # СТРАТЕГИИ с реальными работающими моделями из Blackbox (Сентябрь 2025)
        strategies = [
            # ВЫСШИЙ ПРИОРИТЕТ: Blackbox с проверенными моделями
            {
                'name': 'Blackbox AI (собственная модель)',
                'method': lambda: ChatCompletion.create(
                    model="blackboxai",
                    messages=messages,
                    provider=g4f.Provider.Blackbox
                ),
                'rate_limit': False,
                'timeout': 20.0
            },
            
            {
                'name': 'GPT-4 via Blackbox',
                'method': lambda: ChatCompletion.create(
                    model="gpt-4",
                    messages=messages,
                    provider=g4f.Provider.Blackbox
                ),
                'rate_limit': False,
                'timeout': 22.0
            },
            
            {
                'name': 'GPT-4o via Blackbox',
                'method': lambda: ChatCompletion.create(
                    model="gpt-4o",
                    messages=messages,
                    provider=g4f.Provider.Blackbox
                ),
                'rate_limit': False,
                'timeout': 20.0
            },
            
            {
                'name': 'GPT-4o-mini via Blackbox',
                'method': lambda: ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    provider=g4f.Provider.Blackbox
                ),
                'rate_limit': False,
                'timeout': 18.0
            },
            
            # ВТОРОЙ ПРИОРИТЕТ: Client API (самые надежные)
            {
                'name': 'Client API - GPT-4',
                'method': lambda: self.client.chat.completions.create(
                    model="gpt-4",
                    messages=messages
                ),
                'rate_limit': True,
                'timeout': 25.0
            },
            
            {
                'name': 'Client API - GPT-4o-mini',
                'method': lambda: self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages
                ),
                'rate_limit': True,
                'timeout': 20.0
            },
            
            {
                'name': 'Client API - GPT-3.5-turbo',
                'method': lambda: self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages
                ),
                'rate_limit': True,
                'timeout': 18.0
            },
            
            # ТРЕТИЙ ПРИОРИТЕТ: Автоматический выбор
            {
                'name': 'Auto GPT-4',
                'method': lambda: ChatCompletion.create(
                    model="gpt-4",
                    messages=messages
                ),
                'rate_limit': False,
                'timeout': 30.0
            },
            
            {
                'name': 'Auto GPT-4o-mini',
                'method': lambda: ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=messages
                ),
                'rate_limit': False,
                'timeout': 25.0
            },
            
            {
                'name': 'Auto Claude-3.5-sonnet',
                'method': lambda: ChatCompletion.create(
                    model="claude-3.5-sonnet",
                    messages=messages
                ),
                'rate_limit': False,
                'timeout': 28.0
            },
            
            # ЧЕТВЕРТЫЙ ПРИОРИТЕТ: Попытка DeepSeek через Client (если поддерживается)
            {
                'name': 'Client DeepSeek (если доступен)',
                'method': lambda: self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages
                ),
                'rate_limit': True,
                'timeout': 30.0
            },
            
            # РЕЗЕРВНЫЕ стратегии
            {
                'name': 'Auto Gemini-Pro',
                'method': lambda: ChatCompletion.create(
                    model="gemini-pro",
                    messages=messages
                ),
                'rate_limit': False,
                'timeout': 25.0
            }
        ]
        
        # Логирование начала генерации
        logging.info(f"Начинаю генерацию с проверенными провайдерами для запроса: {prompt[:50]}...")
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logging.info(f"Попытка {i}/{len(strategies)}: {strategy['name']}")
                
                if strategy.get('rate_limit', False):
                    await self._rate_limit_check(strategy['name'])
                
                timeout = strategy.get('timeout', 20.0)
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(strategy['method']),
                    timeout=timeout
                )
                
                # Обработка ответа
                response_text = ""
                
                if hasattr(response, 'choices') and response.choices:
                    response_text = response.choices[0].message.content
                elif hasattr(response, 'content'):
                    response_text = response.content
                elif isinstance(response, str):
                    response_text = response
                elif hasattr(response, 'text'):
                    response_text = response.text
                else:
                    response_text = str(response)
                
                if response_text and len(response_text.strip()) > 5:
                    cleaned_response = self._clean_response(response_text)
                    logging.info(f"✅ {strategy['name']} успешна (длина: {len(cleaned_response)} символов)")
                    
                    # Сообщения об успехе
                    if 'blackbox' in strategy['name'].lower():
                        logging.info("⚫ Использован Blackbox провайдер")
                    elif 'client' in strategy['name'].lower():
                        if 'deepseek' in strategy['name'].lower():
                            logging.info("🔥 Подключен DeepSeek через Client API!")
                        else:
                            logging.info("🔧 Использован Client API")
                    elif 'auto' in strategy['name'].lower():
                        logging.info("🔄 Использован автовыбор провайдера")
                    
                    return cleaned_response
                        
                logging.warning(f"❌ {strategy['name']}: Пустой или слишком короткий ответ")
                        
            except asyncio.TimeoutError:
                logging.warning(f"❌ {strategy['name']}: Таймаут ({timeout}s)")
                
            except Exception as e:
                error_msg = str(e)[:200]
                logging.warning(f"❌ {strategy['name']}: {error_msg}")
                
                # Простая обработка ошибок
                if "rate_limit" in error_msg.lower():
                    logging.warning("🚨 Rate limit, пауза и переключение...")
                    await asyncio.sleep(3)
                    continue
                    
                if "api_key" in error_msg.lower():
                    logging.warning("🚨 Требуется API ключ, пропускаем...")
                    continue
                    
                if "model not found" in error_msg.lower():
                    logging.warning("🚨 Модель не найдена в провайдере...")
                    continue
                    
                continue
        
        # Если все стратегии не сработали
        logging.error("❌ Все провайдеры недоступны")
        return (
            "❌ Все ИИ провайдеры временно недоступны.\n\n"
            "📝 Что можно попробовать:\n"
            "• Подождать несколько минут и повторить\n"
            "• Сократить длину запроса\n"
            "• Перефразировать вопрос\n\n"
            "🔄 Сервисы испытывают высокую нагрузку."
        )

    async def test_providers_speed(self) -> Dict[str, Any]:
        """Тестирует скорость доступных провайдеров"""
        logging.info("⚡ Тестирование скорости доступных провайдеров...")
        
        test_results = {
            'blackbox_ai_speed': None,
            'blackbox_gpt4_speed': None,
            'client_gpt4_speed': None,
            'client_deepseek_speed': None,
            'fastest_overall': None,
            'test_time': time.time()
        }
        
        test_prompt = "Hello"
        messages = [{"role": "user", "content": test_prompt}]
        
        # Тест основных провайдеров
        providers_test = [
            ('Blackbox AI', 'blackbox_ai_speed', 
             lambda: ChatCompletion.create(model="blackboxai", messages=messages, provider=g4f.Provider.Blackbox)),
            ('Blackbox GPT-4', 'blackbox_gpt4_speed',
             lambda: ChatCompletion.create(model="gpt-4", messages=messages, provider=g4f.Provider.Blackbox)),
            ('Client GPT-4', 'client_gpt4_speed',
             lambda: self.client.chat.completions.create(model="gpt-4", messages=messages)),
            ('Client DeepSeek', 'client_deepseek_speed',
             lambda: self.client.chat.completions.create(model="deepseek-chat", messages=messages))
        ]
        
        fastest_time = float('inf')
        fastest_provider = None
        
        for provider_name, result_key, method in providers_test:
            try:
                start_time = time.time()
                response = await asyncio.wait_for(
                    asyncio.to_thread(method),
                    timeout=15.0
                )
                
                response_text = ""
                if hasattr(response, 'choices') and response.choices:
                    response_text = response.choices[0].message.content
                elif isinstance(response, str):
                    response_text = response
                elif hasattr(response, 'content'):
                    response_text = response.content
                
                if response_text and len(response_text.strip()) > 0:
                    response_time = time.time() - start_time
                    test_results[result_key] = response_time
                    
                    if response_time < fastest_time:
                        fastest_time = response_time
                        fastest_provider = provider_name
                    
                    logging.info(f"⚡ {provider_name}: {response_time:.2f}s")
                
            except Exception as e:
                logging.warning(f"❌ {provider_name} недоступен для теста: {str(e)[:100]}")
        
        if fastest_provider:
            test_results['fastest_overall'] = {
                'provider': fastest_provider,
                'time': fastest_time
            }
            logging.info(f"🏆 Самый быстрый провайдер: {fastest_provider} ({fastest_time:.2f}s)")
        
        return test_results

    async def get_speed_status(self) -> str:
        """Возвращает статус скорости провайдеров"""
        try:
            speed_results = await self.test_providers_speed()
            
            status_lines = ["⚡ Статус скорости провайдеров:"]
            
            if speed_results['blackbox_ai_speed']:
                status_lines.append(f"⚫ Blackbox AI: {speed_results['blackbox_ai_speed']:.1f}s")
            else:
                status_lines.append("❌ Blackbox AI: Недоступен")
                
            if speed_results['blackbox_gpt4_speed']:
                status_lines.append(f"⚫ Blackbox GPT-4: {speed_results['blackbox_gpt4_speed']:.1f}s")
            else:
                status_lines.append("❌ Blackbox GPT-4: Недоступен")
            
            if speed_results['client_gpt4_speed']:
                status_lines.append(f"🔧 Client GPT-4: {speed_results['client_gpt4_speed']:.1f}s")
            else:
                status_lines.append("❌ Client GPT-4: Недоступен")
                
            if speed_results['client_deepseek_speed']:
                status_lines.append(f"🔥 Client DeepSeek: {speed_results['client_deepseek_speed']:.1f}s")
            else:
                status_lines.append("❌ Client DeepSeek: Недоступен")
            
            if speed_results['fastest_overall']:
                fastest = speed_results['fastest_overall']
                status_lines.append(f"🏆 Самый быстрый: {fastest['provider']} ({fastest['time']:.1f}s)")
            else:
                status_lines.append("❌ Все провайдеры недоступны")
            
            return "\n".join(status_lines)
            
        except Exception as e:
            return f"❌ Ошибка проверки скорости: {str(e)[:100]}"

# Создаем глобальный экземпляр
g4f_api_service = G4FAPI()