import os

from dotenv import load_dotenv

from app import create_app

load_dotenv()

# Получаем порт из переменных окружения
port = os.getenv("FLASK_PORT", "5000")

# Создаем приложение
app = create_app()


# Запуск через Gunicorn будет автоматически управлять процессом запуска
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(port))
