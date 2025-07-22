import time

from loguru import logger

# Загрузка переменных окружения
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By

from app.parsers.base_parser import BaseParser
from config import Settings


class ArsexpressParser(BaseParser):
    url = Settings.URL_ARSEXPRESS
    name = "Арсэкспресс"
    DEFAULT_WAIT_TIME = 30

    def parse(self, orderno, driver):
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

            for row_index, row in enumerate(rows):
                for attempt in range(3):  # Retry до 3 раз
                    try:
                        spans = row.find_elements(By.CSS_SELECTOR, "td span.wpr-table-text")
                        texts = [s.text.strip() for s in spans if s.text.strip()]

                        entry = {
                            "Дата": texts[0] if len(texts) > 0 else "",
                            "Статус": texts[1] if len(texts) > 1 else "",
                            "Примечание": texts[2] if len(texts) > 2 else "",
                        }

                        if entry["Дата"] or entry["Статус"]:
                            parsed_data.append(entry)

                        break  # успех, выходим из retry-цикла

                    except StaleElementReferenceException:
                        logger.warning(f"{self.name}. Stale элемент в строке {row_index}, попытка {attempt + 1}")
                        time.sleep(1)
                    except Exception as e:
                        logger.error(f"{self.name}. Ошибка в строке {row_index}: {e}")
                        break

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
