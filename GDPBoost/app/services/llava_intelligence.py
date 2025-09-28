"""
LLaVA Intelligence Service - Мультимодальные возможности для Telegram бота
Имитирует возможности LLaVA-One-Vision для работы с изображениями и визуальным контентом
"""

import random
import asyncio
import aiosqlite
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class LLaVAIntelligenceService:
    """
    Сервис для добавления мультимодальных возможностей в стиле LLaVA
    """
    
    def __init__(self, db_path: str = "datasets/datasets.db"):
        self.db_path = db_path
        
        # База знаний LLaVA-стиля для мультимодальных задач
        self.visual_task_patterns = {
            'image_description': [
                "Анализирую изображение с детальным описанием визуальных элементов...",
                "Изучаю композицию, цвета, объекты и их расположение на изображении...",
                "Провожу визуальный анализ с акцентом на ключевые детали...",
            ],
            'object_detection': [
                "Определяю объекты на изображении и их местоположение...",
                "Сканирую изображение для выявления всех видимых элементов...",
                "Анализирую пространственные отношения между объектами...",
            ],
            'text_recognition': [
                "Распознаю и читаю текст на изображении...",
                "Извлекаю текстовую информацию из визуального контента...",
                "Анализирую текстовые элементы и их содержание...",
            ],
            'scene_understanding': [
                "Понимаю контекст и ситуацию, изображенную на фото...",
                "Анализирую общую сцену и атмосферу изображения...",
                "Интерпретирую визуальную информацию в контексте...",
            ],
            'visual_reasoning': [
                "Применяю визуальное мышление для анализа изображения...",
                "Делаю логические выводы на основе визуальных данных...",
                "Рассуждаю о причинно-следственных связях в изображении...",
            ]
        }
        
        # Профессиональные советы для работы с изображениями
        self.visual_expertise = {
            'photography': {
                'ru': 'фотография',
                'tips': [
                    "Обратите внимание на композицию и правило третей",
                    "Учитывайте освещение и его влияние на настроение",
                    "Экспериментируйте с различными ракурсами съемки",
                    "Используйте глубину резкости для создания фокуса",
                ]
            },
            'design': {
                'ru': 'дизайн',
                'tips': [
                    "Соблюдайте баланс между элементами дизайна",
                    "Используйте цветовую гармонию для создания настроения",
                    "Применяйте принципы типографики для лучшей читаемости",
                    "Создавайте визуальную иерархию для направления внимания",
                ]
            },
            'art_analysis': {
                'ru': 'искусствоведение',
                'tips': [
                    "Анализируйте стиль и технику исполнения произведения",
                    "Рассматривайте исторический и культурный контекст",
                    "Обращайте внимание на символизм и скрытые смыслы",
                    "Изучайте влияние эпохи на художественное выражение",
                ]
            },
            'technical_analysis': {
                'ru': 'техническое изображение',
                'tips': [
                    "Тщательно анализируйте технические детали и схемы",
                    "Обращайте внимание на масштаб и пропорции",
                    "Изучайте функциональные элементы и их взаимосвязи",
                    "Проверяйте соответствие стандартам и требованиям",
                ]
            }
        }
        
        # Популярные визуальные задачи
        self.common_visual_tasks = [
            {
                'task': 'Описание содержимого изображения',
                'context': 'Детальный анализ всех визуальных элементов',
                'example': 'На изображении видны люди, объекты и их взаимодействие в определенной обстановке'
            },
            {
                'task': 'Распознавание текста на изображении',
                'context': 'Извлечение и интерпретация текстовой информации',
                'example': 'Читаю вывески, надписи, документы на фотографии'
            },
            {
                'task': 'Анализ эмоций и настроения',
                'context': 'Определение эмоционального содержания изображения',
                'example': 'Анализирую выражения лиц, позы тела, общую атмосферу'
            },
            {
                'task': 'Подсчет объектов',
                'context': 'Точный подсчет количества элементов на изображении',
                'example': 'Считаю людей, предметы, животных или другие объекты'
            },
            {
                'task': 'Определение местоположения и контекста',
                'context': 'Анализ места съемки и обстоятельств',
                'example': 'Определяю где и при каких обстоятельствах сделано фото'
            }
        ]

    async def create_llava_tables(self):
        """Создает таблицы для хранения LLaVA данных"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Таблица для визуальных паттернов
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS llava_visual_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        context TEXT,
                        example TEXT,
                        expertise_area TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Индексы
                await db.execute("CREATE INDEX IF NOT EXISTS idx_llava_pattern_type ON llava_visual_patterns(pattern_type)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_llava_expertise ON llava_visual_patterns(expertise_area)")
                
                await db.commit()
                
                # Заполняем базовыми данными, если таблица пустая
                await self._populate_initial_data(db)
                
        except Exception as e:
            logger.error(f"Ошибка создания таблиц LLaVA: {e}")

    async def _populate_initial_data(self, db):
        """Заполняет таблицы начальными данными"""
        try:
            # Проверяем есть ли уже данные
            async with db.execute("SELECT COUNT(*) FROM llava_visual_patterns") as cursor:
                row = await cursor.fetchone()
                if row[0] > 0:
                    return  # Данные уже есть
            
            # Добавляем визуальные паттерны
            patterns_data = []
            
            for task in self.common_visual_tasks:
                patterns_data.append((
                    'visual_task',
                    task['task'],
                    task['context'],
                    task['example'],
                    'general'
                ))
            
            # Добавляем экспертные советы
            for area, data in self.visual_expertise.items():
                for tip in data['tips']:
                    patterns_data.append((
                        'expert_tip',
                        tip,
                        f"Профессиональный совет в области {data['ru']}",
                        None,
                        area
                    ))
            
            await db.executemany("""
                INSERT INTO llava_visual_patterns 
                (pattern_type, description, context, example, expertise_area)
                VALUES (?, ?, ?, ?, ?)
            """, patterns_data)
            
            await db.commit()
            logger.info("✅ LLaVA данные инициализированы")
            
        except Exception as e:
            logger.error(f"Ошибка заполнения LLaVA данных: {e}")

    def detect_visual_content(self, user_message: str) -> bool:
        """Определяет, содержит ли сообщение запрос о визуальном контенте"""
        visual_keywords = [
            'изображение', 'картинка', 'фото', 'picture', 'image', 'photo',
            'видео', 'video', 'screenshot', 'скриншот',
            'рисунок', 'drawing', 'схема', 'diagram',
            'что на фото', 'что изображено', 'опиши картинку',
            'analyze image', 'describe picture', 'what do you see'
        ]
        
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in visual_keywords)

    def get_visual_task_type(self, user_message: str) -> str:
        """Определяет тип визуальной задачи"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['опиши', 'describe', 'что изображено', 'что на']):
            return 'image_description'
        elif any(word in message_lower for word in ['найди', 'find', 'detect', 'найти', 'где']):
            return 'object_detection'
        elif any(word in message_lower for word in ['текст', 'text', 'читай', 'read', 'надпись']):
            return 'text_recognition'
        elif any(word in message_lower for word in ['понимай', 'understand', 'ситуация', 'сцена']):
            return 'scene_understanding'
        elif any(word in message_lower for word in ['анализ', 'analyze', 'рассуждение', 'reasoning']):
            return 'visual_reasoning'
        else:
            return 'image_description'  # По умолчанию

    async def get_visual_context(self, task_type: str, expertise_area: str = None) -> Dict[str, Any]:
        """Получает контекст для визуальной задачи"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Получаем паттерн для типа задачи
                query = """
                    SELECT description, context, example 
                    FROM llava_visual_patterns 
                    WHERE pattern_type = 'visual_task' 
                    ORDER BY RANDOM() LIMIT 1
                """
                
                async with db.execute(query) as cursor:
                    task_row = await cursor.fetchone()
                
                # Получаем экспертный совет
                if expertise_area:
                    expert_query = """
                        SELECT description, context 
                        FROM llava_visual_patterns 
                        WHERE pattern_type = 'expert_tip' AND expertise_area = ?
                        ORDER BY RANDOM() LIMIT 1
                    """
                    async with db.execute(expert_query, (expertise_area,)) as cursor:
                        expert_row = await cursor.fetchone()
                else:
                    expert_row = None
                
                return {
                    'task_description': task_row[0] if task_row else None,
                    'task_context': task_row[1] if task_row else None,
                    'task_example': task_row[2] if task_row else None,
                    'expert_advice': expert_row[0] if expert_row else None,
                    'expert_context': expert_row[1] if expert_row else None,
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения визуального контекста: {e}")
            return {}

    async def enhance_visual_prompt(self, user_message: str) -> tuple[str, str]:
        """Улучшает промпт для работы с визуальным контентом"""
        try:
            if not self.detect_visual_content(user_message):
                return user_message, ""
            
            task_type = self.get_visual_task_type(user_message)
            
            # Базовый контекст для визуальных задач
            visual_intro = random.choice(self.visual_task_patterns.get(task_type, [
                "Анализирую визуальный контент с использованием LLaVA-подобных возможностей..."
            ]))
            
            # Улучшенный системный промпт
            enhanced_system = f"""
