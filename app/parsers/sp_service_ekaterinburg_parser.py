# parsers/sp_service_ekaterinburg.py
import logging
import os

from dotenv import load_dotenv

from app.parsers.sp_service_base_parser import SPServiceBaseParser

# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger("parser")


class SPServiceEkaterinburgParser(SPServiceBaseParser):
    name = "СП-Сервис Екатеринбург"
    url = os.getenv("URL_EKATERINBURG")
    cookies = {"PHPSESSID": "u9jo4hsn17irl8cg7vvf0qrecd"}
    referer_suffix = "52/tracking"
