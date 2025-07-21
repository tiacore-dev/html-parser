from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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
            wait = WebDriverWait(driver, 15)

            input_field = wait.until(EC.presence_of_element_located((By.NAME, "name")))
            input_field.clear()
            input_field.send_keys(orderno)

            # Удаляем клик по скрытому input[name='tab']

            # Отправка формы
            submit_button = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
            submit_button.click()

            # Ждём таблицу или сообщение об отсутствии
            wait.until(lambda d: "не найдено" in d.page_source.lower() or d.find_elements(By.TAG_NAME, "table"))

            if "не найдено" in driver.page_source.lower():
                logger.warning(f"{self.name}. Заказ {orderno} не найден.")
                return None

            tables = driver.find_elements(By.TAG_NAME, "table")
            if not tables:
                logger.warning(f"{self.name}. Таблица не найдена для заказа {orderno}.")
                return None

            table = tables[0]
            rows = table.find_elements(By.TAG_NAME, "tr")

            data = {}
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) == 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    data[key] = value

            if not data:
                logger.warning(f"{self.name}. Таблица пуста для заказа {orderno}")
                return None

            logger.info(f"{self.name}. Полученные данные для заказа {orderno}: {data}")
            return data

        except TimeoutException:
            logger.error(f"{self.name}. Timeout при ожидании элементов для заказа {orderno}")
            return None
        except NoSuchElementException as e:
            logger.error(f"{self.name}. Элемент не найден при заказе {orderno}: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при заказе {orderno}: {e}")
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
