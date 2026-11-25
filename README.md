# SVS Parser (html-parser)

Сервис автоматически отслеживает доставку заказов, переданных сторонним курьерским службам. Он получает из SVS список заказов партнёра, открывает сайт отслеживания перевозчика через Selenium, ищет признак «Доставлено» и при его наличии выставляет заказу статус доставки в SVS.

## Задачи сервиса

- Получение незакрытых заказов каждого партнёра из SVS.
- Парсинг страниц отслеживания перевозчиков (headless Firefox).
- Выставление в SVS даты доставки и получателя для доставленных заказов.
- Запись результата по каждому заказу в таблицу `parsing_log`.
- Отправка сводного отчёта и ошибок выставления статуса в Telegram.
- HTTP API для просмотра логов и ручной отладки парсеров.

## Стек и архитектура

- Python 3.12, FastAPI + Gunicorn/Uvicorn (веб-API).
- APScheduler (планировщик), Selenium + Firefox ESR + geckodriver + Xvfb (парсинг).
- Tortoise ORM + PostgreSQL (asyncpg) — хранение логов парсинга.
- httpx — уведомления в Telegram через Notification Service; loguru — логирование.

Проект состоит из двух процессов (отдельные Docker-образы):

| Процесс | Точка входа | Назначение |
|---|---|---|
| `scheduler` | `schedule_run.py` → `app/scheduler.py` | Плановый запуск парсинга всех партнёров |
| `web` | `run.py` → `app/web_app.py` | REST API: логи и отладочные эндпоинты |

Основные каталоги:

- `app/parsers/` — парсеры перевозчиков (наследники `BaseParser`), реестр и основной цикл (`parse_main.py`), работа с SVS (`svs.py`).
- `app/routes/` — эндпоинты API.
- `app/handlers/` — проверка API-ключа и отправка сообщений в Telegram.
- `app/database/` — модель `ParsingLog` и инициализация ORM.
- `app/utils/` — создание и закрытие Selenium-драйвера, вспомогательные функции.

## Поддерживаемые перевозчики

| Ключ реестра | ID партнёра в SVS | Парсер | Отображаемое имя |
|---|---|---|---|
| `vip_mail_ufa` | `90b470a2-a775-11e7-ad08-74d43522d93b` | `VIPMailUfaParser` | ВипМайл Уфа |
| `arsexpress` | `1034e0be-855a-11ea-80dd-74d43522d93b` | `ArsexpressParser` | Арсэкспресс |
| `arsexpress_2` | `637276a0-d453-11f1-9929-f403433d1b1b` | `ArsexpressParser` | Арсэкспресс |
| `rasstoyaniya_net` | `b3116f3b-9f4a-11e7-a536-00252274a609` | `RasstoyaniyaNetParser` | Расстояния нет |
| `plex_post` | `d56a2a0c-6339-11e8-80b5-74d43522d93b` | `PlexPostParser` | Плекс Пост |
| `plex_post_2` | `6e1759c5-ad4d-11ef-b438-d85ed3a38e2b` | `PlexPostParser` | Плекс Пост |
| `plex_post_3` | `6d033b1a-280e-11ed-8113-74d43522d93b` | `PlexPostParser` | Плекс Пост |
| `plex_post_4` | `b4a37738-bb21-11e7-9bdb-74d43522d93b` | `PlexPostParser` | Плекс Пост |
| `bizon_express` | `6208860c-f583-11ef-9de4-a1ec92d2beb8` | `BizonExpressParser` | Бизон Экспресс |
| `avis_logistics` | `076db763-9c54-11e7-aa9c-00252274a609` | `AvisLogisticsParser` | Авис-Логистик |
| `sp_service_tyumen` | `26d49356-559c-11eb-80ef-74d43522d93b` | `SPServiceTyumenParser` | СП-Сервис Тюмень |
| `sib_express` | `33c8793d-96c2-11e7-b541-00252274a609` | `SibExpressParser` | Сибирский Экспресс |
| `sp_service_ekaterinburg` | `1d4be527-c61e-11e7-9bdb-74d43522d93b` | `SPServiceEkaterinburgParser` | СП-Сервис Екатеринбург |

Несколько партнёров могут использовать один и тот же парсер: парсер не хранит состояния и ничего не знает об ID партнёра, а заказы запрашиваются и обрабатываются отдельно для каждого ID.

## Реестр парсеров и регистрация партнёра

Реестр — словарь `PARSER_REGISTRY` в `app/parsers/parse_main.py`:

```python
"arsexpress_2": {"partner_id": "637276a0-d453-11f1-9929-f403433d1b1b", "parser": ArsexpressParser()},
```

- Ключ реестра (`parser_key`) используется в отладочных эндпоинтах и должен быть уникальным.
- `partner_id` — ID клиента (партнёра) в SVS, тоже уникальный: из реестра строится словарь `partners` (`partner_id → парсер`), и повторяющийся ID перезапишет предыдущую запись.

