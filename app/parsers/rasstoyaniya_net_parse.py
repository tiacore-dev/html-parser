# parsers/rasstoyaniya_net.py

import os
import json
import logging
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.parsers.parse import parse_rasstoyaniya_net_response

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


def rasstoyaniya_net(orderno):
    """
    Парсит данные заказа из сервиса Расстояния.нет.

    :param orderno: Номер заказа
    :return: JSON-строка с результатами или ошибкой
    """
    url = os.getenv('URL_RASTOYANIYA')
    if not url:
        logger.error("URL_RASTOYANIYA не установлен в переменных окружения.")
        return json.dumps({"error": "URL_RASTOYANIYA not set"}, ensure_ascii=False)

    # Параметры формы
    data = {
        "FindForm[bill]": orderno
    }

    # Заголовки запроса
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,ru;q=0.8,it;q=0.7",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "cookie": os.getenv('COOKIES_RASTOYANIYA'),
        "origin": "https://www.rasstoyanie.net",
        "priority": "u=1, i",
        "referer": f"https://www.rasstoyanie.net/tracking/index?orderno={orderno}&singlebutton=submit",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    # Проверка наличия необходимых куки
    if not os.getenv('COOKIES_RASTOYANIYA'):
        logger.error(
            "COOKIES_RASTOYANIYA не установлены в переменных окружения.")
        return json.dumps({"error": "COOKIES_RASTOYANIYA not set"}, ensure_ascii=False)

    session = requests.Session()

    try:
        response = make_post_request(session, url, data=data, headers=headers)
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for order {orderno}: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

    try:
        response_data = response.json()
    except json.JSONDecodeError:
        logger.error(
            f"Не удалось разобрать JSON-ответ для заказа {
                orderno}. Ответ: {response.text}"
        )
        return json.dumps({"error": "Invalid JSON response"}, ensure_ascii=False)

    logger.info(
        f"""Расстояния.нет. Полученные данные для order number {
            orderno}: {response_data}"""
    )

    # Вызов функции парсинга
    return parse_rasstoyaniya_net_response(response_data, orderno)
