# -*- coding: utf-8 -*-
"""
Оптимизированный G4F API для максимальной скорости ответов
Поддержка датасетов bigcode/the-stack и laion/relaion-high-resolution
"""

# Импортируем оптимизированную версию
from app.services.g4f_api_optimized import ultra_fast_g4f, UltraFastG4F

# Сохраняем обратную совместимость с улучшенным функционалом
class G4FAPI:
    """Обратно-совместимый API wrapper с полной интеграцией optimized версии"""
    
    def __init__(self):
        self.ultra_fast = ultra_fast_g4f
        self.max_tokens = 1000
    
    async def generate_text(self, prompt: str, system_prompt: str = None, show_typing: callable = None) -> str:
        """Полностью совместимый метод генерации с поддержкой анимации"""
        # Используем errorer v1 identity по умолчанию
        if not system_prompt:
            system_prompt = self.ultra_fast.russian_system_prompt
        return await self.ultra_fast.generate_text(prompt, system_prompt, show_typing)
    
    async def test_speed(self):
        """Тест скорости провайдеров"""
        return await self.ultra_fast.test_speed()

# Создаем экземпляры для совместимости
g4f_api_service = G4FAPI()

# Экспортируем все нужные классы
__all__ = ['g4f_api_service', 'G4FAPI', 'UltraFastG4F']