Чтобы подключить нового партнёра к существующему перевозчику, достаточно добавить запись в `PARSER_REGISTRY`. Изменения в планировщике, БД или API не нужны: партнёр сразу попадает в плановый парсинг и в отладочные эндпоинты.

Для нового перевозчика нужно создать класс-наследник `BaseParser` с методами `parse(orderno, driver)` и `process_delivered_info(info)`, добавить URL перевозчика в `config.py`/`.env` и зарегистрировать его в реестре.

## Получение заказов и выставление статусов (SVS)

Логика находится в `app/parsers/svs.py` и `process_orders_for_partner()` в `parse_main.py`:

1. `get_orders(partner_id)` — `POST` на `URL_SVS_GET` с телом `{"customer": partner_id}`; ответ — список заказов (`id`, `number`, …). При ошибке сети или JSON возвращается `{"error": ...}`.
2. Для каждого заказа открывается новый Selenium-драйвер и вызывается `parser.parse(number, driver)`:
   - `None` — ошибка парсинга;
   - пустой результат — заказ не найден или нет истории (не считается ошибкой);
   - иначе `parser.process_delivered_info(info)` ищет событие доставки.
3. Если заказ доставлен, `set_orders()` отправляет `POST` на `URL_SVS_SET`: `parcelId` (ID заказа), `recDate` (дата доставки, приводится к формату `ДД.ММ.ГГГГ ЧЧ:ММ:СС`), `recName` (получатель), `comment` (отображаемое имя парсера) и токен авторизации (`USER_KEY`, `TOKEN`).
4. Между заказами делается пауза 15 секунд. Партнёры обрабатываются последовательно; ошибка одного партнёра не останавливает обработку остальных.

## Планировщик

`app/scheduler.py`: `AsyncIOScheduler` с часовым поясом `Asia/Novosibirsk` запускает `parser_main()` по cron каждые 3 часа (`hour="*/3", minute=0`), а также один раз сразу при старте процесса.

## API

Все эндпоинты имеют префикс `/api` и требуют заголовок `X-API-Key` со значением `API_KEY`.

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/logs` | Последние 100 записей `parsing_log` с фильтрами: `date_from`, `date_to`, `partner_id`, `order_number`, `parser_name`, `success`, `status` |
| GET | `/api/dev/parsers` | Список зарегистрированных парсеров (`parser_key`, `partner_id`, `parser_name`) |
| GET | `/api/dev/parsers/{parser_key}/orders` | Заказы партнёра из SVS (без парсинга) |
| POST | `/api/dev/parsers/run` | Парсинг одного номера заказа: `{"parser_key": "...", "order_number": "..."}`. Статус в SVS не выставляется |
| POST | `/api/dev/parsers/{parser_key}/run-all` | Полная обработка всех заказов партнёра, **включая выставление статусов в SVS** |

## Логирование и уведомления

- Логи приложения пишутся через loguru в stdout контейнера (для `scheduler` включена ротация json-file: 10 МБ × 3).
- Результат по каждому заказу сохраняется в таблицу `parsing_log`: `partner_id`, `order_id`, `order_number`, `parser_name`, `success`, `status`, `error_message`, `raw_data`, `parsed_at`.
- В Telegram (через Notification Service, см. ниже) отправляются:
  - сводный отчёт после каждого прогона `parser_main()` — по строке на партнёра с именем, ID партнёра и счётчиками (строки с ошибкой партнёра тоже содержат ID партнёра, так как несколько партнёров могут иметь одинаковое имя парсера);
  - сообщение об ошибке, если SVS не принял статус доставки (имя парсера, ID партнёра, номер и ID заказа, ответ сервера).

## Уведомления через Notification Service

Приложение не обращается к Telegram API напрямую: прямые запросы с продакшен-сервера (Россия) ненадёжны. Сообщения отправляются во внешний Notification Service — тот же, что используется в EK-LS. Реализация: `send_telegram_message()` в `app/handlers/telegram_handler.py` (асинхронный `httpx.AsyncClient`).

Контракт запроса:

```http
POST {NOTIFICATION_SERVICE_URL}/notifications/telegram/send
api-key: <NOTIFICATION_SERVICE_API_KEY>
Content-Type: application/json

