#!/bin/bash
# Простые команды для скачивания файлов с HuggingFace

echo "📦 Скачивание датасетов с HuggingFace в папку database/"

# Создаём папку для датасетов
mkdir -p database/downloaded_datasets

echo "📥 Скачиваем файлы..."

# Для датасета openai/gdpval (с вашего скриншота)
# Замените ссылки на актуальные с сайта
wget -O "database/downloaded_datasets/gdpval_train.parquet" \
  "https://huggingface.co/datasets/openai/gdpval/resolve/main/data/train-00000-of-00001-d52c0ad0a0f92c33.parquet"

# Другие популярные датасеты (примеры)
# wget -O "database/downloaded_datasets/emotions.csv" \
#   "https://huggingface.co/datasets/emotion/resolve/main/data/train.csv"

echo "✅ Готово! Файлы сохранены в database/downloaded_datasets/"
echo ""
echo "💡 Как найти ссылки:"
echo "1. Откройте https://huggingface.co/datasets/НАЗВАНИЕ_ДАТАСЕТА"
echo "2. Перейдите на вкладку 'Files and versions'"
echo "3. Щёлкните правой кнопкой на файл → 'Копировать адрес ссылки'"
echo "4. Замените ссылку в этом скрипте"
echo ""
echo "📋 Структура ссылок HuggingFace:"
echo "https://huggingface.co/datasets/АВТОР/ДАТАСЕТ/resolve/main/ПУТЬ_К_ФАЙЛУ"