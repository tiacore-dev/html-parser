import logging
import os
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Настройка логирования

logger = logging.getLogger('parser')

# Загрузка переменных окружения
load_dotenv()


@retry(
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(5),
    reraise=True
)
def make_request(orderno):
    """
    Отправляет запрос к API и возвращает результат.
    :param order_id: Номер заказа
    :return: Данные заказа в формате JSON
    """
    url = os.getenv('URL_POST_MASTER')
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,ru;q=0.8,it;q=0.7",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://www.post-master.ru",
        "referer": "https://www.post-master.ru/status/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    data = f"command=track_orders&order_id%5B%5D={orderno}"
    response = requests.post(url, headers=headers, data=data, timeout=30)
    response.raise_for_status()
    return response.json()


def post_master(orderno):
    """
    Обрабатывает заказ, отправляя запрос и парся ответ.
    :param order_id: Номер заказа
    :return: Результат обработки
    """
    try:
        response = make_request(orderno)
        logger.info(f"""Пост Мастер. Полученные данные для заказа {
                    orderno}: {response}""")
        info = {"order_id": orderno, "entries": []}
        # Обработка данных из JSON
        if isinstance(response, list):
            for entry in response:
                order_entry = {
                    "Накладная": entry.get("VDOCNUMBER"),
                    "Город отправки": entry.get("VSENDERCITY"),
                    "Город доставки": entry.get("VDELIVERYCITY"),
                    "Дата": entry.get("VDATE"),
                    "Статус": entry.get("VPOINT"),
                }
                info["entries"].append(order_entry)
            logger.info(f"Пост Мастер. Распарсенные данные: {info}")
            return info
        else:
            logger.error(f"""Пост Мастер.Неожиданный формат ответа для заказа {
                         orderno}: {response}""")
            return None
    except Exception as e:
        logger.error(f"""Пост Мастер. Ошибка при обработке заказа {
                     orderno}: {e}""")
        return None


def extract_delivered_info_master(order_data):
    """
    Извлекает информацию о доставленных заказах.

    :param order_data: Словарь с данными заказа
    :return: Список словарей с информацией о доставке
    """
    delivered_entries = []

    for entry in order_data.get("entries", []):
        if "доставлено" in entry.get("Статус", "").lower():
            delivered_info = {
                "date": entry.get("Дата"),
                # Получатель после слова "Доставлено"
                "recipient": entry.get("Статус").split()[-1],
                "status": "Доставлено"
            }
            delivered_entries.append(delivered_info)

    return delivered_entries
