from loguru import logger
from tortoise import Tortoise

from config import settings


async def init_db():
    logger.info("🔌 Инициализация Tortoise ORM без FastAPI")
    await Tortoise.init(db_url=settings.DATABASE_SCHEDULER_URL, modules={"models": ["app.database.models"]})

    logger.info("✅ База данных готова")
