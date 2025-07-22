# utils/helpers.py

import os
import re

from loguru import logger
from selenium import webdriver
from selenium.webdriver import FirefoxOptions


def clean_html(html):
    """
    Удаляет лишние </div> внутри <td>, учитывая пробельные символы и переносы строк.
    """
    cleaned_html = re.sub(r"</div>\s*</td>", "</td>", html, flags=re.IGNORECASE)
    return cleaned_html


def dump_debug(driver, name):
    with open(f"/tmp/{name}.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    driver.save_screenshot(f"/tmp/{name}.png")


def create_firefox_driver(remote: bool = True):
    options = FirefoxOptions()
    options.add_argument("-headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    options.set_capability("pageLoadStrategy", "eager")
    options.set_capability("acceptInsecureCerts", True)
    options.set_capability("browserName", "firefox")

    if remote:
        logger.info("🚗 Попытка запуска Firefox драйвера (Remote)")
        selenium_url = os.getenv("SELENIUM_REMOTE_URL", "http://selenium:4444/wd/hub")
        logger.info(f"🔗 Подключение к Selenium: {selenium_url}")

        try:
            driver = webdriver.Remote(command_executor=selenium_url, options=options)
        except Exception as e:
            logger.exception(f"❌ Ошибка при создании remote-драйвера: {e}")
            raise
    else:
        logger.info("🚗 Локальный запуск Firefox драйвера")
        try:
            driver = webdriver.Firefox(options=options)
        except Exception as e:
            logger.exception(f"❌ Ошибка при создании локального драйвера: {e}")
            raise

    # Общие таймауты
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)
    driver.set_script_timeout(15)
    driver.set_window_size(1920, 1080)

    logger.info("✅ Драйвер успешно создан и таймауты установлены")
    return driver
