# parsers/sp_service_tyumen.py

import os
import logging
from dotenv import load_dotenv
from app.parsers.sp_service_base_parser import SPServiceBaseParser


# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger('parser')

# Конкретный парсер для СП-Сервис Тюмень


class SPServiceTyumenParser(SPServiceBaseParser):
    name = "СП-Сервис Тюмень"
    url = os.getenv('URL_TYUMEN')
    # Куки непосредственно в запросе
    cookies = {
        "PHPSESSID": "pd0apr1en20lsphs6r2f5ghp6r",
        "_csrf": "f1dcfc532e329c03f9464faf503cc8315d80ff1b7306197c20e7bbccf0369106a:2:{i:0;s:5:\"_csrf\";i:1;s:32:\"YWMCORltU4wwvVINjaVnH9qJv2RxieQD\";}"
    }
    referer_suffix = "178/tracking"
