from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.parsers.base_parser import BaseParser
from app.utils.helpers import retry_on_stale, safe_click
from config import Settings


class RasstoyaniyaNetParser(BaseParser):
    name = "Расстояния нет"
    url = Settings.URL_RASTOYANIYA

    @retry_on_stale(retries=5, delay=1)
    def _parse_table_row(self, row):
        ths = row.find_elements(By.TAG_NAME, "th")
        tds = row.find_elements(By.TAG_NAME, "td")
        if ths and tds:
            key = ths[0].text.strip().rstrip(":")
            value = tds[0].text.strip()
            return key, value
        return None, None

    def parse(self, orderno, driver):
        try:
            driver.get(self.url)
            wait = WebDriverWait(driver, 15)

            input_field = wait.until(EC.presence_of_element_located((By.NAME, "FindForm[bill]")))
            input_field.clear()
            input_field.send_keys(orderno)

            # Устойчивый клик по кнопке "Отправить"
            safe_click(driver, "//form//button[@type='submit']", "кнопка Отправить")

            # Ждём заголовок или текст "Не найдено"
            wait.until(lambda d: "не найдено" in d.page_source.lower() or d.find_elements(By.CSS_SELECTOR, "h5.find-header"))

            if "не найдено" in driver.page_source.lower():
                logger.error(f"{self.name}. Заказ {orderno} не найден.")
                return None

            # Заголовок накладной
            header_elem = driver.find_element(By.CSS_SELECTOR, "h5.find-header")
            invoice = header_elem.text.strip()

            # Таблица с деталями
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.detail-view#quick_find")))
            rows = table.find_elements(By.TAG_NAME, "tr")

            data = {"invoice": invoice}
            for idx, row in enumerate(rows):
                try:
                    key, value = self._parse_table_row(row)
                    if key:
                        data[key] = value
                except Exception as e:
                    logger.warning(f"{self.name}. Ошибка при обработке строки {idx}: {e}")

            logger.info(f"{self.name}. Полученные данные для заказа {orderno}: {data}")
            return data

        except TimeoutException:
            logger.error(f"{self.name}. Таймаут при заказе {orderno}")
            return None
        except NoSuchElementException as e:
            logger.error(f"{self.name}. Элемент не найден: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при обработке заказа {orderno}: {e}")
            return None

    def process_delivered_info(self, info):
        if info.get("Статус") in ("Доставлена", "Доставлено") and info.get("Получатель") != "Сдано в ТК":
            return {
                "date": info.get("Дата доставки", ""),
                "receipient": info.get("Получатель", ""),
                "status": info.get("Статус", ""),
            }
        return None
