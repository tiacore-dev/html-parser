# __init__.py
import logging
from flask_jwt_extended import JWTManager
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import Config
from logger import setup_logger
from app.database import init_db, set_db_globals
from app.parsers import parser_main
from set_password import set_password


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    # Инициализация базы данных
    engine, Session, Base = init_db(app.config['SQLALCHEMY_DATABASE_URI'])
    set_db_globals(engine, Session, Base)
    set_password(login=app.config['LOGIN'], password=app.config['PASSWORD'])

    # Инициализация JWT
    try:
        JWTManager(app)
    except Exception as e:
        logging.error(f"Ошибка при инициализации JWT: {e}")
        raise

    from app.routes import register_routes
    # Регистрация маршрутов
    try:
        register_routes(app)
        # logging.info("Маршруты успешно зарегистрированы.",
        # extra={'user_id': 'init'})
    except Exception as e:
        logging.error(f"Ошибка при регистрации маршрутов: {e}")
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
        trigger=IntervalTrigger(hours=3),
        id='parser_main_job',
        name='Выполнение parser_main каждые 3 часа',
        replace_existing=True,
        max_instances=3,  # Разрешаем до 3 одновременно выполняющихся задач
        misfire_grace_time=3600  # Разрешаем выполнить пропущенные задачи в течение 1 часа
    )

    # Запуск планировщика
    scheduler.start()

    # logging.info("Планировщик задач APScheduler успешно запущен.")
    setup_logger()

    return app
