from loguru import logger
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.parsers.base_parser import BaseParser
from app.utils.helpers import create_firefox_driver

# Загрузка переменных окружения
from config import Settings


class PlexPostParser(BaseParser):
    url = Settings.URL_PLEX_POST
    name = "Плекс Пост"
    DEFAULT_WAIT_TIME = 30

    def get_html(self, orderno):
        """Метод не нужен для PlexPostParser."""
        raise NotImplementedError(f"Метод 'get_html' не реализован в {self.name}.")

    def parse(self, orderno):
        driver = create_firefox_driver()
        driver.get(self.url)
        try:
            # 1) Ждем появления поля ввода: id="tn", name="codes"
            code_field = WebDriverWait(driver, self.DEFAULT_WAIT_TIME).until(EC.presence_of_element_located((By.NAME, "codes")))
            code_field.clear()
            code_field.send_keys(orderno)

            # 2) Нажимаем на кнопку с id="btn-tracking"
            submit_button = driver.find_element(By.ID, "btn-tracking")
            submit_button.click()

            # 3) Ждем, пока появится блок с результатом: id="tracking-results"
            result_block = WebDriverWait(driver, self.DEFAULT_WAIT_TIME).until(EC.presence_of_element_located((By.ID, "tracking-results")))

            # 4) «Ленивый» вариант: берем весь текст из result_block
            all_text = result_block.text
            # Пример строки: "09.01.2025 07:42 - Поступило на склад Самара"
            # Разделяем по переносам
            lines = all_text.splitlines()

            results = []
            for line in lines:
                # Ожидаем формат: "дата - статус"
                parts = line.split(" - ", 1)  # делим один раз
                if len(parts) == 2:
                    date_part = parts[0].strip()
                    status_part = parts[1].strip()
                    results.append({"Дата": date_part, "Статус": status_part})

            logger.info(f"{self.name}. Данные отслеживания: {results}")
            return results
        except TimeoutException as e:
            logger.error(f"""{self.name}. Элемент не найден для заказа {orderno}: {e}""")
            return None
        except Exception as e:
            logger.error(f"""{self.name}. Ошибка при обработке заказа {orderno}: {e}""")
            return None

        finally:
            driver.quit()

    def process_delivered_info(self, info):
        for event in info:
            if "доставлено" in event["Статус"].lower():
                return {
                    "date": event["Дата"],
                    "receipient": event["Статус"].split()[-1],
                    "status": "Доставлено",
                }
        return None
