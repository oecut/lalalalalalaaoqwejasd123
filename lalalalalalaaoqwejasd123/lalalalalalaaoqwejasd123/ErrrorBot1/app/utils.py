# /ErrrorBot/app/utils.py

import re
import html

def escape_html(text: str) -> str:
    """Экранирует специальные HTML символы в строке."""
    if not isinstance(text, str):
        text = str(text)
    return html.escape(text)

def format_ai_response_to_html(text: str) -> str:
    """
    Преобразует ответ ИИ из Markdown в HTML для Telegram.
    Корректно обрабатывает все элементы форматирования.
    """
    if not text:
        return ""
    
    # Базовая очистка
    text = text.strip()
    
    # Убираем экранирующие символы
    text = re.sub(r'\\(.)', r'\1', text)
    
    # Преобразуем заголовки в жирный текст
    text = re.sub(r'^#{1,6}\s+(.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    
    # Преобразуем блоки кода в код (до обработки инлайн кода)
    text = re.sub(r'```(?:\w+\n)?([\s\S]*?)```', r'<code>\1</code>', text)
    
    # Преобразуем жирный текст (**text** или __text__)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
    
    # Преобразуем курсив (*text* или _text_) - только одиночные символы
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!_)_([^_]+?)_(?!_)', r'<i>\1</i>', text)
    
    # Преобразуем инлайн код (`text`)
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
    
    # Очистка лишних переносов
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text.strip()

def split_long_message(text: str, max_length: int = 4096) -> list:
    """
    Разделяет длинное сообщение на части, сохраняя HTML-форматирование.
    Старается разделять по логическим границам (переносы строк, предложения).
    """
    if len(text) <= max_length:
        return [text]
    
    # Список частей сообщения
    parts = []
    current_part = ""
    
    # Разделяем по абзацам (двойные переносы)
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        # Если добавление абзаца не превышает лимит
        if len(current_part + '\n\n' + paragraph) <= max_length:
            if current_part:
                current_part += '\n\n' + paragraph
            else:
                current_part = paragraph
        else:
            # Если current_part не пустой, сохраняем его
            if current_part:
                parts.append(current_part)
                current_part = ""
            
            # Если сам абзац слишком длинный, разделяем его
            if len(paragraph) > max_length:
                # Разделяем по предложениям
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                
                for sentence in sentences:
                    # Если добавление предложения не превышает лимит
                    if len(current_part + ' ' + sentence) <= max_length:
                        if current_part:
                            current_part += ' ' + sentence
                        else:
                            current_part = sentence
                    else:
                        # Сохраняем накопленную часть
                        if current_part:
                            parts.append(current_part)
                            current_part = ""
                        
                        # Если само предложение слишком длинное, разделяем принудительно
                        if len(sentence) > max_length:
                            words = sentence.split()
                            for word in words:
                                if len(current_part + ' ' + word) <= max_length:
                                    if current_part:
                                        current_part += ' ' + word
                                    else:
                                        current_part = word
                                else:
                                    if current_part:
                                        parts.append(current_part)
                                        current_part = word
                                    else:
                                        # Если слово само по себе слишком длинное
                                        parts.append(word[:max_length-3] + "...")
                        else:
                            current_part = sentence
            else:
                current_part = paragraph
    
    # Добавляем последнюю часть, если она есть
    if current_part:
        parts.append(current_part)
    
    # Убеждаемся, что ни одна часть не превышает лимит
    final_parts = []
    for part in parts:
        if len(part) <= max_length:
            final_parts.append(part)
        else:
            # Принудительное разделение очень длинных частей
            while len(part) > max_length:
                split_point = max_length - 3
                final_parts.append(part[:split_point] + "...")
                part = "..." + part[split_point:]
            if part:
                final_parts.append(part)
    
    # Добавляем индикаторы частей, если сообщение разделено
    if len(final_parts) > 1:
        for i in range(len(final_parts)):
            final_parts[i] = f"<i>[Часть {i+1}/{len(final_parts)}]</i>\n\n" + final_parts[i]
    
    return final_parts

def format_final_message_html(user_name: str, query: str, ai_response: str) -> str:
    """
    Форматирует финальный ответ с корректным отображением цитаты и ответа ИИ.
    """
    # Экранируем пользовательский ввод
    safe_user_name = escape_html(user_name)
    safe_query = escape_html(query)
    
    # Форматируем ответ ИИ
    formatted_ai_response = format_ai_response_to_html(ai_response)
    
    # Формируем финальное сообщение в новом формате
    final_message = (
        f"<blockquote>{safe_user_name}: {safe_query}</blockquote>\n\n"
        f"<b>💬 {formatted_ai_response}</b>"
    )
    
    return final_message