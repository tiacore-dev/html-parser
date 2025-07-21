from aiogram import Bot
from loguru import logger

from config import Settings


async def send_telegram_message(text, parse_mode):
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

        lines.append(f"🔹 *{item['name']}* ({item['partner_id']})\nВсего: {item['total']} | ✅ Успешно: {item['success']} | ❌ Ошибок: {item['failed']}\n")

    text = "\n".join(lines)

    await send_telegram_message(text, parse_mode="Markdown")
