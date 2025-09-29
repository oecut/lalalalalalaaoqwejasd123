# /ErrrorBot/app/services/database.py

import aiosqlite
import logging
import json
import asyncio
from typing import Optional, List, Tuple, Dict
from datetime import date, datetime
from contextlib import asynccontextmanager

DB_PATH = 'database/database.db'

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection_lock = asyncio.Lock()
        self._connection = None

    @asynccontextmanager
    async def get_connection(self):
        """Получает переиспользуемое соединение с БД"""
        async with self._connection_lock:
            if self._connection is None:
                self._connection = await aiosqlite.connect(self.db_path)
                # Включаем WAL mode для лучшей производительности
                await self._connection.execute("PRAGMA journal_mode=WAL")
                await self._connection.execute("PRAGMA synchronous=NORMAL")
                await self._connection.execute("PRAGMA cache_size=10000")
                await self._connection.execute("PRAGMA temp_store=memory")
        
        try:
            yield self._connection
        finally:
            pass  # Соединение остается открытым для переиспользования

    async def close(self):
        """Закрывает соединение с БД"""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def _execute(self, query: str, params: tuple = (), fetch: str = None):
        """Выполняет SQL-запрос с переиспользованием соединения"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute(query, params)
                if fetch == 'one': 
                    result = await cursor.fetchone()
                    return result[0] if result and len(result) == 1 else result
                elif fetch == 'all': 
                    return await cursor.fetchall()
                await db.commit()
        except aiosqlite.Error as e:
            logging.error(f"Ошибка базы данных: {e}")
            # При ошибке пересоздаем соединение
            if self._connection:
                try:
                    await self._connection.close()
                except:
                    pass
                self._connection = None
            return None

    async def _execute_many(self, query: str, params_list: List[tuple]):
        """Выполняет батч-вставку"""
        try:
            async with self.get_connection() as db:
                await db.executemany(query, params_list)
                await db.commit()
        except aiosqlite.Error as e:
            logging.error(f"Ошибка батч-вставки: {e}")
            return False
        return True

    async def _column_exists(self, table_name: str, column_name: str) -> bool:
        """Проверяет существование колонки в таблице"""
        try:
            result = await self._execute(f"PRAGMA table_info({table_name})", fetch='all')
            if result:
                columns = [row[1] for row in result]
                return column_name in columns
            return False
        except:
            return False

    async def initialize(self):
        # Основная таблица пользователей с отслеживанием статуса
        await self._execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, 
                username TEXT, 
                first_name TEXT, 
                registration_date DATETIME DEFAULT CURRENT_TIMESTAMP, 
                daily_requests INTEGER DEFAULT 0, 
                last_request_date DATE DEFAULT CURRENT_DATE,
                is_blocked BOOLEAN DEFAULT 0,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создаем индексы для оптимизации
        await self._execute("CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity)")
        await self._execute("CREATE INDEX IF NOT EXISTS idx_users_is_blocked ON users(is_blocked)")
        
        # Таблица стилей пользователей
        await self._execute('''
            CREATE TABLE IF NOT EXISTS user_styles (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_id INTEGER NOT NULL, 
                style_name TEXT NOT NULL, 
                style_prompt TEXT NOT NULL, 
                is_active BOOLEAN DEFAULT 0, 
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Индексы для стилей
        await self._execute("CREATE INDEX IF NOT EXISTS idx_user_styles_user_id ON user_styles(user_id)")
        await self._execute("CREATE INDEX IF NOT EXISTS idx_user_styles_active ON user_styles(user_id, is_active)")
        
        # Глобальная статистика
        await self._execute('''
            CREATE TABLE IF NOT EXISTS global_stats (
                stat_key TEXT PRIMARY KEY, 
                stat_value INTEGER DEFAULT 0
            )
        ''')
        
        # Демо-триггеры с поддержкой сохранения сущностей
        await self._execute('''
            CREATE TABLE IF NOT EXISTS demo_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_id INTEGER NOT NULL, 
                trigger_text TEXT NOT NULL, 
                responses TEXT NOT NULL, 
                is_animated BOOLEAN DEFAULT 1,
                entities TEXT DEFAULT NULL,
                UNIQUE(user_id, trigger_text)
            )
        ''')
        
        # Индексы для демо-триггеров
        await self._execute("CREATE INDEX IF NOT EXISTS idx_demo_triggers_user_id ON demo_triggers(user_id)")
        await self._execute("CREATE INDEX IF NOT EXISTS idx_demo_triggers_lookup ON demo_triggers(user_id, trigger_text)")
        
        # Обновленная таблица групповых чатов с количеством участников
        await self._execute('''
            CREATE TABLE IF NOT EXISTS group_chats (
                chat_id INTEGER PRIMARY KEY, 
                chat_title TEXT, 
                added_by INTEGER NOT NULL, 
                added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                member_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Индексы для групп
        await self._execute("CREATE INDEX IF NOT EXISTS idx_group_chats_added_by ON group_chats(added_by)")
        
        # Таблица групповых стилей
        await self._execute('''
            CREATE TABLE IF NOT EXISTS group_styles (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                chat_id INTEGER NOT NULL, 
                style_name TEXT NOT NULL, 
                style_prompt TEXT NOT NULL, 
                is_active BOOLEAN DEFAULT 0, 
                added_by INTEGER NOT NULL, 
                FOREIGN KEY (chat_id) REFERENCES group_chats (chat_id)
            )
        ''')
        
        # Индексы для групповых стилей
        await self._execute("CREATE INDEX IF NOT EXISTS idx_group_styles_chat_id ON group_styles(chat_id)")
        await self._execute("CREATE INDEX IF NOT EXISTS idx_group_styles_active ON group_styles(chat_id, is_active)")
        
        # Безопасное добавление новых колонок с проверкой существования
        try:
            if not await self._column_exists('users', 'is_blocked'):
                await self._execute('ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT 0')
                logging.info("Добавлена колонка is_blocked в таблицу users")
                
            if not await self._column_exists('users', 'last_activity'):
                await self._execute('ALTER TABLE users ADD COLUMN last_activity DATETIME DEFAULT CURRENT_TIMESTAMP')
                logging.info("Добавлена колонка last_activity в таблицу users")
        except Exception as e:
            logging.warning(f"Ошибка при добавлении колонок в users: {e}")
            
        try:
            if not await self._column_exists('group_chats', 'member_count'):
                await self._execute('ALTER TABLE group_chats ADD COLUMN member_count INTEGER DEFAULT 0')
                logging.info("Добавлена колонка member_count в таблицу group_chats")
                
            if not await self._column_exists('group_chats', 'last_updated'):
                await self._execute('ALTER TABLE group_chats ADD COLUMN last_updated DATETIME DEFAULT CURRENT_TIMESTAMP')
                logging.info("Добавлена колонка last_updated в таблицу group_chats")
        except Exception as e:
            logging.warning(f"Ошибка при добавлении колонок в group_chats: {e}")
            
        try:
            if not await self._column_exists('demo_triggers', 'entities'):
                await self._execute('ALTER TABLE demo_triggers ADD COLUMN entities TEXT DEFAULT NULL')
                logging.info("Добавлена колонка entities в таблицу demo_triggers")
        except Exception as e:
            logging.warning(f"Ошибка при добавлении колонки entities в demo_triggers: {e}")
        
        logging.info("База данных успешно инициализирована.")

    async def add_or_update_user(self, user_id: int, username: str, first_name: str):
        query = '''
            INSERT INTO users (user_id, username, first_name, is_blocked, last_activity) 
            VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP) 
            ON CONFLICT(user_id) DO UPDATE SET 
                username=excluded.username, 
                first_name=excluded.first_name, 
                is_blocked=0,
                last_activity=CURRENT_TIMESTAMP
        '''
        await self._execute(query, (user_id, username, first_name))

    async def mark_user_blocked(self, user_id: int):
        """Отмечает пользователя как заблокировавшего бота"""
        await self._execute("UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,))

    async def get_user_requests_count(self, user_id: int) -> Optional[int]:
        """ИСПРАВЛЕНО: правильная обработка типов данных"""
        result = await self._execute("SELECT daily_requests, last_request_date FROM users WHERE user_id = ?", (user_id,), fetch='one')
        if not result: 
            return None
        
        daily_requests, last_request_date_str = result
        today = date.today()
        
        # Исправление: проверяем тип и обрабатываем корректно
        try:
            if isinstance(last_request_date_str, str):
                last_request_date = date.fromisoformat(last_request_date_str)
            elif hasattr(last_request_date_str, 'year'):  # date объект
                last_request_date = last_request_date_str
            else:
                # Неизвестный формат, считаем что сегодня
                last_request_date = today
        except (ValueError, TypeError):
            # Если не удалось парсить дату, считаем что сегодня
            last_request_date = today
        
        if last_request_date != today:
            await self._execute("UPDATE users SET daily_requests = 0, last_request_date = ? WHERE user_id = ?", (today.isoformat(), user_id))
            return 0
        return daily_requests

    async def increment_user_requests(self, user_id: int, service_type: str):
        # Используем батч для атомарных операций
        queries_params = [
            ("UPDATE users SET daily_requests = daily_requests + 1, last_activity = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,)),
            (f"INSERT INTO global_stats (stat_key, stat_value) VALUES ('total_{service_type}', 1) ON CONFLICT(stat_key) DO UPDATE SET stat_value = stat_value + 1", ()),
            ("INSERT INTO global_stats (stat_key, stat_value) VALUES ('total_requests_all_time', 1) ON CONFLICT(stat_key) DO UPDATE SET stat_value = stat_value + 1", ())
        ]
        
        async with self.get_connection() as db:
            try:
                for query, params in queries_params:
                    await db.execute(query, params)
                await db.commit()
            except Exception as e:
                await db.rollback()
                logging.error(f"Ошибка в increment_user_requests: {e}")

    async def add_user_style(self, user_id: int, style_name: str, style_prompt: str):
        await self._execute("INSERT INTO user_styles (user_id, style_name, style_prompt) VALUES (?, ?, ?)", (user_id, style_name, style_prompt))

    async def get_user_styles(self, user_id: int) -> List[Tuple[int, str, bool]]:
        return await self._execute("SELECT id, style_name, is_active FROM user_styles WHERE user_id = ?", (user_id,), fetch='all') or []

    async def set_active_style(self, user_id: int, style_id: int):
        async with self.get_connection() as db:
            try:
                await db.execute("UPDATE user_styles SET is_active = 0 WHERE user_id = ?", (user_id,))
                await db.execute("UPDATE user_styles SET is_active = 1 WHERE user_id = ? AND id = ?", (user_id, style_id))
                await db.commit()
            except Exception as e:
                await db.rollback()
                logging.error(f"Ошибка в set_active_style: {e}")

    async def get_active_style_prompt(self, user_id: int) -> Optional[str]:
        query = "SELECT style_prompt FROM user_styles WHERE user_id = ? AND is_active = 1"
        return await self._execute(query, (user_id,), fetch='one')

    # === МЕТОДЫ ДЛЯ ГРУППОВЫХ ЧАТОВ ===
    async def add_group_chat(self, chat_id: int, chat_title: str, added_by: int, member_count: int = 0):
        """Добавляет/обновляет групповой чат в базу данных с количеством участников"""
        query = '''
            INSERT OR REPLACE INTO group_chats (chat_id, chat_title, added_by, member_count, last_updated) 
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        '''
        await self._execute(query, (chat_id, chat_title, added_by, member_count))

    async def update_group_member_count(self, chat_id: int, member_count: int):
        """Обновляет количество участников в групповом чате"""
        await self._execute(
            "UPDATE group_chats SET member_count = ?, last_updated = CURRENT_TIMESTAMP WHERE chat_id = ?", 
            (member_count, chat_id)
        )

    async def get_user_group_chats(self, user_id: int) -> List[Tuple[int, str]]:
        """Получает список групповых чатов, добавленных пользователем"""
        query = "SELECT chat_id, chat_title FROM group_chats WHERE added_by = ?"
        return await self._execute(query, (user_id,), fetch='all') or []

    async def get_all_group_chats(self) -> List[Tuple[int, str, int, str]]:
        """Получает список всех групповых чатов с информацией"""
        query = "SELECT chat_id, chat_title, member_count, datetime(last_updated) FROM group_chats ORDER BY member_count DESC"
        return await self._execute(query, fetch='all') or []

    async def is_group_owner(self, user_id: int, chat_id: int) -> bool:
        """Проверяет, является ли пользователь владельцем группы (тот, кто добавил бота)"""
        query = "SELECT added_by FROM group_chats WHERE chat_id = ?"
        result = await self._execute(query, (chat_id,), fetch='one')
        return result == user_id if result else False

    async def add_group_style(self, chat_id: int, style_name: str, style_prompt: str, added_by: int):
        """Добавляет стиль для группового чата"""
        await self._execute("INSERT INTO group_styles (chat_id, style_name, style_prompt, added_by) VALUES (?, ?, ?, ?)", 
                           (chat_id, style_name, style_prompt, added_by))

    async def get_group_styles(self, chat_id: int) -> List[Tuple[int, str, bool]]:
        """Получает список стилей для группового чата"""
        return await self._execute("SELECT id, style_name, is_active FROM group_styles WHERE chat_id = ?", (chat_id,), fetch='all') or []

    async def set_active_group_style(self, chat_id: int, style_id: int):
        """Устанавливает активный стиль для группового чата"""
        async with self.get_connection() as db:
            try:
                await db.execute("UPDATE group_styles SET is_active = 0 WHERE chat_id = ?", (chat_id,))
                await db.execute("UPDATE group_styles SET is_active = 1 WHERE chat_id = ? AND id = ?", (chat_id, style_id))
                await db.commit()
            except Exception as e:
                await db.rollback()
                logging.error(f"Ошибка в set_active_group_style: {e}")

    async def get_active_group_style_prompt(self, chat_id: int) -> Optional[str]:
        """Получает активный системный промпт для группового чата"""
        query = "SELECT style_prompt FROM group_styles WHERE chat_id = ? AND is_active = 1"
        return await self._execute(query, (chat_id,), fetch='one')

    # === ОПТИМИЗИРОВАННАЯ СТАТИСТИКА ===
    async def get_basic_stats(self) -> Dict[str, int]:
        """Получает базовые статистики одним запросом"""
        # Используем CTE для эффективности
        query = '''
        WITH stats AS (
            SELECT 
                (SELECT COUNT(*) FROM users WHERE is_blocked = 0) as total_users,
                (SELECT COUNT(*) FROM users WHERE last_activity >= date('now', '-7 days') AND is_blocked = 0) as active_users,
                (SELECT COUNT(*) FROM users WHERE is_blocked = 1) as blocked_users,
                (SELECT COUNT(*) FROM group_chats) as total_groups,
                (SELECT COALESCE(SUM(member_count), 0) FROM group_chats) as total_group_members
        )
        SELECT * FROM stats
        '''
        result = await self._execute(query, fetch='one')
        
        if result:
            return {
                'total_users': result[0],
                'active_users': result[1], 
                'blocked_users': result[2],
                'total_groups': result[3],
                'total_group_members': result[4]
            }
        return {}

    async def get_global_stats(self) -> Dict[str, int]:
        """Получает глобальные статистики без рекурсии"""
        stats = {}
        
        # Получаем статистику из global_stats таблицы
        global_query = "SELECT stat_key, stat_value FROM global_stats WHERE stat_key IN ('total_requests_all_time', 'total_text')"
        global_results = await self._execute(global_query, fetch='all')
        
        for key, value in (global_results or []):
            stats[key] = value
            
        # Добавляем значения по умолчанию если их нет
        stats.setdefault('total_requests_all_time', 0)
        stats.setdefault('total_text', 0)
        
        return stats

    async def get_user_stats(self, user_id: int) -> Optional[Dict[str, int]]:
        """Оптимизированная версия статистики пользователя"""
        if user_id == 0:
            user_req_today = 0
        else:
            user_req_today = await self.get_user_requests_count(user_id)
            if user_req_today is None:
                return None
        
        # Получаем все статистики одним запросом
        basic_stats = await self.get_basic_stats()
        global_stats = await self.get_global_stats()
        
        result = {
            'user_today_total': user_req_today,
            **basic_stats,
            **global_stats
        }
        
        return result

    async def get_extended_stats(self) -> Dict[str, int]:
        """Получает расширенную статистику для админки одним запросом"""
        basic_stats = await self.get_basic_stats()
        global_stats = await self.get_global_stats()
        
        return {**basic_stats, **global_stats}

    async def get_all_user_ids(self) -> List[int]:
        rows = await self._execute("SELECT user_id FROM users WHERE is_blocked = 0", fetch='all')
        return [row[0] for row in rows] if rows else []

    async def get_all_group_chat_ids(self) -> List[int]:
        """Получает ID всех групповых чатов"""
        rows = await self._execute("SELECT chat_id FROM group_chats", fetch='all')
        return [row[0] for row in rows] if rows else []

    # === ДЕМО РЕЖИМ ===
    async def get_demo_trigger(self, user_id: int, text: str) -> Optional[Tuple[List[str], bool, Optional[dict]]]:
        """Возвращает кортеж (responses, is_animated, entities)"""
        query = "SELECT responses, is_animated, entities FROM demo_triggers WHERE user_id = ? AND trigger_text = ?"
        result = await self._execute(query, (user_id, text), fetch='one')
        if result:
            try:
                responses_json, is_animated, entities_json = result
                responses = json.loads(responses_json)
                entities = json.loads(entities_json) if entities_json else None
                return (responses, bool(is_animated), entities)
            except json.JSONDecodeError:
                logging.error(f"Ошибка декодирования JSON для триггера {user_id}:{text}")
                return None
        return None

    async def add_demo_trigger(self, user_id: int, trigger_text: str, responses: List[str], 
                              is_animated: bool = True, entities: Optional[List] = None):
        """Добавляет демо-триггер с поддержкой сущностей"""
        responses_json = json.dumps(responses, ensure_ascii=False)
        entities_json = json.dumps(entities, ensure_ascii=False) if entities else None
        query = """
            INSERT OR REPLACE INTO demo_triggers 
            (user_id, trigger_text, responses, is_animated, entities) 
            VALUES (?, ?, ?, ?, ?)
        """
        await self._execute(query, (user_id, trigger_text, responses_json, is_animated, entities_json))

    async def get_all_demo_triggers(self) -> List[Tuple[int, int, str, bool]]:
        """Возвращает список (id, user_id, trigger_text, is_animated)"""
        return await self._execute("SELECT id, user_id, trigger_text, is_animated FROM demo_triggers", fetch='all') or []

    async def delete_demo_trigger(self, trigger_id: int):
        await self._execute("DELETE FROM demo_triggers WHERE id = ?", (trigger_id,))

# Создаем глобальный экземпляр
db = Database(DB_PATH)

# Добавляем cleanup функцию для корректного закрытия
import atexit

def cleanup_db():
    """Функция для корректного закрытия соединения при завершении"""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(db.close())
    except RuntimeError:
        # Если нет активного loop, создаем новый
        asyncio.run(db.close())

atexit.register(cleanup_db)