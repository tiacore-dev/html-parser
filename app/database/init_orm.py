import os

from dotenv import load_dotenv
from loguru import logger
from tortoise import Tortoise

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def init_db():
    logger.info("🔌 Инициализация Tortoise ORM без FastAPI")
    await Tortoise.init(db_url=DATABASE_URL, modules={"models": ["app.database.models"]})

    logger.info("✅ База данных готова")
