import logging
import os
import json
import html
import requests
from dotenv import load_dotenv
from app.parsers.parse import parse_plex_post

# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger('parser')


def send_request(order_code):
    url = os.getenv('URL_PLEX_POST')
    params = {
        "v": "1.4",
        "method": "getTracking",
        "token": "17e0b224abe4828d0a9ad369f8e2a256"
    }
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": "PHPSESSID=pidm8adq9j62bbah45p3tjeep2; city=%D0%A1%D0%B0%D0%BC%D0%B0%D1%80%D0%B0",
        "Origin": "http://plexpost.ru",
        "Referer": "http://plexpost.ru/tracking/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    data = {"codes": order_code}

    try:
        response = requests.post(
            url, params=params, headers=headers, data=data, timeout=30)

        # Байты в строку
        response_str = response.content.decode('utf-8')

        # Декодируем JSON
        parsed_data = json.loads(response_str)

        # Достаем HTML-контент
        decoded_html = html.unescape(parsed_data["content"])

        response.raise_for_status()
        return decoded_html
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса: {e}")
        return None


def plex_post(orderno):
    try:
        response = send_request(orderno)
        logger.info(f"""Плекс Пост. Полученный html для заказа {
                     orderno}: {response}""")
        info = parse_plex_post(response, orderno)
        return info
    except Exception as e:
        logger.error(f'Плекс Пост. Ошибка при выполнении парсинга: {e}')
        return None


def extract_delivered_info_plex(events):
    """
    Проверяет и фильтрует события со статусом "Доставлено".

    :param events: Список событий
    :return: Список доставленных событий
    """
    delivered_entries = [
        {
            "date": event["Дата"],
            "recipient": event.get("Статус").split()[-1],
            "status": "Доставлено"  # Переименовываем статус
        }
        for event in events if "доставлено" in event["Статус"].lower()
    ]
    return delivered_entries
