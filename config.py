import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    API_KEY = os.getenv("API_KEY")
    LOGIN = os.getenv("LOGIN")
    PASSWORD = os.getenv("PASSWORD")
    # Настройки APScheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_JOBSTORES = {"default": {"type": "memory"}}
    SCHEDULER_EXECUTORS = {"default": {"type": "threadpool", "max_workers": 10}}
    SCHEDULER_JOB_DEFAULTS = {"coalesce": False, "max_instances": 1}
