# CyberGram Android Mod

Модифицированная версия Telegram с функциями приватности.

## Изменения:
- Название: CyberGram
- Добавлена кнопка "Cyber Sec" в боковом меню
- Экран с функциями анонимности

## API Ключи:
Вставьте ваши Telegram API ключи в файл:
`TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java`

Строки 29-30:
```java
public static int APP_ID = ВАШ_APP_ID;
public static String APP_HASH = "ВАШ_APP_HASH";
```

Получить ключи: https://my.telegram.org

## Сборка APK:
Используйте Android Studio для сборки проекта.
