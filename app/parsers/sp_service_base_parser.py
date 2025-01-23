# parsers/sp_service_ekaterinburg.py
import json
import logging
import requests
from app.parsers.base_parser import BaseParser
from app.utils.helpers import clean_html


logger = logging.getLogger('parser')


class SPServiceBaseParser(BaseParser):
    def get_html(self, orderno):
        if not self.url:
            raise ValueError(
                f"URL для {self.name} не задан. Проверьте переменные окружения.")

        # Параметры запроса
        params = {
            "orderno": orderno,
            "singlebutton": "submit"
        }
        # Заголовки запроса
        custom_headers = {
            "priority": "u=0, i",
            "referer": f"{self.url}/{self.referer_suffix}?orderno={orderno}&singlebutton=submit",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
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
            response = session.get(
                self.url, params=params, headers=headers, cookies=self.cookies, timeout=30)
            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"""{self.name}. Request failed for order {
                         orderno}: {e}""")
            return None

    def parse(self, orderno):
        html = self.get_html(orderno)
        if not html:
            return {"error": "Failed to retrieve HTML"}
        cleaned_html = clean_html(html)
        logger.info(
            f"{self.name}. Полученный HTML для order number {orderno}: {cleaned_html}")
        table = self._get_table(cleaned_html, 'table-striped')
        if not table:
            logger.error(
                f"{self.name}. Таблица с деталями не найдена для заказа {orderno}.")
            return json.dumps({"error": "Detail table not found"}, ensure_ascii=False)

        data = self.extract_table_data(table, key_tag='td', min_cells=2)
        return data

    def process_delivered_info(self, info):
        if info.get('Date parcel received'):
            return {
                "date": f"{info['Date parcel received']} {info['Time parcel received']}",
                "receipient": info['Delivery info'],
                "Status": info['Status'],
            }
        return None
