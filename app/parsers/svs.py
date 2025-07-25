import json

import requests
from loguru import logger

from config import Settings


def get_orders(customer) -> dict:
    """
    Получение заказов для указанного клиента.

    :param customer: Имя клиента
    :return: JSON-ответ с заказами или ошибка
    """
    url = Settings.URL_SVS_GET
    data = {"customer": customer}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=data, timeout=300)
        response.raise_for_status()
        logger.info(f"Успешно получены заказы для клиента {customer}.")
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"Превышено время ожидания при запросе заказов для клиента {customer}.")
        return {"error": "Timeout error"}
    except requests.exceptions.RequestException as e:
        logger.error(f"""Ошибка запроса при получении заказов для клиента {customer}: {e}""")
        return {"error": str(e)}
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON для клиента {customer}: {e}")
        return {"error": "Invalid JSON response"}


def set_orders(info, order_id, name) -> bool:
    """
    Установка статуса заказа.

    :param info: Информация о заказе (дата, получатель)
    :param order_id: Идентификатор заказа
    :return: None
    """
    url = Settings.URL_SVS_SET
    headers = {"Content-Type": "application/json"}

    data = {
        "authToken": {"userkey": f"{Settings.USER_KEY}", "token": f"{Settings.TOKEN}"},
        "parcelId": f"{order_id}",
        "recDate": info["date"],
        "recName": info["receipient"],
        "comment": name,
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=300)
        response.raise_for_status()
        logger.info(f"""{name}.Ответ сервера: {response.status_code}, {response.text}""")
        response_text = json.loads(response.text)
        if response_text.get("error") is False:
            logger.info(
                f"""Успешно установлен статус 'Доставлено' 
                для заказа {order_id} для сервиса {name}."""
            )
            return True
        else:
            logger.info(
                f"""Не удалось установить статус 'Доставлено' для 
                заказа {order_id} для сервиса {name}."""
            )
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка установки статуса для заказа {order_id} ({name}): {e}")
        return False
