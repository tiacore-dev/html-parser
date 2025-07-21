from loguru import logger
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from app.parsers.base_parser import BaseParser
from app.utils.helpers import create_firefox_driver
from config import Settings


class SibExpressParser(BaseParser):
    name = "Сибирский Экспресс"
    url = Settings.URL_SIB_EXPRESS

    def parse(self, orderno):
        try:
            driver = create_firefox_driver()
        except Exception as e:
            logger.error(f"{self.name}. Ошибка создания драйвера: {e}")
            return None

        try:
            driver.get(self.url)

            # Найдём поле ввода и введём номер заказа
            input_field = driver.find_element(By.NAME, "name")
            input_field.clear()
            input_field.send_keys(orderno)

            # Переключаемся на нужную вкладку, если нужно
            tab_radio = driver.find_element(By.CSS_SELECTOR, "input[name='tab'][value='1']")
            tab_radio.click()

            # Нажимаем кнопку "Показать"
            submit_button = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
            submit_button.click()

            # Ожидаем появление таблицы
            driver.implicitly_wait(5)

            # Проверяем на "Не найдено"
            if "Не найдено" in driver.page_source:
                logger.error(f"{self.name}. Заказ {orderno} не найден.")
                return None

            # Извлекаем таблицу
            table = driver.find_element(By.TAG_NAME, "table")
            rows = table.find_elements(By.TAG_NAME, "tr")

            data = {}
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) == 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    data[key] = value

            logger.info(f"{self.name}. Полученные данные для заказа {orderno}: {data}")
            return data

        except TimeoutException as e:
            logger.error(f"{self.name}. Timeout при заказе {orderno}: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при обработке заказа {orderno}: {e}")
            return None
        finally:
            driver.quit()

    def process_delivered_info(self, info):
        result = None
        for key, value in info.items():
            rec = value.split(" ")
            if rec and rec[0] == "Доставлено":
                result = {
                    "date": key,
                    "receipient": rec[2] if len(rec) > 2 else rec[1] if len(rec) > 1 else "",
                    "status": "Доставлено",
                }
        return result
