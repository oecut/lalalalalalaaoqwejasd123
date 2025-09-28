# /ErrrorBot/app/services/g4f_api.py

import asyncio
import logging
import re
import time
import random

try:
    from g4f.client import Client
    from g4f import ChatCompletion, Provider
    import g4f
    G4F_AVAILABLE = True
except ImportError:
    G4F_AVAILABLE = False

from config import settings
from app.services.gdpval_intelligence import gdpval_intelligence
from app.services.llava_intelligence import llava_intelligence

class G4FAPI:
    def __init__(self):
        self.max_tokens = settings.max_tokens
        self.client = Client() if G4F_AVAILABLE else None

    def _clean_response(self, text: str) -> str:
        """Очистка ответа"""
        if not text:
            return ""
        text = text.strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'\[thinking\].*?\[/thinking\]', '', text, flags=re.DOTALL)
        text = re.sub(r'\n\n+', '\n\n', text)
        return text.strip()

    async def generate_text(self, prompt: str, system_prompt: str = None) -> str:
        """Генерация с интеграцией GDPval и LLaVA для профессионального и мультимодального интеллекта"""
        
        if not G4F_AVAILABLE:
            return "❌ G4F недоступен"
        
        # 🎯 УЛУЧШЕНИЕ ИНТЕЛЛЕКТА: Интегрируем профессиональный контекст из GDPval
        enhanced_prompt, enhanced_system_prompt = gdpval_intelligence.enhance_user_prompt(prompt, system_prompt)
        
        # 🖼️ МУЛЬТИМОДАЛЬНОСТЬ: Добавляем LLaVA возможности для работы с изображениями
        if llava_intelligence.detect_visual_content(enhanced_prompt):
            # Убеждаемся что LLaVA сервис инициализирован
            await llava_intelligence.ensure_initialization()
            
            visual_prompt, visual_system = await llava_intelligence.enhance_visual_prompt(enhanced_prompt)
            enhanced_prompt = visual_prompt
            if visual_system and enhanced_system_prompt:
                enhanced_system_prompt = enhanced_system_prompt + "\n\n" + visual_system
            elif visual_system:
                enhanced_system_prompt = visual_system
        
        messages = []
        if enhanced_system_prompt:
            messages.append({"role": "system", "content": enhanced_system_prompt})
        messages.append({"role": "user", "content": enhanced_prompt})

        # ТОЛЬКО РАБОЧИЕ ПРОВАЙДЕРЫ (из вашего лога)
        strategies = [
            # DeepSeek через рабочие провайдеры
            lambda: ChatCompletion.create(model="deepseek-v3", messages=messages, provider=g4f.Provider.Together),
            lambda: ChatCompletion.create(model="deepseek-v3", messages=messages, provider=g4f.Provider.PollinationsAI),
            lambda: ChatCompletion.create(model="deepseek-v3", messages=messages),
            
            # Blackbox - самый надежный
            lambda: ChatCompletion.create(model="blackboxai", messages=messages, provider=g4f.Provider.Blackbox),
            lambda: ChatCompletion.create(model="gpt-4o-mini", messages=messages, provider=g4f.Provider.Blackbox),
            lambda: ChatCompletion.create(model="gpt-4o", messages=messages, provider=g4f.Provider.Blackbox),
            lambda: ChatCompletion.create(model="gpt-4", messages=messages, provider=g4f.Provider.Blackbox),
            
            # Together - хорошо работает
            lambda: ChatCompletion.create(model="llama-3.3-70b", messages=messages, provider=g4f.Provider.Together),
            lambda: ChatCompletion.create(model="qwen-2.5-72b", messages=messages, provider=g4f.Provider.Together),
            lambda: ChatCompletion.create(model="mixtral-8x7b", messages=messages, provider=g4f.Provider.Together),
            lambda: ChatCompletion.create(model="deepseek-r1", messages=messages, provider=g4f.Provider.Together),
            
            # PollinationsAI - работает без ключей
            lambda: ChatCompletion.create(model="gpt-4o-mini", messages=messages, provider=g4f.Provider.PollinationsAI),
            lambda: ChatCompletion.create(model="gpt-4o", messages=messages, provider=g4f.Provider.PollinationsAI),
            lambda: ChatCompletion.create(model="llama-3.3-70b", messages=messages, provider=g4f.Provider.PollinationsAI),
            lambda: ChatCompletion.create(model="qwq-32b", messages=messages, provider=g4f.Provider.PollinationsAI),
            
            # HuggingSpace - иногда работает
            lambda: ChatCompletion.create(model="qwen-2-72b", messages=messages, provider=g4f.Provider.HuggingSpace),
            lambda: ChatCompletion.create(model="command-r-plus", messages=messages, provider=g4f.Provider.HuggingSpace),
            
            # Websim - стабильный
            lambda: ChatCompletion.create(model="gemini-1.5-pro", messages=messages, provider=g4f.Provider.Websim),
            lambda: ChatCompletion.create(model="gemini-1.5-flash", messages=messages, provider=g4f.Provider.Websim),
            
            # Copilot - MS провайдер
            lambda: ChatCompletion.create(model="gpt-4", messages=messages, provider=g4f.Provider.Copilot),
            
            # Автовыбор - часто работает
            lambda: ChatCompletion.create(model="deepseek-v3", messages=messages),
            lambda: ChatCompletion.create(model="gpt-4o", messages=messages),
            lambda: ChatCompletion.create(model="gpt-4o-mini", messages=messages),
            lambda: ChatCompletion.create(model="claude-3.5-sonnet", messages=messages),
            lambda: ChatCompletion.create(model="gemini-1.5-flash", messages=messages),
            lambda: ChatCompletion.create(model="llama-3.3-70b", messages=messages)
        ]
        
        # Перемешиваем для распределения
        random.shuffle(strategies)
        
        print(f"Генерация для: {prompt[:30]}...")
        
        for i, strategy in enumerate(strategies, 1):
            try:
                print(f"Попытка {i}: ", end="", flush=True)
                
                response = await asyncio.wait_for(
                    asyncio.to_thread(strategy),
                    timeout=15.0
                )
                
                # Извлекаем текст
                response_text = ""
                if hasattr(response, 'choices') and response.choices:
                    response_text = response.choices[0].message.content
                elif hasattr(response, 'content'):
                    response_text = response.content
                elif isinstance(response, str):
                    response_text = response
                else:
                    response_text = str(response)
                
                if response_text and len(response_text.strip()) > 5:
                    cleaned = self._clean_response(response_text)
                    
                    # 🎯 ДОПОЛНИТЕЛЬНЫЙ ИНТЕЛЛЕКТ: Добавляем профессиональные советы
                    smart_enhancement = gdpval_intelligence.get_smart_response_enhancement(prompt)
                    if smart_enhancement and len(cleaned) < 1000:  # Добавляем только к коротким ответам
                        cleaned += smart_enhancement
                    
                    # 🖼️ ВИЗУАЛЬНАЯ ЭКСПЕРТИЗА: Добавляем LLaVA-подобные улучшения для изображений
                    visual_enhancement = await llava_intelligence.get_visual_response_enhancement(prompt)
                    if visual_enhancement and len(cleaned) < 1200:  # Дополнительное место для визуальных советов
                        cleaned += visual_enhancement
                    
                    print(f"✅ Успех! Длина: {len(cleaned)}")
                    return cleaned
                else:
                    print("❌ Пустой ответ")
                        
            except Exception as e:
                error = str(e)[:40]
                print(f"❌ {error}")
                continue
        
        return "❌ Все провайдеры недоступны"

    async def test_speed(self):
        """Тест скорости только рабочих провайдеров"""
        print("\n⚡ Тест провайдеров:")
        
        messages = [{"role": "user", "content": "Hello"}]
        
        tests = [
            ("DeepSeek V3 (Together)", lambda: ChatCompletion.create(model="deepseek-v3", messages=messages, provider=g4f.Provider.Together)),
            ("DeepSeek V3 (Auto)", lambda: ChatCompletion.create(model="deepseek-v3", messages=messages)),
            ("Blackbox AI", lambda: ChatCompletion.create(model="blackboxai", messages=messages, provider=g4f.Provider.Blackbox)),
            ("GPT-4o (Blackbox)", lambda: ChatCompletion.create(model="gpt-4o", messages=messages, provider=g4f.Provider.Blackbox)),
            ("Llama-3.3-70b (Together)", lambda: ChatCompletion.create(model="llama-3.3-70b", messages=messages, provider=g4f.Provider.Together))
        ]
        
        for name, method in tests:
            try:
                start_time = time.time()
                response = await asyncio.wait_for(asyncio.to_thread(method), timeout=15.0)
                
                response_text = ""
                if hasattr(response, 'choices') and response.choices:
                    response_text = response.choices[0].message.content
                elif isinstance(response, str):
                    response_text = response
                elif hasattr(response, 'content'):
                    response_text = response.content
                
                if response_text and len(response_text.strip()) > 0:
                    elapsed = time.time() - start_time
                    print(f"✅ {name}: {elapsed:.1f}s")
                else:
                    print(f"❌ {name}: Пустой ответ")
                    
            except Exception as e:
                print(f"❌ {name}: {str(e)[:30]}")

# Создаем экземпляр
g4f_api_service = G4FAPI()