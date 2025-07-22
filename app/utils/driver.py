from contextlib import contextmanager

from loguru import logger

from app.utils.helpers import create_firefox_driver


@contextmanager
def selenium_driver():
    driver = create_firefox_driver()
    try:
        yield driver
    finally:
        logger.info("Драйвер выключен")
        driver.quit()
