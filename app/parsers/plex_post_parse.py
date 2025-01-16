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
    """
    Открываем страницу plexpost.ru/tracking/,
    вводим накладную в поле name='codes',
    кликаем на кнопку 'Проверить', ждем появления результатов в блоке #tracking-results.
    После чего «ленивым» способом разбиваем результат по строкам, 
    разделяя «дату» и «статус» по разделителю " - ".
    """
    url = os.getenv(
        'URL_PLEX_POST')

    driver = create_firefox_driver()
    driver.get(url)

    try:
        # 1) Ждем появления поля ввода: id="tn", name="codes"
        code_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "codes"))
        )
        code_field.clear()
        code_field.send_keys(order_code)
        logger.info(f"Код накладной {order_code} введён.")

        # 2) Нажимаем на кнопку с id="btn-tracking"
        submit_button = driver.find_element(By.ID, "btn-tracking")
        submit_button.click()
        logger.info("Кнопка 'Проверить' нажата.")

        # 3) Ждем, пока появится блок с результатом: id="tracking-results"
        result_block = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "tracking-results"))
        )
        logger.info("Результаты отслеживания появились.")

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
                results.append({
                    "Дата": date_part,
                    "Статус": status_part
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
