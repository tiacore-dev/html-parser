# utils/helpers.py

import os
import re
import time

from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


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


def retry_on_stale(retries=5, delay=0.5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except StaleElementReferenceException as e:
                    logger.warning(f"StaleElementReferenceException в {func.__name__} (попытка {attempt}/{retries}): {e}")
                    time.sleep(delay)
                except Exception:
                    raise
            logger.error(f"Не удалось выполнить {func.__name__} после {retries} попыток из-за StaleElementReferenceException")
            raise StaleElementReferenceException(f"{func.__name__} не удалось выполнить после {retries} попыток")

        return wrapper

    return decorator


def safe_click(driver, xpath, description="элемент"):
    wait = WebDriverWait(driver, 20)
    for attempt in range(5):
        try:
            logger.info(f"🖱️ Кликаем по {description} (попытка {attempt + 1})")
            element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                element,
            )
            element.click()
            return

        except (StaleElementReferenceException, ElementClickInterceptedException) as e:
            logger.warning(f"⚠️ {description} неактуален или перекрыт, пробуем ещё раз: {e}")
            time.sleep(1)

        except ElementNotInteractableException as e:
            logger.warning(f"⚠️ {description} неинтерактивен (возможно скрыт), пытаемся через JS: {e}")
            try:
                driver.execute_script("arguments[0].click();", element)
                return
            except Exception as js_e:
                logger.error(f"❌ Не получилось кликнуть по {description} даже через JS: {js_e}")
                time.sleep(1)

    raise Exception(f"❌ Не удалось кликнуть по {description} после 5 попыток (xpath: {xpath})")
