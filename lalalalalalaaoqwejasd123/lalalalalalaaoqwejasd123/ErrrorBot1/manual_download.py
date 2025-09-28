#!/usr/bin/env python3
# Ручное скачивание датасетов с HuggingFace в папку database

import os
import requests
from huggingface_hub import hf_hub_download, list_repo_files

def download_dataset_files(repo_id, save_to_folder="database"):
    """
    Скачивает все файлы датасета в указанную папку
    """
    try:
        print(f"📥 Скачиваем датасет: {repo_id}")
        
        # Создаём папку если её нет
        os.makedirs(save_to_folder, exist_ok=True)
        
        # Получаем список всех файлов в репозитории
        files = list_repo_files(repo_id, repo_type="dataset")
        
        # Фильтруем только файлы данных (не README, .gitattributes и т.д.)
        data_files = [f for f in files if f.endswith(('.parquet', '.csv', '.json', '.jsonl', '.txt'))]
        
        print(f"📋 Найдено {len(data_files)} файлов данных:")
        for file in data_files:
            print(f"  - {file}")
        
        # Скачиваем каждый файл
        downloaded_files = []
        for file in data_files:
            try:
                print(f"⬇️ Скачиваем: {file}")
                
                # Скачиваем файл
                local_path = hf_hub_download(
                    repo_id=repo_id,
                    filename=file,
                    repo_type="dataset",
                    local_dir=save_to_folder,
                    local_dir_use_symlinks=False
                )
                
                # Получаем размер файла
                size = os.path.getsize(local_path) / (1024*1024)  # MB
                print(f"✅ Скачан: {file} ({size:.1f} MB)")
                downloaded_files.append(local_path)
                
            except Exception as e:
                print(f"❌ Ошибка при скачивании {file}: {e}")
        
        print(f"\n🎉 Скачано {len(downloaded_files)} файлов в папку '{save_to_folder}'")
        return downloaded_files
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def download_specific_file(repo_id, filename, save_to_folder="database"):
    """
    Скачивает конкретный файл из датасета
    """
    try:
        print(f"📥 Скачиваем файл: {filename} из {repo_id}")
        
        os.makedirs(save_to_folder, exist_ok=True)
        
        local_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset", 
            local_dir=save_to_folder,
            local_dir_use_symlinks=False
        )
        
        size = os.path.getsize(local_path) / (1024*1024)
        print(f"✅ Файл скачан: {local_path} ({size:.1f} MB)")
        return local_path
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

if __name__ == "__main__":
    print("📦 Скрипт ручного скачивания датасетов HuggingFace")
    print("=" * 60)
    
    # Скачиваем датасет который вы показали на скриншоте
    repo_id = "openai/gdpval"
    
    print(f"🎯 Скачиваем: {repo_id}")
    files = download_dataset_files(repo_id)
    
    if files:
        print(f"\n📁 Файлы сохранены в папке 'database/':")
        for file in files:
            print(f"  • {file}")
    
    print("\n" + "=" * 60)
    print("💡 Для скачивания других датасетов замените repo_id")
    print("   Например: 'squad', 'imdb', 'emotion'")