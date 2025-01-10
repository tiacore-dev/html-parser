# parsers/sib_express.py

import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.parsers.parse import parse_sib_express_response

# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger('parser')


def get_csrf_token(session, url):
    response = session.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': '_token'})['value']
    return csrf_token


@retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(5),
    reraise=True
)
def make_post_request(session, url, data, headers):
    """
    Отправляет POST-запрос с использованием сессии, применяет повторные попытки при ошибках подключения.
    """
    response = session.post(url, data=data, headers=headers, timeout=30)
    response.raise_for_status()
    return response


def sib_express(orderno):
    """
    Парсит данные заказа из сервиса Сиб-Экспресс.

    :param orderno: Номер заказа
    :return: JSON-строка с результатами или ошибкой
    """
    session = requests.Session()
    url = os.getenv('URL_SIB_EXPRESS')

    # Параметры формы
    data = {
        "name": orderno,
        "tab": "1"
    }
    csrf_token = get_csrf_token(session, url)
    data["_token"] = csrf_token

    # Куки
    cookies = {
        "_ym_uid": "1734680388574908198",
        "_ym_d": "1734680388",
        "_ym_visorc": "w",
        "_ga_YKHVYXWK0P": "GS1.1.1734680388.1.0.1734680388.0.0.0",
        "_ym_isad": "2",
        "_ga": "GA1.2.845727486.1734680388",
        "_gid": "GA1.2.1752836982.1734680388",
        "_gat_gtag_UA_69478068_8": "1",
        "XSRF-TOKEN": "eyJpdiI6IkErVExBZXVMTUtsd21mamdEcjVkemc9PSIsInZhbHVlIjoicXhrS3BJS0hGV2xBR3FkOVRcL09tUm1TNlBqMnVRc0hXSkQxY1wvVDhvT2VDeEN2dGY3Ylwvc1J1eHk4NDFjc0Q2c1VKXC9EY3FOd0RVcDgzSkdOQ3RjVDR3PT0iLCJtYWMiOiI4MjQ1YTFjYWRkZTM3ZjRjMjhhZmZhOTUxYWU2ZDlkNDBiZjU3Njg4YTY0MTY0ZTg1ZDU0NmE1NWVhMDAzOGNkIn0",
        "sibirskiy_ekspress_session": "eyJpdiI6InlSTVgwQyswTDYrTzYwMFM3NndcL29nPT0iLCJ2YWx1ZSI6Ik0xVHVkdCtOT2JtZEVMRldSc0Jmb0dwRFhCcGVOeCt2akVRSm4xandkcit5VzRXNWpnQ2JoVE5ybms2UWp4WmVzdENVOVVveklKWk45NWp1THcxYkVnPT0iLCJtYWMiOiI2YmMzZGVlZWQwZjFhMmEyYTg4YjMwY2Q4NmQ4YzgyM2QwNjkyOGE2NGZjNjRhMzA0ZWVjMzczYmZkZGY1ODRkIn0"
    }

    # Удаляем лишние пробелы и переносы строк из значений куков
    cleaned_cookies = {key: value.strip().replace("\n", "")
                       for key, value in cookies.items()}

    # Заголовки запроса
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8,it;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.sib-express.ru",
        "Referer": "https://www.sib-express.ru/tracker",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }

    try:
        response = session.post(
            url, data=data, headers=headers, cookies=cleaned_cookies, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for order {orderno}: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

    html = response.text

    # Вызов функции парсинга
    info = parse_sib_express_response(html, orderno)
    if info:
        for key, value in info.items():
            rec = value.split(' ')
            result = {
                "date": key,
                "receipient": rec[2] if len(rec) > 2 else (rec[1] if len(rec) > 1 else None),
                "Status": rec[0] if len(rec) > 0 else None
            }
    else:
        result = None

    return result
