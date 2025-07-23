from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.parsers.base_parser import BaseParser
from app.utils.helpers import dump_debug, retry_on_stale


class SPServiceBaseParser(BaseParser):
    @retry_on_stale(retries=5, delay=1)
    def _parse_row(self, row):
        cols = row.find_elements(By.CSS_SELECTOR, "div.col-8.font-14.pt-0.pb-2, div.col-4.font-14.pt-0.pb-2")
        if len(cols) == 2:
            key = cols[0].text.strip().rstrip(":")
            value = cols[1].text.strip()
            return key, value
        return None, None

    def parse(self, orderno, driver):
        try:
            full_url = f"{self.url}?orderno={orderno}&singlebutton=submit"
            driver.get(full_url)
            logger.info(f"{self.name}. Текущий URL: {driver.current_url}")
            logger.info(f"Заголовок страницы: {driver.title}")

            wait = WebDriverWait(driver, 15)

            # Проверка на "Ничего не найдено"
            try:
                warning_block = driver.find_element(By.CSS_SELECTOR, "div.alert.alert-info.text-center")
                if "Ничего не найдено" in warning_block.text:
                    logger.warning(f"{self.name}. По заказу {orderno} ничего не найдено.")
                    return {}
            except NoSuchElementException:
                pass

            # Ждем появления основной таблицы
            main_table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.main-table")))

            rows = main_table.find_elements(By.CSS_SELECTOR, "div.row")
            data = {}

            for idx, row in enumerate(rows):
                try:
                    key, value = self._parse_row(row)
                    if key:
                        data[key] = value
                except Exception as e:
                    logger.warning(f"{self.name}. Ошибка при обработке строки {idx}: {e}")

            if not data:
                logger.warning(f"{self.name}. Нет данных по заказу {orderno}")
                return None

            logger.info(f"{self.name}. Полученные данные для заказа {orderno}: {data}")
            return data

        except TimeoutException:
            logger.error(f"{self.name}. Таймаут при заказе {orderno}: элемент main-table не найден.")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при парсинге заказа {orderno}: {e}")
            dump_debug(driver, f"debug_{orderno}")
            return None

    def process_delivered_info(self, info):
        if info.get("Date parcel received"):
            return {
                "date": f"{info.get('Date parcel received', '')} {info.get('Time parcel received', '')}".strip(),
                "receipient": info.get("Delivery info", ""),
                "status": info.get("Status", ""),
            }
        return None
