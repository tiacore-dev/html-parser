from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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

            wait = WebDriverWait(driver, 15)

            # Ждём хотя бы один блок событий
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.window__trace_content")))

            data = []

            # Все блоки с информацией
            blocks = driver.find_elements(By.CSS_SELECTOR, "div.window__trace_content")

            if not blocks:
                logger.warning(f"{self.name}. Нет блоков с информацией по заказу {orderno}")
                return None

            # Последний блок — статусные события
            last_block = blocks[-1]
            rows = last_block.find_elements(By.CSS_SELECTOR, "div.window__trace_row")
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

            # Предпоследний блок — данные получателя
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

        except TimeoutException:
            logger.error(f"{self.name}. Timeout при заказе {orderno}")
            return None
        except NoSuchElementException as e:
            logger.error(f"{self.name}. Элемент не найден при заказе {orderno}: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при парсинге заказа {orderno}: {e}")
            return None
        finally:
            driver.quit()

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
