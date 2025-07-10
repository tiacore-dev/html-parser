# utils/helpers.py

import logging
import os
import re

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

logger = logging.getLogger("parser")


def clean_html(html):
    """
    Удаляет лишние </div> внутри <td>, учитывая пробельные символы и переносы строк.
    """
    cleaned_html = re.sub(r"</div>\s*</td>", "</td>", html, flags=re.IGNORECASE)
    return cleaned_html


def create_firefox_driver():
    logger.info("🚗 Попытка запуска Firefox драйвера")
    try:
        os.environ["DISPLAY"] = ":99"  # ключ для Xvfb
        options = Options()
        options.add_argument("-headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Firefox(options=options)
        logger.info("✅ Firefox драйвер успешно запущен")
        return driver
    except Exception as e:
        logger.exception(f"❌ Ошибка при создании Firefox драйвера: {e}")
        raise
