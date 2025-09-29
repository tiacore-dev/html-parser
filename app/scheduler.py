from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.parsers.parse_main import parser_main

# Инициализация планировщика с использованием SQLAlchemy для хранения задач
scheduler = AsyncIOScheduler(timezone="Asia/Novosibirsk")


async def start_scheduler():
    # ⏱ Запускаем задачу по расписанию
    scheduler.add_job(
        parser_main,
        trigger="cron",
        hour="*/3",
        minute=0,
        id="parse_job",
        replace_existing=True,
    )
    scheduler.start()

    logger.info("🕒 Планировщик запущен")
    logger.info(f"Запланированные задачи: {scheduler.get_jobs()}")

    # 🚀 Сразу выполняем задачу один раз при старте
    logger.info("🚀 Моментальный запуск парсера при старте")
    await parser_main()
