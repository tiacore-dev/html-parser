from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.parsers.base_parser import BaseParser
from app.utils.helpers import retry_on_stale
from config import Settings


class SibExpressParser(BaseParser):
    name = "Сибирский Экспресс"
    url = Settings.URL_SIB_EXPRESS

    @retry_on_stale(retries=5, delay=1)
    def _parse_row(self, row):
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) == 2:
            key = cells[0].text.strip()
            value = cells[1].text.strip()
            return key, value
        elif len(cells) == 1:
            text = cells[0].text.strip()
            # Попробуем сплитнуть по первой цифре
            if " " in text:
                split_idx = text.find(" ")
                return text[:split_idx], text[split_idx + 1 :].strip()
            return None, text
        return None, None

    def parse(self, orderno, driver):
        try:
            driver.get(self.url)
            wait = WebDriverWait(driver, 15)

            # Ввод накладной
            input_field = wait.until(EC.presence_of_element_located((By.NAME, "name")))
            input_field.clear()
            input_field.send_keys(orderno)

            # Сабмит формы
            form = driver.find_element(By.CSS_SELECTOR, "form.order-form")
            form.submit()
            logger.info(f"{self.name}. Форма отправлена через submit()")

            # Ждём появление блока с результатом
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "msg")))

            msg_block = driver.find_element(By.CLASS_NAME, "msg")
            table = msg_block.find_element(By.TAG_NAME, "table")
            rows = table.find_elements(By.TAG_NAME, "tr")
            data = {}

            for i, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) == 2:
                        key = cells[0].text.strip()
                        value = cells[1].text.strip()
                        if key:
                            data[key] = value
                except Exception as e:
                    logger.warning(f"{self.name}. Ошибка при разборе строки {i}: {e}")

            if not data:
                logger.warning(f"{self.name}. Таблица пуста для заказа {orderno}")
                # dump_debug(driver, f"sib_express_{orderno}_empty")
                return None

            logger.info(f"{self.name}. Полученные данные для заказа {orderno}: {data}")
            return data

        except TimeoutException:
            logger.error(f"{self.name}. Timeout при ожидании элементов для заказа {orderno}")
            # dump_debug(driver, f"sib_express_{orderno}_timeout")
            return None
        except NoSuchElementException as e:
            logger.error(f"{self.name}. Элемент не найден при заказе {orderno}: {e}")
            # dump_debug(driver, f"sib_express_{orderno}_no_element")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при заказе {orderno}: {e}")
            # dump_debug(driver, f"sib_express_{orderno}_exception")
            return None

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
