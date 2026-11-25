import httpx
from loguru import logger

from config import Settings

NOTIFICATION_PATH = "/notifications/telegram/send"
NOTIFICATION_TIMEOUT = 10.0


async def send_telegram_message(text):
    """
    Отправляет сообщение в Telegram через Notification Service.
    Best-effort: ошибки только логируются и не пробрасываются.
    """
    if not Settings.NOTIFICATION_SERVICE_ENABLED:
        logger.info("Notification Service отключён, уведомление не отправлено")
        return

    if not all(
        (Settings.NOTIFICATION_SERVICE_URL, Settings.NOTIFICATION_SERVICE_API_KEY, Settings.BOT_TOKEN, Settings.CHAT_ID)
    ):
        logger.warning(
            "Notification Service: не заданы NOTIFICATION_SERVICE_URL, NOTIFICATION_SERVICE_API_KEY, "
            "BOT_TOKEN или CHAT_ID, уведомление не отправлено"
        )
        return

    try:
        chat_id = int(Settings.CHAT_ID)
    except ValueError:
        logger.warning("Notification Service: CHAT_ID должен быть целым числом, уведомление не отправлено")
        return

    url = Settings.NOTIFICATION_SERVICE_URL.rstrip("/") + NOTIFICATION_PATH
    payload = {"bot_token": Settings.BOT_TOKEN, "chat_id": chat_id, "message_text": text}

    try:
        async with httpx.AsyncClient(timeout=NOTIFICATION_TIMEOUT) as client:
            response = await client.post(url, headers={"api-key": Settings.NOTIFICATION_SERVICE_API_KEY}, json=payload)
            response.raise_for_status()
        logger.info(f"Уведомление отправлено через Notification Service (HTTP {response.status_code})")
    except httpx.HTTPStatusError as e:
        logger.error(f"Notification Service вернул ошибку HTTP {e.response.status_code}")
    except Exception as e:  # best-effort: никакая ошибка доставки не должна ломать парсинг
        logger.error(f"Ошибка отправки уведомления через Notification Service: {type(e).__name__}: {e}")


async def send_report_to_telegram(summary: list):
    lines = ["📦 Отчёт по парсингу заказов:\n"]

    for item in summary:
        if item.get("error"):
            lines.append(f"❌ {item['name']} ({item['partner_id']}) — ошибка: {item['error']}")
            continue

        lines.append(f"🔹 {item['name']} ({item['partner_id']})\nВсего: {item['total']} | 📄 Спарсено: {item['parsed']} | ✅ Доставлено: {item['delivered']} | ⏳ Не доставлено: {item['undelivered']} | ❌ Ошибок: {item['failed']}\n")

    text = "\n".join(lines)
    await send_telegram_message(text)


async def send_set_status_error_to_telegram(
    partner_id: str,
    parser_name: str,
    order_number: str,
    order_id: str,
    response_text: str,
):
    text = (
        "Ошибка при выставлении статуса в SVS\n"
        f"Клиент: {parser_name} ({partner_id})\n"
        f"Номер заказа: {order_number}\n"
        f"ID заказа: {order_id}\n"
        f"Ответ: {response_text}"
    )
    await send_telegram_message(text)
