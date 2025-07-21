# parsers/sp_service_tyumen.py


from app.parsers.sp_service_base_parser import SPServiceBaseParser

# Загрузка переменных окружения
from config import Settings


class SPServiceTyumenParser(SPServiceBaseParser):
    name = "СП-Сервис Тюмень"
    url = Settings.URL_TYUMEN
