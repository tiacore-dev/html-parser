import os

from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.parsers.base_parser import BaseParser
from app.utils.helpers import retry_on_stale, safe_click


class VIPMailUfaParser(BaseParser):
    url = os.getenv("URL_VIP_MAIL_UFA", "")
    name = "ВипМайл Уфа"
    DEFAULT_WAIT_TIME = 30

    @retry_on_stale(retries=5, delay=1)
    def _parse_table(self, table):
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Пропускаем заголовок
        results = []
        for row_index, row in enumerate(rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            results.append(
                {
                    "Дата": cells[0].text,
                    "Состояние": cells[1].text,
                    "Примечания": cells[2].text if len(cells) > 2 else "",
                }
            )
        return results

    def parse(self, orderno, driver):
        try:
            driver.get(self.url)
        except Exception as e:
            logger.error(f"Ошибка при driver.get(): {e}")
            return None

        try:
            # Вводим номер накладной
            number_field = WebDriverWait(driver, self.DEFAULT_WAIT_TIME).until(EC.presence_of_element_located((By.NAME, "number")))
            number_field.clear()
            number_field.send_keys(orderno)

            # Кликаем по кнопке "Отправить"
            safe_click(driver, "//input[@name='submit']", "кнопка Отправить")

            # Проверка наличия заголовка
            try:
                track_title = driver.find_element(By.CSS_SELECTOR, "h3")
                if "Трек отправления" not in track_title.text:
                    logger.warning(f"{self.name}. Трек не найден для заказа {orderno}")
                    return []
            except NoSuchElementException:
                logger.warning(f"{self.name}. Трек не найден для заказа {orderno}")
                return []

            # Ждем появления таблицы
            table = WebDriverWait(driver, self.DEFAULT_WAIT_TIME).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            logger.info(f"{self.name}. Таблица найдена")

            results = self._parse_table(table)
            logger.info(f"{self.name}. Данные отслеживания: {results}")
            return results

        except TimeoutException as e:
            logger.error(f"{self.name}. Таймаут при обработке заказа {orderno}: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при обработке заказа {orderno}: {e}")
            return None

    def process_delivered_info(self, info):
        for event in info:
            if "доставлено" in event["Состояние"].lower():
                return {
                    "date": event["Дата"],
                    # Получатель из "Примечания"
                    "receipient": event.get("Примечания", "Не указано"),
                    "status": "Доставлено",  # Переименовываем статус
                }
        return None
