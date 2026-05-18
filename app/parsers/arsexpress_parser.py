from loguru import logger

# Загрузка переменных окружения
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
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
    def _parse_row(self, driver, row_index):
        rows = driver.find_elements(By.CSS_SELECTOR, "tr.wpr-table-body-row")
        if row_index >= len(rows):
            raise StaleElementReferenceException(f"Строка {row_index} больше недоступна после перерисовки таблицы")

        spans = rows[row_index].find_elements(By.CSS_SELECTOR, "td span.wpr-table-text")
        texts = [s.text.strip() for s in spans if s.text.strip()]
        return {
            "Дата": texts[0] if len(texts) > 0 else "",
            "Статус": texts[1] if len(texts) > 1 else "",
            "Примечание": texts[2] if len(texts) > 2 else "",
        }

    def _tracking_result_visible(self, driver):
        if driver.find_elements(By.CSS_SELECTOR, "tr.wpr-table-body-row"):
            return True

        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        return all(marker in page_text for marker in ("история отправления", "дата", "статус", "примечание"))

    def parse(self, orderno, driver):
        try:
            driver.get(f"{self.url}{orderno}")
        except Exception as e:
            logger.error(f"Ошибка при driver.get(): {e}")
            return None

        try:
            logger.info(f"Текущий URL: {driver.current_url}")
            logger.info(f"Заголовок страницы: {driver.title}")

            # В кейсе "нет данных" строк нет вообще, поэтому ждём не row,
            # а само состояние результата: заголовок/шапку таблицы или строки истории.
            WebDriverWait(driver, 20).until(self._tracking_result_visible)

            rows = driver.find_elements(By.CSS_SELECTOR, "tr.wpr-table-body-row")
            if not rows:
                logger.info(f"{self.name}. По заказу {orderno} история отслеживания отсутствует.")
                logger.info(f"{self.name}. Данные отслеживания: []")
                return []

            parsed_data = []

            for row_index in range(len(rows)):
                try:
                    entry = self._parse_row(driver, row_index)
                    if entry["Дата"] or entry["Статус"]:
                        parsed_data.append(entry)
                except Exception as e:
                    logger.warning(f"{self.name}. Не удалось обработать строку {row_index}: {e}")

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
