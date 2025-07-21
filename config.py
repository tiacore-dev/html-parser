from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_WEB_URL: str
    DATABASE_SCHEDULER_URL: str

    API_KEY: str

    CHAT_ID: str
    BOT_TOKEN: str

    # URLs

    URL_ARSEXPRESS: str
    URL_AVIS_LOGISTICS: str
    URL_TYUMEN: str
    URL_EKATERINBURG: str
    URL_SIB_EXPRESS: str
    URL_POST_MASTER: str
    URL_PLEX_POST: str

    URL_SVS_GET: str
    URL_SVS_SET: str

    # For SVS
    TOKEN: str
    USER_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()  # type: ignore
