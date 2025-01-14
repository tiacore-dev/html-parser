import logging
import os
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('parser')
url = os.getenv('URL_VIP_MAIL_UFA')


def create_firefox_driver():
    try:
        options = Options()
        options.headless = True  # Headless-режим
        driver = webdriver.Firefox(options=options)
        return driver
    except Exception as e:
        logger.error(f"Ошибка при создании драйвера Firefox: {e}")
        raise


def track_package(tracking_number):
    driver = create_firefox_driver()
    driver.get(url)

    try:

        # Вводим номер накладной
        number_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "number"))
        )
        number_field.send_keys(tracking_number)
        # logger.info(f"Номер накладной {tracking_number} введен.")

        # Нажимаем кнопку "Отправить"
        submit_button = driver.find_element(By.NAME, "submit")
        submit_button.click()
        # logger.info("Кнопка отправки нажата.")

        # Ждем появления таблицы с результатами
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "show_tracks"))
        )
        # logger.info("Таблица с результатами успешно найдена.")

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
            f"ВипМайл Уфа. Данные отслеживания успешно извлечены: {results}")
        return results

    except Exception as e:
        logger.error(f"""ВипМайл Уфа. Ошибка при обработке заказа {
                     tracking_number}: {e}""")
        return None
    finally:
        driver.quit()
        # logger.info("Браузер закрыт.")


def vip_mail_ufa(orderno):
    try:
        response = track_package(orderno)
        return response
    except Exception as e:
        logger.error(f'ВипМайл Уфа. Ошибка при выполнении парсинга: {e}')
        return None


def extract_delivered_info_vip_mail(events):
    """
    Фильтрует события со статусом "Доставлено" и извлекает нужные данные.

    :param events: Список событий (словарей) с ключами "Дата", "Состояние", "Примечания".
    :return: Список доставленных событий с отфильтрованной информацией.
    """
    delivered_entries = [
        {
            "date": event["Дата"],
            # Получатель из "Примечания"
            "recipient": event.get("Примечания", "Не указано"),
            "status": "Доставлено"  # Переименовываем статус
        }
        for event in events if "доставлено" in event["Состояние"].lower()
    ]
    return delivered_entries
