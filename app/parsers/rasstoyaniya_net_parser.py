# parsers/rasstoyaniya_net.py

import os

import requests
from bs4 import BeautifulSoup, Tag
from loguru import logger

from app.parsers.base_parser import BaseParser
from app.utils.helpers import clean_html

# Загрузка переменных окружения


class RasstoyaniyaNetParser(BaseParser):
    name = "Расстояния нет"
    url = os.getenv("URL_RASTOYANIYA")
    # Куки
    cookies = {
        "geobase": "a:0:{}",
        "PHPSESSID": "r4emb86q6607kifd0qe53titc3",
        "_ym_uid": "1734680291770530560",
        "_ym_d": "1734680291",
        "_ym_isad": "2",
        "lhc_per": '{"vid":"3dy2q6mmldpts6crn3k"}',
    }

    def get_html(self, orderno):
        if not self.url:
            raise ValueError(f"URL для {self.name} не задан. Проверьте переменные окружения.")

        # Параметры формы
        data = {"FindForm[bill]": orderno}
        custom_headers = {
            "origin": "https://www.rasstoyanie.net",
            "priority": "u=1, i",
            "referer": self.url,
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-requested-with": "XMLHttpRequest",
        }
        headers = self._get_headers(custom_headers)

        session = requests.Session()

        try:
            response = session.post(self.url, data=data, headers=headers, cookies=self.cookies, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"""{self.name}. Request failed for order {orderno}: {e}""")
            return None

    def parse(self, orderno):
        html = self.get_html(orderno)
        if not html:
            return None
        cleaned_html = clean_html(html)

        try:
            soup = BeautifulSoup(cleaned_html, "lxml")

            # Извлечение заголовка накладной
            header = soup.find("h5", class_="find-header")
            if header:
                invoice = header.get_text(strip=True)
            else:
                logger.error(f"{self.name}.Не удалось найти заголовок накладной для заказа {orderno}.")
                return None

            # Извлечение данных из таблицы
            table = soup.find("table", class_="detail-view", id="quick_find")
            if not table:
                logger.error(f"{self.name}.Таблица с деталями не найдена для заказа {orderno}.")
                return None

            data = {"invoice": invoice}
            if not isinstance(table, Tag):
                logger.error("Неверный тип: таблица не найдена или не является HTML-тегом")
                return None
            rows = table.find_all("tr")
            for row in rows:
                header_cell = row.find("th")
                data_cell = row.find("td")
                if header_cell and data_cell:
                    key = header_cell.get_text(strip=True).rstrip(":")
                    value = data_cell.get_text(strip=True)
                    data[key] = value

            logger.info(f"""{self.name}. Полученные данные для заказа {orderno}: {data}""")
            return data
        except Exception as e:
            logger.error(f"""{self.name}. Ошибка при обработке заказа {orderno}: {e}""")
            return None

    def process_delivered_info(self, info):
        result = None
        if (info["Статус"] == "Доставлена" or info["Статус"] == "Доставлено") and info["Получатель"] != "Сдано в ТК":
            result = {
                "date": f"{info['Дата доставки']}",
                "receipient": f"{info['Получатель']}",
                "status": f"{info['Статус']}",
            }
        return result
