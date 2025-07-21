import os

from dotenv import load_dotenv
from loguru import logger
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from app.parsers.base_parser import BaseParser
from app.utils.helpers import create_firefox_driver

# Загрузка переменных окружения
load_dotenv()


class ArsexpressParser(BaseParser):
    url = os.getenv("URL_ARSEXPRESS", "")
    name = "Арсэкспресс"
    DEFAULT_WAIT_TIME = 30

    def get_html(self, orderno):
        """Метод не нужен для PlexPostParser."""
        raise NotImplementedError(f"Метод 'get_html' не реализован в {self.name}.")

    def parse(self, orderno):
        try:
            driver = create_firefox_driver()
        except Exception as e:
            logger.error(f"Ошибка создания драйвера: {e}")
            return None

        try:
            driver.get(f"{self.url}{orderno}")
        except Exception as e:
            logger.error(f"Ошибка при driver.get(): {e}")
            return None

        try:
            logger.info(f"Текущий URL: {driver.current_url}")
            logger.info(f"Заголовок страницы: {driver.title}")

            rows = driver.find_elements(By.CSS_SELECTOR, "tr.wpr-table-body-row")
            parsed_data = []
            for row in rows:
                spans = row.find_elements(By.CSS_SELECTOR, "td span.wpr-table-text")
                texts = [s.text.strip() for s in spans if s.text.strip()]

                entry = {
                    "Дата": texts[0] if len(texts) > 0 else "",
                    "Статус": texts[1] if len(texts) > 1 else "",
                    "Примечание": texts[2] if len(texts) > 2 else "",
                }

                # Сохраняем, только если хотя бы дата или статус есть
                if entry["Дата"] or entry["Статус"]:
                    parsed_data.append(entry)

            logger.info(f"{self.name}. Данные отслеживания: {parsed_data}")

            return parsed_data

        except TimeoutException as e:
            logger.error(f"""{self.name}. Элемент не найден для заказа {orderno}: {e}""")
            return None
        except Exception as e:
            logger.error(f"""{self.name}. Ошибка при обработке заказа {orderno}: {e}""")
            return None

        finally:
            driver.quit()

    def process_delivered_info(self, info):
        for event in info:
            if "доставлено" in event["Статус"].lower():
                return {
                    "date": event["Дата"],
                    "receipient": event["Примечание"],
                    "status": "Доставлено",
                }
        return None
