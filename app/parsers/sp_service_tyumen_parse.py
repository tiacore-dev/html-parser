# parsers/sp_service_tyumen.py

import os
import json
import logging
import requests
from dotenv import load_dotenv

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


# Предполагается, что вы добавите функцию парсинга для СП-Сервис
from app.parsers.parse import parse_sp_service_response

# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger('parser')


@retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(5),
    reraise=True
)
def make_request(session, url, method='GET', params=None, data=None, headers=None):
    """
    Отправляет HTTP-запрос с использованием сессии, применяет повторные попытки при ошибках подключения.
    """
    if method.upper() == 'GET':
        response = session.get(url, params=params, headers=headers, timeout=30)
    elif method.upper() == 'POST':
        response = session.post(url, data=data, headers=headers, timeout=30)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    response.raise_for_status()
    return response


def sp_service_tyumen(orderno):
    """
    Парсит данные заказа из СП-Сервис Тюмень.

    :param orderno: Номер заказа
    :return: JSON-строка с результатами или ошибкой
    """
    url = os.getenv('URL_TYUMEN')
    if not url:
        logger.error("URL_TYUMEN не установлен в переменных окружения.")
        return json.dumps({"error": "URL_TYUMEN not set"}, ensure_ascii=False)

    # Параметры запроса
    params = {
        "orderno": orderno,
        "singlebutton": "submit"
    }

    # Заголовки запроса
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
                  "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9,ru;q=0.8,it;q=0.7",
        "cookie": os.getenv('COOKIES_TYUMEN'),
        "priority": "u=0, i",
        "referer": f"https://home.courierexe.ru/178/tracking?orderno={orderno}&singlebutton=submit",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "iframe",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    # Проверка наличия необходимых куки
    if not os.getenv('COOKIES_TYUMEN'):
        logger.error("COOKIES_TYUMEN не установлены в переменных окружения.")
        return json.dumps({"error": "COOKIES_TYUMEN not set"}, ensure_ascii=False)

    session = requests.Session()

    try:
        response = make_request(
            session, url, method='GET', params=params, headers=headers)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for order {orderno}: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

    html = response.text

    return parse_sp_service_response(html, orderno, 'Тюмень')
