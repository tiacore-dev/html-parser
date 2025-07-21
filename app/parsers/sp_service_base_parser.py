from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.parsers.base_parser import BaseParser
from app.utils.helpers import create_firefox_driver


class SPServiceBaseParser(BaseParser):
    def parse(self, orderno):
        try:
            driver = create_firefox_driver()
        except Exception as e:
            logger.error(f"{self.name}. Ошибка создания драйвера: {e}")
            return None

        try:
            full_url = f"{self.url}?orderno={orderno}&singlebutton=submit"
            driver.get(full_url)

            logger.info(f"{self.name}. Текущий URL: {driver.current_url}")
            logger.info(f"Заголовок страницы: {driver.title}")

            # Ждём появления таблицы до 15 секунд
            wait = WebDriverWait(driver, 15)
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-striped")))
            rows = table.find_elements(By.TAG_NAME, "tr")

            if "не найден" in driver.page_source.lower():
                logger.warning(f"{self.name}. Заказ {orderno} не найден на странице.")
                return None

            data = {}
            for row in rows:
                tds = row.find_elements(By.TAG_NAME, "td")
                if len(tds) >= 2:
                    key = tds[0].text.strip().rstrip(":")
                    value = tds[1].text.strip()
                    data[key] = value

            logger.info(f"{self.name}. Полученные данные для заказа {orderno}: {data}")
            return data

        except TimeoutException as e:
            logger.error(f"{self.name}. Таймаут при заказе {orderno}: {e}")
            return None
        except NoSuchElementException as e:
            logger.error(f"{self.name}. Элемент не найден: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при обработке заказа {orderno}: {e}")
            return None
        finally:
            driver.quit()

    def process_delivered_info(self, info):
        if info.get("Date parcel received"):
            return {
                "date": f"{info.get('Date parcel received', '')} {info.get('Time parcel received', '')}".strip(),
                "receipient": info.get("Delivery info", ""),
                "status": info.get("Status", ""),
            }
        return None
