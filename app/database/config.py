from config import Settings

TORTOISE_ORM = {
    "connections": {"default": Settings.DATABASE_WEB_URL},
    "apps": {
        "models": {
            # Укажите только модуль
            "models": ["app.database.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
