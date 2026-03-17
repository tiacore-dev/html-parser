from aiogram import Bot
from loguru import logger

from config import Settings


async def send_telegram_message(text, parse_mode=None):
    """
    Отправляет результат анализа в Telegram.
    """
    bot_token = Settings.BOT_TOKEN
    bot = Bot(bot_token)

    try:
        await bot.send_message(chat_id=Settings.CHAT_ID, text=text, parse_mode=parse_mode)
        logger.info("Уведомления успешно отправлены")
    except Exception as e:
        logger.error(
            f"""Ошибка при отправке уведомлений в Telegram: {e}""",
            exc_info=True,
        )
    finally:
        await bot.session.close()


async def send_report_to_telegram(summary: list):
    lines = ["📦 *Отчёт по парсингу заказов*:\n"]

    for item in summary:
        if item.get("error"):
            lines.append(f"❌ *{item['name']}* — ошибка: `{item['error']}`")
            continue

        lines.append(f"🔹 *{item['name']}* ({item['partner_id']})\nВсего: {item['total']} | 📄 Спарсено: {item['parsed']} | ✅ Доставлено: {item['delivered']} | ⏳ Не доставлено: {item['undelivered']} | ❌ Ошибок: {item['failed']}\n")

    text = "\n".join(lines)
    await send_telegram_message(text, parse_mode="Markdown")


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
