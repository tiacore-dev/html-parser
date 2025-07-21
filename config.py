# config.py

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_WEB_URL = os.getenv("DATABASE_WEB_URL", "")
    DATABASE_SCHEDULER_URL = os.getenv("DATABASE_SCHEDULER_URL", "")

    API_KEY = os.getenv("API_KEY", "")

    CHAT_ID = os.getenv("CHAT_ID", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")

    URL_ARSEXPRESS = os.getenv("URL_ARSEXPRESS", "")
    URL_AVIS_LOGISTICS = os.getenv("URL_AVIS_LOGISTICS", "")
    URL_TYUMEN = os.getenv("URL_TYUMEN", "")
    URL_EKATERINBURG = os.getenv("URL_EKATERINBURG", "")
    URL_SIB_EXPRESS = os.getenv("URL_SIB_EXPRESS", "")
    URL_POST_MASTER = os.getenv("URL_POST_MASTER", "")
    URL_PLEX_POST = os.getenv("URL_PLEX_POST", "")
    URL_BIZON = os.getenv("URL_BIZON", "")
    URL_RASTOYANIYA = os.getenv("URL_RASTOYANIYA", "")

    URL_SVS_GET = os.getenv("URL_SVS_GET", "")
    URL_SVS_SET = os.getenv("URL_SVS_SET", "")

    TOKEN = os.getenv("TOKEN", "")
    USER_KEY = os.getenv("USER_KEY", "")
