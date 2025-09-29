# /ErrrorBot/app/services/gdpval_intelligence.py

import sqlite3
import random
import logging
from typing import Optional, List, Dict, Tuple

class GDPvalIntelligence:
    """
    Сервис для интеграции OpenAI GDPval датасета в ответы бота.
    Делает бота умнее, используя профессиональные задачи из реальных секторов экономики.
    """
    
    def __init__(self, dataset_db_path: str = "database/datasets.db"):
        self.dataset_db_path = dataset_db_path
        self.sectors = {
            'Professional, Scientific, and Technical Services': 'профессиональные услуги',
            'Finance and Insurance': 'финансы и страхование', 
            'Healthcare and Social Assistance': 'здравоохранение',
            'Information': 'информационные технологии',
            'Manufacturing': 'производство',
            'Real Estate': 'недвижимость',
            'Educational Services': 'образование',
            'Arts, Entertainment, and Recreation': 'искусство и развлечения',
            'Government': 'государственное управление'
        }

    def _get_random_professional_context(self) -> Optional[Dict]:
        """Получает случайную профессиональную задачу из GDPval датасета"""
        try:
            conn = sqlite3.connect(self.dataset_db_path)
            cursor = conn.cursor()
            
            # Получаем случайную задачу
            cursor.execute("""
                SELECT sector, occupation, prompt 
                FROM gdpval_tasks 
                ORDER BY RANDOM() 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                sector, occupation, prompt = result
                return {
                    'sector': sector,
                    'occupation': occupation,
                    'task_example': prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    'sector_ru': self.sectors.get(sector, sector)
                }
        except Exception as e:
            logging.error(f"Ошибка получения GDPval контекста: {e}")
        
        return None

    def _get_sector_context(self, sector_hint: str) -> Optional[Dict]:
        """Получает контекст из определенного сектора по ключевым словам"""
        try:
            # Определяем сектор по ключевым словам
            sector_mapping = {
                'финанс': 'Finance and Insurance',
                'деньги': 'Finance and Insurance', 
                'банк': 'Finance and Insurance',
                'инвест': 'Finance and Insurance',
                'здоров': 'Healthcare and Social Assistance',
                'медицин': 'Healthcare and Social Assistance',
                'лечен': 'Healthcare and Social Assistance',
                'техн': 'Information',
                'компьютер': 'Information',
                'программ': 'Information',
                'код': 'Information',
                'образован': 'Educational Services',
                'учеб': 'Educational Services',
                'школ': 'Educational Services',
                'студент': 'Educational Services',
                'искусств': 'Arts, Entertainment, and Recreation',
                'развлечен': 'Arts, Entertainment, and Recreation',
                'творчеств': 'Arts, Entertainment, and Recreation'
            }
            
            target_sector = None
            sector_hint_lower = sector_hint.lower()
            
            for keyword, sector in sector_mapping.items():
                if keyword in sector_hint_lower:
                    target_sector = sector
                    break
            
            if not target_sector:
                return self._get_random_professional_context()
            
            conn = sqlite3.connect(self.dataset_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sector, occupation, prompt 
                FROM gdpval_tasks 
                WHERE sector = ?
                ORDER BY RANDOM() 
                LIMIT 1
            """, (target_sector,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                sector, occupation, prompt = result
                return {
                    'sector': sector,
                    'occupation': occupation, 
                    'task_example': prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    'sector_ru': self.sectors.get(sector, sector)
                }
                
        except Exception as e:
            logging.error(f"Ошибка получения секторного контекста: {e}")
        
        return self._get_random_professional_context()

    def enhance_user_prompt(self, user_message: str, system_prompt: str = None) -> Tuple[str, str]:
        """
        Улучшает промпт пользователя профессиональным контекстом из GDPval
        Возвращает (enhanced_prompt, enhanced_system_prompt)
        """
        try:
            # Получаем релевантный профессиональный контекст
            if any(keyword in user_message.lower() for keyword in ['работа', 'профессия', 'бизнес', 'карьера']):
                context = self._get_sector_context(user_message)
            else:
                context = self._get_random_professional_context()
            
            if not context:
                return user_message, system_prompt
            
            # Создаем улучшенный системный промпт
            professional_enhancement = f"""
Ты - умный ИИ-ассистент с экспертизой в различных профессиональных областях.

🎯 ПРОФЕССИОНАЛЬНЫЙ КОНТЕКСТ:
Сектор: {context['sector_ru']} ({context['occupation']})
Пример задачи: {context['task_example']}

📋 ИНСТРУКЦИИ:
- Отвечай профессионально и грамотно
- Используй знания из реальных рабочих процессов
- Если вопрос связан с профессиональной деятельностью, применяй экспертизу
- Будь полезным и практичным в ответах
- Адаптируй стиль под контекст вопроса
"""
            
            # Комбинируем с существующим системным промптом
            if system_prompt:
                enhanced_system_prompt = f"{professional_enhancement}\n\nДОПОЛНИТЕЛЬНЫЕ ИНСТРУКЦИИ:\n{system_prompt}"
            else:
                enhanced_system_prompt = professional_enhancement
            
            # Слегка улучшаем пользовательский промпт
            enhanced_user_prompt = user_message
            
            return enhanced_user_prompt, enhanced_system_prompt
            
        except Exception as e:
            logging.error(f"Ошибка улучшения промпта: {e}")
            return user_message, system_prompt

    def get_smart_response_enhancement(self, user_message: str) -> Optional[str]:
        """Получает дополнительную информацию для ответа на основе GDPval"""
        try:
            context = self._get_sector_context(user_message)
            if context:
                return f"\n\n💡 <b>Профессиональный совет</b> ({context['sector_ru']}):\n<blockquote>Эксперты в области '{context['occupation']}' рекомендуют использовать структурированный подход к подобным задачам.</blockquote>"
        except Exception as e:
            logging.error(f"Ошибка получения умного дополнения: {e}")
        
        return None

    def get_dataset_stats(self) -> Dict[str, int]:
        """Получает статистику по загруженному датасету"""
        try:
            conn = sqlite3.connect(self.dataset_db_path)
            cursor = conn.cursor()
            
            # Общее количество задач
            cursor.execute("SELECT COUNT(*) FROM gdpval_tasks")
            total_tasks = cursor.fetchone()[0]
            
            # Количество секторов
            cursor.execute("SELECT COUNT(DISTINCT sector) FROM gdpval_tasks")
            total_sectors = cursor.fetchone()[0]
            
            # Количество профессий
            cursor.execute("SELECT COUNT(DISTINCT occupation) FROM gdpval_tasks")
            total_occupations = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_tasks': total_tasks,
                'total_sectors': total_sectors,
                'total_occupations': total_occupations
            }
        except Exception as e:
            logging.error(f"Ошибка получения статистики датасета: {e}")
            return {'total_tasks': 0, 'total_sectors': 0, 'total_occupations': 0}

# Создаем глобальный экземпляр
gdpval_intelligence = GDPvalIntelligence()