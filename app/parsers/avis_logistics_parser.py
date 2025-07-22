from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.parsers.base_parser import BaseParser
from app.utils.helpers import retry_on_stale
from config import Settings


class AvisLogisticsParser(BaseParser):
    url = Settings.URL_AVIS_LOGISTICS
    name = "Авис-Логистик"
    DEFAULT_WAIT_TIME = 30

    @retry_on_stale(retries=5, delay=1)
    def _parse_status_block(self, block):
        rows = block.find_elements(By.CSS_SELECTOR, "div.window__trace_row")
        data = []
        for row in rows:
            cols = row.find_elements(By.CSS_SELECTOR, "div.trace__row_title.text")
            if len(cols) == 3:
                data.append(
                    {
                        "date": cols[0].text.strip(),
                        "status": cols[1].text.strip(),
                        "city": cols[2].text.strip(),
                    }
                )
        return data

    @retry_on_stale(retries=5, delay=1)
    def _parse_receiver_info(self, block):
        receiver_rows = block.find_elements(By.CSS_SELECTOR, "div.window__trace_row")
        if receiver_rows:
            last = receiver_rows[-1].find_elements(By.CSS_SELECTOR, "div.trace__row_title.text")
            if len(last) == 3:
                return {"date": last[0].text.strip(), "receiver_name": last[1].text.strip(), "receiver_role": last[2].text.strip(), "status": "receiver"}
        return None

    def parse(self, orderno, driver):
        try:
            trace_url = f"{self.url}?trace={orderno}"
            driver.get(trace_url)

            logger.info(f"{self.name}. Текущий URL: {driver.current_url}")
            logger.info(f"Заголовок страницы: {driver.title}")

            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.window__trace_content")))

            blocks = driver.find_elements(By.CSS_SELECTOR, "div.window__trace_content")
            if not blocks:
                logger.warning(f"{self.name}. Нет блоков с информацией по заказу {orderno}")
                return None

            data = []

            # Последний блок — события
            last_block = blocks[-1]
            data.extend(self._parse_status_block(last_block))

            # Предпоследний блок — данные получателя
            if len(blocks) >= 2:
                receiver_info = self._parse_receiver_info(blocks[-2])
                if receiver_info:
                    data.append(receiver_info)

            if not data:
                logger.warning(f"{self.name}. Нет данных по заказу {orderno}")
                return None

            logger.info(f"{self.name}. Данные по заказу {orderno}: {data}")
            return data

        except TimeoutException:
            logger.error(f"{self.name}. Timeout при заказе {orderno}")
            return None
        except NoSuchElementException as e:
            logger.error(f"{self.name}. Элемент не найден при заказе {orderno}: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при парсинге заказа {orderno}: {e}")
            return None

    def process_delivered_info(self, info):
        result = None
        for event in info:
            if event.get("status") == "Доставлено":
                receiver_info = info[-1]
                if receiver_info.get("receiver_name"):
                    result = {
                        "date": event["date"],
                        "receipient": receiver_info["receiver_name"],
                        "status": "Доставлено",
                    }
        return result
