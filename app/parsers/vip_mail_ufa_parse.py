import logging
import os
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('parser')

url = os.getenv('URL_VIP_MAIL_UFA')

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')


def track_package(tracking_number):
    # Настройка Selenium
    driver = webdriver.Chrome(options=options)  # Или другой драйвер
    driver.get(url)

    try:
        # Найти поле для ввода номера накладной
        number_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "number"))
        )
        number_field.send_keys(tracking_number)

        # Нажать кнопку "Отправить"
        submit_button = driver.find_element(By.NAME, "submit")
        submit_button.click()

        # Дождаться таблицы с результатами
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "show_tracks"))
        )

        # Извлечь данные из таблицы
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

        return results
    except Exception as e:
        logger.error(f"""ВипМайл Уфа. Ошибка при парсинге для заказа: {
                     tracking_number}""")
    finally:
        driver.quit()


"""def get_initial_session():
    session = requests.Session()
    response = session.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Извлекаем `sessid` и `PARAMS_HASH`
    sessid = soup.find("input", {"name": "sessid"}).get("value")
    params_hash = soup.find("input", {"name": "PARAMS_HASH"}).get("value")

    logging.info(f"Получены sessid: {sessid}, PARAMS_HASH: {params_hash}")
    return session, sessid, params_hash


def track_package_session(session, sessid, params_hash, number):
    data = {
        "sessid": sessid,
        "number": number,
        "PARAMS_HASH": params_hash,
        "submit": "Отправить",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "content-type": "application/x-www-form-urlencoded",
        "referer": url,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    response = session.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.text

"""


def make_request(orderno):
    """
    Отправляет запрос к API и возвращает HTML-ответ.
    :param orderno: Номер заказа
    :return: HTML-контент ответа
    """
    try:
        # Шаг 1: Получение сессии
        # session, sessid, params_hash = get_initial_session()

        # Отправляем запрос на отслеживание
        tracking_html = track_package(orderno)
        logging.info("Получены данные отслеживания.")

        # html_response = response.text
        # decoded_html = decode_response_content(response)
        logging.info(f"""ВипМайл Уфа. Ответ сервера для заказа {
                     orderno}: {tracking_html}""")
        return tracking_html  # Возвращаем HTML
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе: {e}")
        raise


def vip_mail_ufa(orderno):
    try:
        response = make_request(orderno)
        # info = parse_vip_mail_ufa(response, orderno)
        return response
    except Exception as e:
        logging.error(f'ВипМайл Уфа. Ошибка при выполнении парсинга: {e}')
        return None
