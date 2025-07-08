# parsers/sib_express.py

import logging
import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from app.parsers.base_parser import BaseParser
from app.utils.helpers import clean_html

# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger("parser")


class AvisLogisticsParser(BaseParser):
    name = "Авис-Логистик"
    url = os.getenv("URL_AVIS_LOGISTICS")
    # Куки
    cookies = {
        "PHPSESSID": "uur2h0fp5ks9hub2dnn462j5kq",
        "_ga": "GA1.1.1532879673.1739871303",
        "_ym_uid": "1739871303729443487",
        "_ym_d": "1739871303",
        "_ym_isad": "1",
        "_ym_visorc": "w",
        "_ga_R2Z36FPB41": "GS1.1.1739874415.2.1.1739874662.0.0.0",
    }

    def get_html(self, orderno):
        if not self.url:
            raise ValueError(f"URL для {self.name} не задан. Проверьте переменные окружения.")
        session = requests.Session()

        # Параметры формы
        data = f"trackNumberButton={orderno}"

        # Кастомные заголовки
        headers = {
            "Accept": "text/html, */*; q=0.01",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://avislogistics.ru",
            "Referer": f"https://avislogistics.ru/?trace={orderno}",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }

        try:
            response = session.post(self.url, data=data, headers=headers, cookies=self.cookies, timeout=30)
            response.raise_for_status()
            html = response.text

            if not html:
                logger.error(f"{self.name}. Не получили html для заказа {orderno}.")
                return None

            logger.info(f"{self.name}. Извлеченный HTML для заказа {orderno}: {html}")
            return html
        except requests.exceptions.RequestException as e:
            logger.error(f"""{self.name}. Request failed for order {orderno}: {e}""")
            return None

    def parse(self, orderno):
        html = self.get_html(orderno)
        if not html:
            return None
        cleaned_html = clean_html(html)
        # logger.info(
        # f"{self.name}. Полученный HTML для order number {orderno}: {cleaned_html}")

        soup = BeautifulSoup(cleaned_html, "lxml")

        # Проверка на отсутствие данных
        if "Не найдено" in html:
            logger.error(f"Ответ не содержит данных для заказа {orderno}.")
            return None

        data = []

        try:
            # Ищем блоки с событиями (доставка, транзит и т. д.)
            events_container = soup.find_all("div", class_="window__trace_content")

            if not events_container:
                logger.error(f"{self.name}. Данные о заказе {orderno} не найдены.")
                return None

            # Обрабатываем первую найденную таблицу со статусами заказа
            status_rows = events_container[-1].find_all("div", class_="window__trace_row")

            for row in status_rows:
                cells = row.find_all("div", class_="trace__row_title text")
                if len(cells) == 3:
                    event = {
                        "date": cells[0].get_text(strip=True),
                        "status": cells[1].get_text(strip=True),
                        "city": cells[2].get_text(strip=True),
                    }
                    data.append(event)

            # Теперь ищем блок с получателем/администратором
            receiver_block = events_container[-2]  # Берём второй с конца
            receiver_rows = receiver_block.find_all("div", class_="window__trace_row")

            if receiver_rows:
                last_receiver = receiver_rows[-1].find_all("div", class_="trace__row_title text")
                if len(last_receiver) == 3:
                    receiver_info = {
                        "date": last_receiver[0].get_text(strip=True),
                        "receiver_name": last_receiver[1].get_text(strip=True),
                        "receiver_role": last_receiver[2].get_text(strip=True),
                        "status": "receiver",
                    }
                    data.append(receiver_info)

            logger.info(f"{self.name}. Полученные данные для заказа {orderno}: {data}")
            return data

        except Exception as e:
            logger.error(f"{self.name}. Ошибка при обработке заказа {orderno}: {e}")
            return None

    def process_delivered_info(self, info):
        result = None
        for event in info:
            # Проверяем наличие статуса
            if len(event) > 0 and event["status"] == "Доставлено":
                receiver_info = info[-1]
                if receiver_info["receiver_name"]:
                    result = {"date": event["date"], "receipient": receiver_info["receiver_name"], "Status": "Доставлено"}
        return result
