import asyncio

from loguru import logger

from app.database.init_orm import init_db
from app.scheduler import start_scheduler


async def main():
    logger.info("🚀 Запуск парсера и планировщика задач")
    await init_db()
    await start_scheduler()

    # Просто держим процесс живым
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("❌ Остановка по Ctrl+C")
    except Exception as e:
        logger.exception(f"❗️Произошла ошибка при запуске: {e}")
