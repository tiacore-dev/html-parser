import os

from dotenv import load_dotenv
from loguru import logger
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.parsers.base_parser import BaseParser
from app.utils.helpers import create_firefox_driver

load_dotenv()


class VIPMailUfaParser(BaseParser):
    url = os.getenv("URL_VIP_MAIL_UFA", "")
    name = "ВипМайл Уфа"
    DEFAULT_WAIT_TIME = 30

    def parse(self, orderno):
        try:
            driver = create_firefox_driver()
        except Exception as e:
            logger.error(f"Ошибка создания драйвера: {e}")
            return None

        try:
            driver.get(self.url)
        except Exception as e:
            logger.error(f"Ошибка при driver.get(): {e}")
            return None

        try:
            # Вводим номер накладной
            number_field = WebDriverWait(driver, self.DEFAULT_WAIT_TIME).until(EC.presence_of_element_located((By.NAME, "number")))
            number_field.send_keys(orderno)
            # logger.info(f"Номер накладной {tracking_number} введен.")

            # Нажимаем кнопку "Отправить"
            submit_button = driver.find_element(By.NAME, "submit")
            submit_button.click()
            # logger.info("Кнопка отправки нажата.")

            # Ждем появления таблицы с результатами
            table = WebDriverWait(driver, self.DEFAULT_WAIT_TIME).until(EC.presence_of_element_located((By.CLASS_NAME, "show_tracks")))
            logger.info(f"{self.name}. Таблица с результатами успешно найдена: {table}.")

            # Извлекаем данные из таблицы
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Пропускаем заголовок
            results = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                results.append(
                    {
                        "Дата": cells[0].text,
                        "Состояние": cells[1].text,
                        "Примечания": cells[2].text,
                    }
                )

            logger.info(f"{self.name}. Данные отслеживания успешно извлечены: {results}")
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
            if "доставлено" in event["Состояние"].lower():
                return {
                    "date": event["Дата"],
                    # Получатель из "Примечания"
                    "receipient": event.get("Примечания", "Не указано"),
                    "status": "Доставлено",  # Переименовываем статус
                }
        return None
