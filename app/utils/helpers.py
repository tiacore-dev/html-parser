# utils/helpers.py

import os
import re

from loguru import logger
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


def clean_html(html):
    """
    Удаляет лишние </div> внутри <td>, учитывая пробельные символы и переносы строк.
    """
    cleaned_html = re.sub(r"</div>\s*</td>", "</td>", html, flags=re.IGNORECASE)
    return cleaned_html


def create_firefox_driver():
    logger.info("🚗 Попытка запуска Firefox драйвера (Remote)")

    options = Options()
    options.add_argument("-headless")
    options.set_capability("browserName", "firefox")
    options.set_capability("acceptInsecureCerts", True)

    selenium_url = os.getenv("SELENIUM_REMOTE_URL", "http://selenium:4444/wd/hub")
    logger.info(f"🔗 Подключение к Selenium: {selenium_url}")

    try:
        driver = webdriver.Remote(command_executor=selenium_url, options=options)

        # Установка таймаутов
        driver.set_page_load_timeout(30)  # 30 секунд на загрузку страницы
        driver.implicitly_wait(10)  # 10 секунд ожидания элементов
        driver.set_script_timeout(15)  # 15 секунд на выполнение скриптов

        logger.info("✅ Драйвер успешно создан и таймауты установлены")
        return driver
    except Exception as e:
        logger.exception(f"❌ Ошибка при создании драйвера: {e}")
        raise
