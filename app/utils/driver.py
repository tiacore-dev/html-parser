from contextlib import contextmanager

from loguru import logger

from app.utils.helpers import create_firefox_driver


@contextmanager
def selenium_driver():
    driver = create_firefox_driver()
    try:
        yield driver
    finally:
        logger.info("⏹️ Закрытие драйвера...")
        try:
            driver.quit()
            logger.info("✅ Драйвер успешно завершён")
        except Exception as e:
            logger.warning(f"❌ Ошибка при закрытии драйвера: {e}")
