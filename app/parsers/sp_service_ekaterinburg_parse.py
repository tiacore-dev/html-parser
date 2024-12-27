# parsers/sp_service_ekaterinburg.py

import os
import json
import logging
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
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


def sp_service_ekaterinburg(orderno):
    """
    Парсит данные заказа из СП-Сервис Екатеринбург.

    :param orderno: Номер заказа
    :return: JSON-строка с результатами или ошибкой
    """
    url = os.getenv('URL_EKATERINBURG')

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
        "priority": "u=0, i",
        "referer": f"https://home.courierexe.ru/52/tracking?orderno={orderno}&singlebutton=submit",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "iframe",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    # Куки непосредственно в запросе
    cookies = {
        "PHPSESSID": "u9jo4hsn17irl8cg7vvf0qrecd"
    }

    session = requests.Session()

    try:
        response = session.get(
            url, params=params, headers=headers, cookies=cookies, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for order {orderno}: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

    html = response.text

    info = parse_sp_service_response(html, orderno, 'Екатеринбург')
    if info and info['Date parcel received']:
        result = {
            "date": f"{info['Date parcel received']} {info['Time parcel received']}",
            "receipient": f"{info['Delivery info']}",
            "Status": info['Status']
        }
    else:
        result = None
    return result
