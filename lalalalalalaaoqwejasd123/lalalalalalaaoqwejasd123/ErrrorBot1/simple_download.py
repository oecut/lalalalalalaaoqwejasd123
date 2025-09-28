#!/usr/bin/env python3
# Простое скачивание файлов с HuggingFace

import requests
import os

def download_file_simple(url, filename, folder="database"):
    """
    Простое скачивание файла по прямой ссылке
    """
    try:
        print(f"📥 Скачиваем: {filename}")
        
        # Создаём папку
        os.makedirs(folder, exist_ok=True)
        
        # Скачиваем файл
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        filepath = os.path.join(folder, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Проверяем размер
        size = os.path.getsize(filepath) / (1024*1024)
        print(f"✅ Скачан: {filepath} ({size:.1f} MB)")
        return filepath
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    print("📦 Простое скачивание с HuggingFace")
    print("=" * 50)
    
    # Пример прямых ссылок на файлы с HuggingFace
    # Для датасета openai/gdpval (который на вашем скриншоте)
    files_to_download = [
        {
            "url": "https://huggingface.co/datasets/openai/gdpval/resolve/main/data/train-00000-of-00001-d52c0ad0a0f92c33.parquet",
            "filename": "gdpval_train.parquet"
        }
    ]
    
    # Скачиваем файлы
    for file_info in files_to_download:
        download_file_simple(file_info["url"], file_info["filename"])
    
    print("\n💡 Как найти прямые ссылки:")
    print("1. Откройте датасет на HuggingFace")
    print("2. Перейдите на вкладку 'Files and versions'") 
    print("3. Щёлкните правой кнопкой на файл → 'Копировать адрес ссылки'")
    print("4. Вставьте ссылку в этот скрипт")