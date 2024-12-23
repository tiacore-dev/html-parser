# parsers/sib_express.py

import os
import json
import logging
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.parsers.parse import parse_sib_express_response

# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger('parser')


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
    url = os.getenv('URL_SIB_EXPRESS')
    if not url:
        logger.error("URL_SIB_EXPRESS не установлен в переменных окружения.")
        return json.dumps({"error": "URL_SIB_EXPRESS not set"}, ensure_ascii=False)

    # Параметры формы
    data = {
        "_token": os.getenv('TOKEN_SIB_EXPRESS'),  # Токен CSRF
        "name": orderno,
        "tab": "1"
    }

    # Заголовки запроса
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8,it;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": os.getenv('COOKIES_SIB_EXPRESS'),
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

    # Проверка наличия необходимых куки и токена
    if not os.getenv('COOKIES_SIB_EXPRESS'):
        logger.error(
            "COOKIES_SIB_EXPRESS не установлены в переменных окружения.")
        return json.dumps({"error": "COOKIES_SIB_EXPRESS not set"}, ensure_ascii=False)

    if not os.getenv('TOKEN_SIB_EXPRESS'):
        logger.error("TOKEN_SIB_EXPRESS не установлен в переменных окружения.")
        return json.dumps({"error": "TOKEN_SIB_EXPRESS not set"}, ensure_ascii=False)

    session = requests.Session()

    try:
        response = make_post_request(session, url, data=data, headers=headers)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for order {orderno}: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

    html = response.text

    # Вызов функции парсинга
    return parse_sib_express_response(html, orderno)