Ты - умный ИИ-ассистент с мультимодальными возможностями, похожими на LLaVA-OneVision.

🎯 ВИЗУАЛЬНАЯ ЭКСПЕРТИЗА:
Тип задачи: {task_type}
Подход: {visual_intro}

💡 МУЛЬТИМОДАЛЬНЫЕ ВОЗМОЖНОСТИ:
- Детальный анализ изображений и визуального контента
- Распознавание объектов, текста и сцен
- Понимание пространственных отношений
- Визуальное рассуждение и интерпретация
- Профессиональный анализ в различных областях

📸 ИНСТРУКЦИЯ:
Если пользователь отправил изображение или спрашивает о визуальном контенте, 
используй свои возможности анализа изображений для детального и профессионального ответа.
Применяй принципы LLaVA: понимание + рассуждение + экспертиза.
"""
            
            return user_message, enhanced_system
            
        except Exception as e:
            logger.error(f"Ошибка улучшения визуального промпта: {e}")
            return user_message, ""

    async def get_visual_response_enhancement(self, user_message: str) -> Optional[str]:
        """Добавляет визуально-ориентированное улучшение к ответу"""
        try:
            if not self.detect_visual_content(user_message):
                return None
            
            task_type = self.get_visual_task_type(user_message)
            
            # Определяем область экспертизы
            message_lower = user_message.lower()
            expertise_area = None
            
            if any(word in message_lower for word in ['фото', 'снимок', 'съемка']):
                expertise_area = 'photography'
            elif any(word in message_lower for word in ['дизайн', 'макет', 'композиция']):
                expertise_area = 'design'
            elif any(word in message_lower for word in ['искусство', 'картина', 'художник']):
                expertise_area = 'art_analysis'
            elif any(word in message_lower for word in ['схема', 'чертеж', 'диаграмма']):
                expertise_area = 'technical_analysis'
            
            if expertise_area and expertise_area in self.visual_expertise:
                tip = random.choice(self.visual_expertise[expertise_area]['tips'])
                area_name = self.visual_expertise[expertise_area]['ru']
                
                return f"""
