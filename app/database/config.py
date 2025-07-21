from config import settings

TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_WEB_URL},
    "apps": {
        "models": {
            # Укажите только модуль
            "models": ["app.database.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
