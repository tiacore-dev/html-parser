# Журнал изменений

## [Unreleased]

### Добавлено

- Новые партнёры в `PARSER_REGISTRY` (`app/parsers/parse_main.py`), использующие существующие парсеры без изменений:
  - `arsexpress_2` — партнёр `637276a0-d453-11f1-9929-f403433d1b1b`, парсер `ArsexpressParser` («Арсэкспресс»).
  - `plex_post_2` — партнёр `6e1759c5-ad4d-11ef-b438-d85ed3a38e2b`, парсер `PlexPostParser` («Плекс Пост»).
  - `plex_post_3` — партнёр `6d033b1a-280e-11ed-8113-74d43522d93b`, парсер `PlexPostParser` («Плекс Пост»).
  - `plex_post_4` — партнёр `b4a37738-bb21-11e7-9bdb-74d43522d93b`, парсер `PlexPostParser` («Плекс Пост»).
- Новые партнёры автоматически участвуют в плановом парсинге и доступны через отладочные эндпоинты `/api/dev/parsers/...`.
- `README.md` с описанием проекта.
- Переменные окружения `NOTIFICATION_SERVICE_URL`, `NOTIFICATION_SERVICE_API_KEY`, `NOTIFICATION_SERVICE_ENABLED` (по умолчанию `false`).

Существующие регистрации `arsexpress` и `plex_post` не изменены.

### Изменено

- Telegram-уведомления приложения (отчёт по парсингу и ошибки выставления статуса в SVS) отправляются через Notification Service (`POST /notifications/telegram/send`) вместо прямых запросов к Telegram API. Используются существующие `BOT_TOKEN` и `CHAT_ID`.
- **Важно для деплоя:** уведомления по умолчанию выключены. Чтобы они продолжили приходить, на сервере нужно задать `NOTIFICATION_SERVICE_ENABLED=true`, `NOTIFICATION_SERVICE_URL` и `NOTIFICATION_SERVICE_API_KEY`.
- `example.env` приведён в соответствие с кодом: добавлены все используемые переменные с заглушками, удалены неиспользуемые (`DATABASE_URL`, `JWT_SECRET_KEY`, `LOGIN`, `PASSWORD`, `FLASK_PORT`).
- Уведомления отправляются простым текстом: Markdown-разметка (`*`, `` ` ``) из отчёта убрана.
- В строках отчёта с ошибкой партнёра теперь указывается ID партнёра.
- Ошибки доставки уведомлений только логируются и не прерывают парсинг.

### Удалено

- Зависимость `aiogram` из `requirements.scheduler.txt` — больше не используется.
