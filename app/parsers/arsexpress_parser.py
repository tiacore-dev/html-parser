from loguru import logger

# Загрузка переменных окружения
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.parsers.base_parser import BaseParser
from app.utils.helpers import retry_on_stale
from config import Settings


class ArsexpressParser(BaseParser):
    url = Settings.URL_ARSEXPRESS
    name = "Арсэкспресс"
    DEFAULT_WAIT_TIME = 30

    @retry_on_stale(retries=5, delay=1)
    def _parse_row(self, row):
        spans = row.find_elements(By.CSS_SELECTOR, "td span.wpr-table-text")
        texts = [s.text.strip() for s in spans if s.text.strip()]
        return {
            "Дата": texts[0] if len(texts) > 0 else "",
            "Статус": texts[1] if len(texts) > 1 else "",
            "Примечание": texts[2] if len(texts) > 2 else "",
        }

    def parse(self, orderno, driver):
        try:
            driver.get(f"{self.url}{orderno}")
        except Exception as e:
            logger.error(f"Ошибка при driver.get(): {e}")
            return None

        try:
            logger.info(f"Текущий URL: {driver.current_url}")
            logger.info(f"Заголовок страницы: {driver.title}")

            # Ожидание появления таблицы
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr.wpr-table-body-row")))

            rows = driver.find_elements(By.CSS_SELECTOR, "tr.wpr-table-body-row")
            parsed_data = []

            for row_index, row in enumerate(rows):
                try:
                    entry = self._parse_row(row)
                    if entry["Дата"] or entry["Статус"]:
                        parsed_data.append(entry)
                except Exception as e:
                    logger.error(f"{self.name}. Ошибка при обработке строки {row_index}: {e}")

            logger.info(f"{self.name}. Данные отслеживания: {parsed_data}")
            return parsed_data

        except TimeoutException as e:
            logger.error(f"{self.name}. Таймаут для заказа {orderno}: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при обработке заказа {orderno}: {e}")
            return None

    def process_delivered_info(self, info):
        for event in info:
            if "доставлено" in event["Статус"].lower():
                return {
                    "date": event["Дата"],
                    "receipient": event["Примечание"],
                    "status": "Доставлено",
                }
        return None
