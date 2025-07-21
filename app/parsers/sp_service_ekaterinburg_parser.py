# parsers/sp_service_ekaterinburg.py


from app.parsers.sp_service_base_parser import SPServiceBaseParser

# Загрузка переменных окружения
from config import settings


class SPServiceEkaterinburgParser(SPServiceBaseParser):
    name = "СП-Сервис Екатеринбург"
    url = settings.URL_EKATERINBURG
    cookies = {"PHPSESSID": "u9jo4hsn17irl8cg7vvf0qrecd"}
    referer_suffix = "52/tracking"
