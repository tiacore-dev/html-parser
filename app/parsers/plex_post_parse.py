import logging
import os
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger('parser')


def create_firefox_driver():
    try:
        options = Options()
        options.headless = True  # Запуск в headless-режиме
        driver = webdriver.Firefox(options=options)
        return driver
    except Exception as e:
        logger.error(f"Ошибка при создании драйвера Firefox: {e}")
        raise


def track_package_plexpost(order_code):
    url = os.getenv('URL_PLEX_POST')
    driver = create_firefox_driver()
    driver.get(url)

    try:
        # Ждем появления поля ввода
        code_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "codes"))
        )
        code_field.clear()
        code_field.send_keys(order_code)
        # logger.info(f"Код {order_code} введен.")

        # Ищем кнопку. Допустим, она имеет атрибут name="submit" или другой
        submit_button = driver.find_element(By.ID, "check")  # Пример!
        submit_button.click()
        # logger.info("Кнопка отправки нажата.")

        # Ждем появления какого-то блока результата (нужно уточнять по реальной верстке)
        result_block = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "row_track"))  # Пример!
        )
        # logger.info("Результат появился.")

        # Парсим содержимое result_block
        # Допустим, каждая запись - это <div class="history_item"> или <tr> и т. д.
        # Нужно смотреть реальный HTML.
        rows = result_block.find_elements(
            By.CLASS_NAME, "some_history_class")  # Пример!

        results = []
        for row in rows:
            # В зависимости от структуры строки
            date_el = row.find_element(By.CLASS_NAME, "date_class")
            status_el = row.find_element(By.CLASS_NAME, "status_class")
            # и т. д.

            results.append({
                "Дата": date_el.text,
                "Статус": status_el.text
            })

        logger.info(f"Плекс Пост. Данные отслеживания: {results}")
        return results

    except Exception as e:
        logger.error(f"""Плекс Пост. Ошибка при обработке заказа {
                     order_code}: {e}""")
        return None
    finally:
        driver.quit()
        logger.info("Браузер закрыт.")


def plex_post(orderno):
    try:
        info = track_package_plexpost(orderno)
        # info = parse_plex_post(response, orderno)
        return info
    except Exception as e:
        logger.error(f'Плекс Пост. Ошибка при выполнении парсинга: {e}')
        return None


def extract_delivered_info_plex(events):
    """
    Проверяет и фильтрует события со статусом "Доставлено".

    :param events: Список событий
    :return: Список доставленных событий
    """
    result = None
    for event in events:
        if "доставлено" in event["Статус"].lower():
            result = {
                "date": event["Дата"],
                "receipient": event.get("Статус").split()[-1],
                "status": "Доставлено"  # Переименовываем статус
            }
    return result