{
  "bot_token": "<BOT_TOKEN>",
  "chat_id": -1001234567890,
  "message_text": "Текст уведомления"
}
```

- Завершающий `/` в `NOTIFICATION_SERVICE_URL` допустим — он отбрасывается при сборке адреса.
- `chat_id` берётся из `CHAT_ID` и отправляется целым числом.
- Сообщения отправляются простым текстом (контракт не поддерживает `parse_mode`), поэтому Markdown-разметка в текстах не используется.

Включение и отключение — переменная `NOTIFICATION_SERVICE_ENABLED`:

- `true` / `1` / `yes` / `on` (без учёта регистра) — уведомления отправляются;
- любое другое значение или отсутствие переменной — уведомления выключены (по умолчанию), запросы не выполняются.

Обработка ошибок (доставка уведомлений — best-effort):

- если уведомления включены, но не заданы `NOTIFICATION_SERVICE_URL`, `NOTIFICATION_SERVICE_API_KEY`, `BOT_TOKEN`, `CHAT_ID` или `CHAT_ID` не является целым числом — пишется предупреждение, запрос не отправляется;
- таймаут запроса — 10 секунд; ответ проверяется через `raise_for_status()`;
- HTTP-ошибки, таймауты и ошибки соединения только логируются и не прерывают обработку заказов, выставление статусов и обработку следующих партнёров;
- повторных попыток, очереди и запасной отправки напрямую в Telegram нет — при сбое уведомление теряется;
- API-ключ, токен бота и заголовки запроса в лог не пишутся.

Пример настроек для продакшена (только заглушки):

```env
NOTIFICATION_SERVICE_ENABLED=true
NOTIFICATION_SERVICE_URL=https://<notification-service-host>
NOTIFICATION_SERVICE_API_KEY=<notification-service-api-key>
BOT_TOKEN=<telegram-bot-token>
CHAT_ID=<telegram-chat-id>
```

Уведомление о деплое из GitHub Actions (job `notify`, см. ниже) к этому не относится: оно выполняется на раннере GitHub, отправляется напрямую в Telegram API и использует собственные секреты репозитория (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_THREAD_ID`).

## Переменные окружения

Задаются в `.env` (читается `config.py` через python-dotenv). Значения не хранятся в репозитории.

| Переменная | Назначение |
|---|---|
| `DATABASE_WEB_URL` | Строка подключения к PostgreSQL для веб-API |
| `DATABASE_SCHEDULER_URL` | Строка подключения к PostgreSQL для планировщика |
| `API_KEY` | Ключ доступа к API |
| `BOT_TOKEN`, `CHAT_ID` | Telegram-бот и чат для уведомлений (`CHAT_ID` — целое число) |
| `NOTIFICATION_SERVICE_ENABLED` | Включение отправки уведомлений (`true`/`false`, по умолчанию `false`) |
| `NOTIFICATION_SERVICE_URL` | Базовый адрес Notification Service |
| `NOTIFICATION_SERVICE_API_KEY` | API-ключ Notification Service (заголовок `api-key`) |
| `URL_SVS_GET`, `URL_SVS_SET` | Эндпоинты SVS для получения заказов и выставления статуса |
| `USER_KEY`, `TOKEN` | Авторизация в SVS при выставлении статуса |
| `URL_ARSEXPRESS`, `URL_AVIS_LOGISTICS`, `URL_TYUMEN`, `URL_EKATERINBURG`, `URL_SIB_EXPRESS`, `URL_PLEX_POST`, `URL_BIZON`, `URL_RASTOYANIYA`, `URL_VIP_MAIL_UFA`, `URL_POST_MASTER` | Адреса страниц отслеживания перевозчиков |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Параметры контейнера PostgreSQL |
| `PORT` | Внешний порт веб-API в docker compose |
| `TAG` | Тег Docker-образов (выставляется при деплое) |

## Локальный запуск

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.backend.txt -r requirements.scheduler.txt
cp example.env .env   # заполнить значения

python run.py           # веб-API на порту 8000
python schedule_run.py  # планировщик (нужны Firefox и geckodriver)
```

Важно: при старте `schedule_run.py` сразу запускает полный прогон и выставляет статусы в SVS, указанный в `.env`.

Для разработки веб-части есть `docker-compose.dev.yaml` (образ `Dockerfile.backend`, target `dev`, автоперезапуск при изменении кода; нужна внешняя сеть `local_network`).

## Docker и деплой

- `Dockerfile.backend` — образ веб-API (Firefox, geckodriver, Xvfb; запуск через Gunicorn с `uvicorn.workers.UvicornWorker`, конфиг `gunicorn.conf.py`).
- `Dockerfile.scheduler` — образ планировщика (Xvfb + `python schedule_run.py`).
- `docker-compose.yaml` — сервисы `db` (PostgreSQL 15, порт 5433), `web`, `scheduler`; внешняя сеть `parser_network`. Образы берутся с тегом `${TAG}`.

## CI/CD (GitHub Actions)

`.github/workflows/deploy.yml` запускается при push в `master`:

1. **build-push** — сборка и публикация образов `svs-parser-scheduler` и `svs-parser-web` в Docker Hub с тегом SHA коммита.
2. **deploy** — по SSH на сервере: `git pull`, `docker pull` образов, запись `TAG` в `.env`, затем `docker compose up web scheduler -d --force-recreate`.
3. **notify** — уведомление о результате деплоя напрямую в Telegram (с раннера GitHub, не через Notification Service).

Все учётные данные берутся из секретов репозитория.
