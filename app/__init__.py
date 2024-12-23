# __init__.py

from flask_jwt_extended import JWTManager
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import Config
from logger import setup_logger
from app.database import init_db, set_db_globals
from app.parsers import parser_main


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    # Инициализация базы данных
    engine, Session, Base = init_db(app.config['SQLALCHEMY_DATABASE_URI'])
    set_db_globals(engine, Session, Base)
    logger = setup_logger()
    logger.info("База данных успешно инициализирована.")

    # Инициализация JWT
    try:
        JWTManager(app)
        logger.info(f"""JWT инициализирован. Срок действия токенов: {
                    app.config['JWT_ACCESS_TOKEN_EXPIRES']}""")
    except Exception as e:
        logger.error(f"Ошибка при инициализации JWT: {e}")
        raise

    from app.routes import register_routes
    # Регистрация маршрутов
    try:
        register_routes(app)
        logger.info("Маршруты успешно зарегистрированы.",
                    extra={'user_id': 'init'})
    except Exception as e:
        logger.error(f"Ошибка при регистрации маршрутов: {e}")
        raise

    # Инициализация и настройка планировщика
    scheduler = BackgroundScheduler(jobstores=app.config.get('SCHEDULER_JOBSTORES', {}),
                                    executors=app.config.get(
                                        'SCHEDULER_EXECUTORS', {}),
                                    job_defaults=app.config.get(
                                        'SCHEDULER_JOB_DEFAULTS', {}),
                                    timezone="UTC")  # Укажите нужную временную зону

    # Добавление задачи в планировщик
    scheduler.add_job(
        func=parser_main,
        trigger=IntervalTrigger(hours=2),
        id='parser_main_job',
        name='Выполнение parser_main каждые 2 часа',
        replace_existing=True
    )

    # Запуск планировщика
    scheduler.start()
    logger.info("Планировщик задач APScheduler успешно запущен.")

    # Обеспечение корректного завершения планировщика при остановке приложения
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        scheduler.shutdown(wait=False)
        logger.info("Планировщик задач APScheduler успешно остановлен.")

    return app
