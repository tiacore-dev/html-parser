# parsers/sp_service_ekaterinburg.py


from app.parsers.sp_service_base_parser import SPServiceBaseParser

# Загрузка переменных окружения
from config import Settings


class SPServiceEkaterinburgParser(SPServiceBaseParser):
    name = "СП-Сервис Екатеринбург"
    url = Settings.URL_EKATERINBURG
