from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.parsers.base_parser import BaseParser

# Загрузка переменных окружения
from config import Settings


class PlexPostParser(BaseParser):
    url = Settings.URL_PLEX_POST
    name = "Плекс Пост"
    DEFAULT_WAIT_TIME = 30

    def parse(self, orderno, driver):
        try:
            driver.get(self.url)

            # Ждём появления поля ввода
            WebDriverWait(driver, self.DEFAULT_WAIT_TIME).until(EC.presence_of_element_located((By.NAME, "codes")))

            # Вводим номер накладной
            code_field = driver.find_element(By.NAME, "codes")
            code_field.clear()
            code_field.send_keys(orderno)

            # Жмём на кнопку
            driver.find_element(By.ID, "btn-tracking").click()

            # Ждём появления блока результатов
            WebDriverWait(driver, self.DEFAULT_WAIT_TIME).until(EC.presence_of_element_located((By.ID, "tracking-results")))

            # Проверяем, появился ли alert с предупреждением
            try:
                warning_elem = driver.find_element(By.CLASS_NAME, "alert-warning")
                if "По введенным накладным данных нет" in warning_elem.text:
                    logger.warning(f"{self.name}. Для заказа {orderno} нет данных на сайте.")
                    return []
            except NoSuchElementException:
                pass  # предупреждения нет, продолжаем

            # Парсим результат
            result_block = driver.find_element(By.ID, "tracking-results")
            all_text = result_block.text
            lines = all_text.splitlines()

            results = []
            for line in lines:
                parts = line.split(" - ", 1)
                if len(parts) == 2:
                    date_part, status_part = parts[0].strip(), parts[1].strip()
                    results.append({"Дата": date_part, "Статус": status_part})

            logger.info(f"{self.name}. Данные отслеживания: {results}")
            return results

        except TimeoutException as e:
            logger.error(f"{self.name}. Таймаут при обработке заказа {orderno}: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.name}. Ошибка при обработке заказа {orderno}: {e}")
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
