import os

import requests
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from loguru import logger

from app.parsers.base_parser import BaseParser

# Загрузка переменных окружения
load_dotenv()


class BizonExpressParser(BaseParser):
    url = os.getenv("URL_BIZON", "")
    name = "Бизон Экспресс"
    cookies = {
        "PHPSESSID": "guj6203cf7mpovg0rc539oorcb",
        "_ym_uid": "1741339459805860605",
        "_ym_d": "1741339459",
        "_ym_isad": "1",
        "_ym_visorc": "w",
    }
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "priority": "u=0, i",
        "referer": "https://new.courierexe.ru/287/tracking",
        "sec-fetch-dest": "iframe",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }

    def get_html(self, orderno):
        params = {"orderno": orderno, "submit": "1", "singlebutton": "submit"}
        try:
            response = requests.get(
                self.url,
                headers=self.headers,
                cookies=self.cookies,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса для заказа {orderno}: {e}")
            return None

    def parse(self, orderno):
        html = self.get_html(orderno)

        if not html:
            return None

        try:
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", class_="table")
            if not table:
                logger.error(f"Таблица с деталями не найдена для заказа {orderno}.")
                return None

            data = {"invoice": orderno}
            if not isinstance(table, Tag):
                logger.error("Неверный тип: таблица не найдена или не является HTML-тегом")
                return None
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    data[key] = value
            logger.info(f"""{self.name}. Полученные данные для заказа {orderno}: {data}""")
            return data
        except Exception as e:
            logger.error(f"Ошибка обработки HTML для заказа {orderno}: {e}")
            return None

    def process_delivered_info(self, info):
        result = None

        if info["Статус"] == "Доставлен":
            result = {
                "date": f"{info['Дата вручения']} {info['Время вручения']}",
                "receipient": info["Инфо о доставке"],
                "Status": info["Статус"],
            }
        return result
