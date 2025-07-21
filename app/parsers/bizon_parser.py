from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.parsers.base_parser import BaseParser
from app.utils.helpers import create_firefox_driver
from config import Settings


class BizonExpressParser(BaseParser):
    url = Settings.URL_BIZON
    name = "Бизон Экспресс"
    DEFAULT_WAIT_TIME = 30

    def parse(self, orderno):
        try:
            driver = create_firefox_driver()
        except Exception as e:
            logger.error(f"{self.name}. Ошибка создания драйвера: {e}")
            return None

        try:
            full_url = f"{self.url}?orderno={orderno}&submit=1&singlebutton=submit"
            driver.get(full_url)

            logger.info(f"{self.name}. Текущий URL: {driver.current_url}")
            logger.info(f"Заголовок страницы: {driver.title}")

            wait = WebDriverWait(driver, 15)

            # Явное ожидание появления таблицы
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table")))
            rows = table.find_elements(By.TAG_NAME, "tr")

            data = {"invoice": orderno}
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) == 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    data[key] = value

            logger.info(f"{self.name}. Полученные данные для заказа {orderno}: {data}")
            return data

        except TimeoutException:
            logger.error(f"{self.name}. Таймаут при ожидании таблицы для заказа {orderno}")
            return None
        except NoSuchElementException as e:
            logger.error(f"{self.name}. Элемент не найден на странице заказа {orderno}: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при обработке заказа {orderno}: {e}")
            return None
        finally:
            driver.quit()

    def process_delivered_info(self, info):
        if info.get("Статус") == "Доставлен":
            return {
                "date": f"{info.get('Дата вручения', '')} {info.get('Время вручения', '')}".strip(),
                "receipient": info.get("Инфо о доставке", ""),
                "status": info["Статус"],
            }
        return None
