from loguru import logger
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from app.parsers.base_parser import BaseParser
from app.utils.helpers import create_firefox_driver
from config import Settings


class AvisLogisticsParser(BaseParser):
    url = Settings.URL_AVIS_LOGISTICS
    name = "Авис-Логистик"
    DEFAULT_WAIT_TIME = 30

    def parse(self, orderno):
        try:
            driver = create_firefox_driver()
        except Exception as e:
            logger.error(f"{self.name}. Ошибка создания драйвера: {e}")
            return None

        try:
            trace_url = f"{self.url}?trace={orderno}"
            driver.get(trace_url)

            logger.info(f"{self.name}. Текущий URL: {driver.current_url}")
            logger.info(f"Заголовок страницы: {driver.title}")

            data = []

            # Ждём и парсим последние события (окно со статусами)
            rows = driver.find_elements(By.CSS_SELECTOR, "div.window__trace_content:last-of-type div.window__trace_row")
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

            # Блок с получателем/администратором (предпоследний блок)
            blocks = driver.find_elements(By.CSS_SELECTOR, "div.window__trace_content")
            if len(blocks) >= 2:
                receiver_rows = blocks[-2].find_elements(By.CSS_SELECTOR, "div.window__trace_row")
                if receiver_rows:
                    last = receiver_rows[-1].find_elements(By.CSS_SELECTOR, "div.trace__row_title.text")
                    if len(last) == 3:
                        data.append({"date": last[0].text.strip(), "receiver_name": last[1].text.strip(), "receiver_role": last[2].text.strip(), "status": "receiver"})

            if not data:
                logger.warning(f"{self.name}. Нет данных по заказу {orderno}")
                return None

            logger.info(f"{self.name}. Данные по заказу {orderno}: {data}")
            return data

        except TimeoutException as e:
            logger.error(f"{self.name}. Timeout при заказе {orderno}: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при парсинге заказа {orderno}: {e}")
            return None
        finally:
            driver.quit()

    def process_delivered_info(self, info):
        result = None
        for event in info:
            if len(event) > 0 and event.get("status") == "Доставлено":
                receiver_info = info[-1]
                if receiver_info.get("receiver_name"):
                    result = {
                        "date": event["date"],
                        "receipient": receiver_info["receiver_name"],
                        "status": "Доставлено",
                    }
        return result
