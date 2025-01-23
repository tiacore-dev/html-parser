import logging
import os
import requests
from dotenv import load_dotenv
from app.parsers.base_parser import BaseParser

# Настройка логирования

logger = logging.getLogger('parser')

# Загрузка переменных окружения
load_dotenv()


class PostMasterParser(BaseParser):
    name = "Пост Мастер"
    url = os.getenv('URL_POST_MASTER')

    def get_html(self, orderno):
        custom_headers = {
            "origin": "https://www.post-master.ru",
            "referer": "https://www.post-master.ru/status/",
            "x-requested-with": "XMLHttpRequest"
        }
        headers = self._get_headers(custom_headers)
        data = f"command=track_orders&order_id%5B%5D={orderno}"
        response = requests.post(
            self.url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        return response.json()

    def parse(self, orderno):
        try:
            response = self.get_html(orderno)
            logger.info(f"""{self.name}. Полученные данные для заказа {
                        orderno}: {response}""")
            info = []
            # Обработка данных из JSON
            if isinstance(response, list):
                for entry in response:
                    order_entry = {
                        "Накладная": entry.get("VDOCNUMBER"),
                        "Город отправки": entry.get("VSENDERCITY"),
                        "Город доставки": entry.get("VDELIVERYCITY"),
                        "Дата": entry.get("VDATE"),
                        "Статус": entry.get("VPOINT"),
                    }
                    info.append(order_entry)
                logger.info(f"{self.name}. Распарсенные данные: {info}")
                return info
            else:
                logger.error(f"""{self.name}. Неожиданный формат ответа для заказа {
                    orderno}: {response}""")
                return None
        except Exception as e:
            logger.error(f"""{self.name}. Ошибка при обработке заказа {
                orderno}: {e}""")
            return None

    def process_delivered_info(self, info):
        result = None
        for event in info:
            if "доставлено" in event["Статус"].lower():
                result = {
                    "date": event["Дата"],
                    "receipient": event.get("Статус").split()[-1],
                    "status": "Доставлено"  # Переименовываем статус
                }
        return result
