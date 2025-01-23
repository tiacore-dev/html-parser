# parsers/sib_express.py

import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from app.parsers.base_parser import BaseParser
from app.utils.helpers import clean_html

# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger('parser')


def get_csrf_token(session, url):
    response = session.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    token_input = soup.find('input', {'name': '_token'})
    if not token_input or 'value' not in token_input.attrs:
        raise ValueError(f"CSRF-токен не найден по URL: {url}")
    return token_input['value']


class SibExpressParser(BaseParser):
    name = "Сибирский Экспресс"
    url = os.getenv('URL_SIB_EXPRESS')
    # Куки
    cookies = {
        "_ym_uid": "1734680388574908198",
        "_ym_d": "1734680388",
        "_ym_visorc": "w",
        "_ga_YKHVYXWK0P": "GS1.1.1734680388.1.0.1734680388.0.0.0",
        "_ym_isad": "2",
        "_ga": "GA1.2.845727486.1734680388",
        "_gid": "GA1.2.1752836982.1734680388",
        "_gat_gtag_UA_69478068_8": "1",
        "XSRF-TOKEN": "eyJpdiI6IkErVExBZXVMTUtsd21mamdEcjVkemc9PSIsInZhbHVlIjoicXhrS3BJS0hGV2xBR3FkOVRcL09tUm1TNlBqMnVRc0hXSkQxY1wvVDhvT2VDeEN2dGY3Ylwvc1J1eHk4NDFjc0Q2c1VKXC9EY3FOd0RVcDgzSkdOQ3RjVDR3PT0iLCJtYWMiOiI4MjQ1YTFjYWRkZTM3ZjRjMjhhZmZhOTUxYWU2ZDlkNDBiZjU3Njg4YTY0MTY0ZTg1ZDU0NmE1NWVhMDAzOGNkIn0",
        "sibirskiy_ekspress_session": "eyJpdiI6InlSTVgwQyswTDYrTzYwMFM3NndcL29nPT0iLCJ2YWx1ZSI6Ik0xVHVkdCtOT2JtZEVMRldSc0Jmb0dwRFhCcGVOeCt2akVRSm4xandkcit5VzRXNWpnQ2JoVE5ybms2UWp4WmVzdENVOVVveklKWk45NWp1THcxYkVnPT0iLCJtYWMiOiI2YmMzZGVlZWQwZjFhMmEyYTg4YjMwY2Q4NmQ4YzgyM2QwNjkyOGE2NGZjNjRhMzA0ZWVjMzczYmZkZGY1ODRkIn0"
    }

    def get_html(self, orderno):
        if not self.url:
            raise ValueError(
                f"URL для {self.name} не задан. Проверьте переменные окружения.")
        session = requests.Session()

        # Параметры формы
        data = {
            "name": orderno,
            "tab": "1"
        }
        csrf_token = get_csrf_token(session, self.url)
        data["_token"] = csrf_token

        # Кастомные заголовки
        custom_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.sib-express.ru",
            "Referer": self.url,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
        }

        # Получаем итоговые заголовки
        headers = self._get_headers(custom_headers)

        try:
            response = session.post(
                self.url, data=data, headers=headers, cookies=self.cookies, timeout=30)
            response.raise_for_status()
            html = response.text
            # Попытка декодирования JSON
            response_data = json.loads(html)
            if "msg" not in response_data:
                logger.error(
                    f"{self.name}. Поле 'msg' отсутствует в ответе для заказа {orderno}.")
                return None

            # Извлечение HTML из поля 'msg'
            raw_html = response_data["msg"]
            logger.info(
                f"{self.name}. Извлеченный HTML для заказа {orderno}: {raw_html}")
            return raw_html
        except requests.exceptions.RequestException as e:
            logger.error(f"""{self.name}. Request failed for order {
                         orderno}: {e}""")
            return None

    def parse(self, orderno):
        html = self.get_html(orderno)
        if not html:
            return None
        cleaned_html = clean_html(html)
        logger.info(
            f"{self.name}. Полученный HTML для order number {orderno}: {cleaned_html}")
        # Ищем первую таблицу (или по фильтрам, если заданы)
        # Парсинг HTML
        soup = BeautifulSoup(html, 'lxml')

        # Проверка на отсутствие данных
        if "Не найдено" in html:
            logger.error(f"Ответ не содержит данных для заказа {orderno}.")
            return None

            # Извлечение данных из таблицы
        data = {}
        try:
            # Поиск таблицы или строки с информацией
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) == 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        data[key] = value
            else:
                logger.error(
                    f"{self.name}. Таблица с деталями не найдена для заказа {orderno}.")
                return None

            # Логирование и возврат результата
            logger.info(
                f"{self.name}. Полученные данные для заказа {orderno}: {data}")
            return data
        except Exception as e:
            logger.error(f"""{self.name}. Ошибка при обработке заказа {
                orderno}: {e}""")
            return None

    def process_delivered_info(self, info):
        result = None
        for key, value in info.items():
            rec = value.split(' ')
            # Проверяем наличие статуса
            if len(rec) > 0 and rec[0] == 'Доставлено':
                result = {
                    "date": key,
                    # Берем третье слово, если оно есть
                    "receipient": rec[-1],
                    "Status": "Доставлено"
                }
        return result
