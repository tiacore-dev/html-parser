from loguru import logger
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from app.parsers.base_parser import BaseParser
from app.utils.helpers import create_firefox_driver
from config import Settings


class RasstoyaniyaNetParser(BaseParser):
    name = "Расстояния нет"
    url = Settings.URL_RASTOYANIYA

    def parse(self, orderno):
        try:
            driver = create_firefox_driver()
        except Exception as e:
            logger.error(f"{self.name}. Ошибка создания драйвера: {e}")
            return None

        try:
            # Переход на страницу поиска
            driver.get(self.url)

            # Ввод номера накладной
            input_field = driver.find_element(By.NAME, "FindForm[bill]")
            input_field.clear()
            input_field.send_keys(orderno)

            # Отправка формы (обычно кнопка с type="submit")
            submit_button = driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
            submit_button.click()

            # Ждём загрузки таблицы и заголовка
            driver.implicitly_wait(5)

            # Извлечение заголовка
            header_elem = driver.find_element(By.CSS_SELECTOR, "h5.find-header")
            invoice = header_elem.text.strip()

            # Извлечение таблицы
            table = driver.find_element(By.CSS_SELECTOR, "table.detail-view#quick_find")
            rows = table.find_elements(By.TAG_NAME, "tr")

            data = {"invoice": invoice}
            for row in rows:
                ths = row.find_elements(By.TAG_NAME, "th")
                tds = row.find_elements(By.TAG_NAME, "td")
                if ths and tds:
                    key = ths[0].text.strip().rstrip(":")
                    value = tds[0].text.strip()
                    data[key] = value

            logger.info(f"{self.name}. Полученные данные для заказа {orderno}: {data}")
            return data

        except TimeoutException as e:
            logger.error(f"{self.name}. Таймаут при заказе {orderno}: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при обработке заказа {orderno}: {e}")
            return None
        finally:
            driver.quit()

    def process_delivered_info(self, info):
        if info.get("Статус") in ("Доставлена", "Доставлено") and info.get("Получатель") != "Сдано в ТК":
            return {
                "date": info.get("Дата доставки", ""),
                "receipient": info.get("Получатель", ""),
                "status": info.get("Статус", ""),
            }
        return None
