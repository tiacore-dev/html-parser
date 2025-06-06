import logging
import os
from dotenv import load_dotenv
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from app.parsers.base_parser import BaseParser
from app.utils.helpers import create_firefox_driver


load_dotenv()

logger = logging.getLogger('parser')


class VIPMailUfaParser(BaseParser):
    url = os.getenv('URL_VIP_MAIL_UFA')
    name = "ВипМайл Уфа"
    DEFAULT_WAIT_TIME = 30

    def get_html(self, orderno):
        """Метод не нужен для VIPMailUfaParser."""
        raise NotImplementedError(
            f"Метод 'get_html' не реализован в {self.name}.")

    def parse(self, orderno):
        driver = create_firefox_driver()
        driver.get(self.url)
        try:
            # Вводим номер накладной
            number_field = WebDriverWait(driver, self.DEFAULT_WAIT_TIME).until(
                EC.presence_of_element_located((By.NAME, "number"))
            )
            number_field.send_keys(orderno)
            # logger.info(f"Номер накладной {tracking_number} введен.")

            # Нажимаем кнопку "Отправить"
            submit_button = driver.find_element(By.NAME, "submit")
            submit_button.click()
            # logger.info("Кнопка отправки нажата.")

            # Ждем появления таблицы с результатами
            table = WebDriverWait(driver, self.DEFAULT_WAIT_TIME).until(
                EC.presence_of_element_located((By.CLASS_NAME, "show_tracks"))
            )
            logger.info(
                f"{self.name}. Таблица с результатами успешно найдена: {table}.")

            # Извлекаем данные из таблицы
            rows = table.find_elements(By.TAG_NAME, "tr")[
                1:]  # Пропускаем заголовок
            results = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                results.append({
                    "Дата": cells[0].text,
                    "Состояние": cells[1].text,
                    "Примечания": cells[2].text,
                })

            logger.info(
                f"{self.name}. Данные отслеживания успешно извлечены: {results}")
            return results
        except TimeoutException as e:
            logger.error(f"""{self.name}. Элемент не найден для заказа {
                         orderno}: {e}""")
            return None
        except Exception as e:
            logger.error(f"""{self.name}. Ошибка при обработке заказа {
                orderno}: {e}""")
            return None

        finally:
            driver.quit()

    def process_delivered_info(self, info):
        for event in info:
            if "доставлено" in event["Состояние"].lower():
                return {
                    "date": event["Дата"],
                    # Получатель из "Примечания"
                    "receipient": event.get("Примечания", "Не указано"),
                    "status": "Доставлено"  # Переименовываем статус
                }
        return None