💡 <b>Визуальная экспертиза</b> ({area_name}):
<blockquote>{tip}</blockquote>

<i>🎯 Powered by LLaVA-inspired multimodal intelligence</i>"""
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка создания визуального улучшения: {e}")
            return None

    async def ensure_initialization(self):
        """Убеждаемся что инициализация выполнена"""
        global _initialization_done
        if not _initialization_done:
            await self.create_llava_tables()
            _initialization_done = True

    async def get_dataset_stats(self) -> Dict[str, Any]:
        """Возвращает статистику LLaVA возможностей"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                stats = {}
                
                # Считаем визуальные паттерны
                async with db.execute("SELECT COUNT(*) FROM llava_visual_patterns WHERE pattern_type = 'visual_task'") as cursor:
                    row = await cursor.fetchone()
                    stats['visual_tasks'] = row[0] if row else 0
                
                # Считаем экспертные советы
                async with db.execute("SELECT COUNT(*) FROM llava_visual_patterns WHERE pattern_type = 'expert_tip'") as cursor:
                    row = await cursor.fetchone()
                    stats['expert_tips'] = row[0] if row else 0
                
                # Считаем области экспертизы
                async with db.execute("SELECT COUNT(DISTINCT expertise_area) FROM llava_visual_patterns") as cursor:
                    row = await cursor.fetchone()
                    stats['expertise_areas'] = row[0] if row else 0
                
                return {
                    'total_visual_patterns': stats['visual_tasks'] + stats['expert_tips'],
                    'visual_tasks': stats['visual_tasks'],
                    'expert_tips': stats['expert_tips'],
                    'expertise_areas': stats['expertise_areas'],
                    'capabilities': [
                        'Анализ изображений',
                        'Распознавание объектов',
                        'Чтение текста на изображениях',
                        'Понимание сцен',
                        'Визуальное рассуждение',
                        'Профессиональная экспертиза'
                    ]
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики LLaVA: {e}")
            return {'error': str(e)}

# Флаг инициализации должен быть определен ДО создания экземпляра
_initialization_done = False

# Глобальный экземпляр сервиса
llava_intelligence = LLaVAIntelligenceService()

async def initialize_llava_service():
    """Инициализирует LLaVA сервис"""
    try:
        await llava_intelligence.create_llava_tables()
        logger.info("✅ LLaVA Intelligence Service инициализирован")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации LLaVA сервиса: {e}")

async def ensure_initialization():
    """Убеждаемся что инициализация выполнена"""
    global _initialization_done
    if not _initialization_done:
        await initialize_llava_service()
        _initialization_done = True