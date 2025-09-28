#!/usr/bin/env python3
# Скрипт для загрузки датасетов с HuggingFace в папку database

from datasets import load_dataset
import sqlite3
import os

def download_dataset_to_db(dataset_name, table_name="dataset_data"):
    """
    Загружает датасет с HuggingFace и сохраняет в SQLite
    
    Примеры датасетов:
    - "squad" - вопросы и ответы
    - "imdb" - отзывы фильмов  
    - "emotion" - эмоции в тексте
    - "wikitext" - тексты из википедии
    """
    try:
        print(f"📥 Загружаем датасет: {dataset_name}")
        
        # Загружаем датасет
        dataset = load_dataset(dataset_name)
        
        # Берём тренировочную часть (или другую доступную)
        if 'train' in dataset:
            data = dataset['train']
        else:
            # Берём первую доступную часть
            split_name = list(dataset.keys())[0]
            data = dataset[split_name]
            print(f"ℹ️ Используем часть: {split_name}")
        
        # Конвертируем в pandas
        df = data.to_pandas()
        print(f"✅ Загружено {len(df)} записей")
        
        # Сохраняем в SQLite
        db_path = "database/datasets.db"
        conn = sqlite3.connect(db_path)
        
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"💾 Сохранено в {db_path}, таблица '{table_name}'")
        
        # Показываем структуру
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print("\n📋 Структура таблицы:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]}")
        
        # Показываем пример данных
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        sample = cursor.fetchall()
        print(f"\n🔍 Первые 3 записи:")
        for i, row in enumerate(sample, 1):
            print(f"  {i}. {row}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    # Примеры популярных датасетов
    datasets_to_try = [
        ("emotion", "emotions"),  # Эмоции в тексте
        ("squad", "qa_data"),     # Вопросы и ответы  
        ("imdb", "movie_reviews") # Отзывы на фильмы
    ]
    
    print("🤖 Скрипт загрузки датасетов HuggingFace")
    print("=" * 50)
    
    for dataset_name, table_name in datasets_to_try:
        download_dataset_to_db(dataset_name, table_name)
        print("-" * 50)