# parsers/sp_service_ekaterinburg.py


import requests
from bs4 import BeautifulSoup, Tag
from loguru import logger

from app.parsers.base_parser import BaseParser
from app.utils.helpers import clean_html


class SPServiceBaseParser(BaseParser):
    def get_html(self, orderno):
        if not self.url:
            raise ValueError(f"URL для {self.name} не задан. Проверьте переменные окружения.")

        # Параметры запроса
        params = {"orderno": orderno, "singlebutton": "submit"}
        # Заголовки запроса
        custom_headers = {
            "priority": "u=0, i",
            "referer": f"{self.url}/{self.referer_suffix}?orderno={orderno}&singlebutton=submit",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "iframe",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        }

        # Получаем итоговые заголовки
        headers = self._get_headers(custom_headers)

        session = requests.Session()
        try:
            response = session.get(self.url, params=params, headers=headers, cookies=self.cookies, timeout=30)
            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"""{self.name}. Request failed for order {orderno}: {e}""")
            return None

    def parse(self, orderno):
        html = self.get_html(orderno)
        if not html:
            return None
        try:
            cleaned_html = clean_html(html)

            soup = BeautifulSoup(cleaned_html, "lxml")
            all_tables = soup.find_all("table")
            logger.debug(f"""Найденные таблицы: {[str(table)[:200] for table in all_tables]}""")

            # Попробуем найти таблицу с данными
            table = soup.find("table", class_=lambda x: isinstance(x, str) and "table-striped" in x)

            if not table:
                logger.error(f"{self.name}. Таблица с деталями не найдена для заказа {orderno}.")
                return None

            data = {}
            if not isinstance(table, Tag):
                logger.error("Неверный тип: таблица не найдена или не является HTML-тегом")
                return None
            rows = table.find_all("tr")
            for row in rows:
                # Используем <td> для первой ячейки
                header_cell = row.find("td")
                data_cell = row.find_all("td")[1] if len(row.find_all("td")) > 1 else None
                if header_cell and data_cell:
                    key = header_cell.get_text(strip=True).rstrip(":")
                    value = data_cell.get_text(strip=True)
                    data[key] = value

            logger.info(f"{self.name}. Полученные данные для order number {orderno}: {data}")
            return data

        except Exception as e:
            logger.error(f"""{self.name}. Ошибка при обработке заказа {orderno}: {e}""")
            return None

    def process_delivered_info(self, info):
        if info.get("Date parcel received"):
            return {
                "date": f"{info['Date parcel received']} {info['Time parcel received']}",
                "receipient": info["Delivery info"],
                "Status": info["Status"],
            }
        return None
