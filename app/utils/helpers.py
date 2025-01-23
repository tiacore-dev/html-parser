# utils/helpers.py

import re
import logging
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

logger = logging.getLogger('parser')


def clean_html(html):
    """
    Удаляет лишние </div> внутри <td>, учитывая пробельные символы и переносы строк.
    """
    cleaned_html = re.sub(r'</div>\s*</td>', '</td>',
                          html, flags=re.IGNORECASE)
    return cleaned_html


def create_firefox_driver():
    try:
        options = Options()
        options.headless = True  # Headless-режим
        driver = webdriver.Firefox(options=options)
        return driver
    except Exception as e:
        logger.error(f"Ошибка при создании драйвера Firefox: {e}")
        raise
