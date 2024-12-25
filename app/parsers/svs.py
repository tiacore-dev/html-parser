import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger('parser')

token = os.getenv('TOKEN')
user_key = os.getenv('USER_KEY')


def get_orders(customer):
    url = os.getenv('URL_SVS_GET')
    data = {
        "customer": customer
    }
    headers = {
        "Content-Type": "application/json",
        # Исправление ошибки в названии ключа:
        "Content": "application/json"
    }
    response = requests.post(url, headers=headers, json=data, timeout=300)
    return response.json()


def set_orders(info, order_id):
    url = os.getenv('URL_SVS_SET')
    headers = {
        "content-type": "application/json"
    }
    data = {
        "auth_token": {
            "userkey": f"{user_key}",
            "token": f"{token}"
        },
        "parcelId": f"{order_id}",
        "recDate": info['date'],
        "recName": info['receipient'],
        "comment": ""
    }
    request = requests.post(url, headers=headers,
                            json=json.dumps(data), timeout=300)
    logger.info(f'''Статус запроса к SVS на установку статуса "Доставлено": {
                request.status_code}''')
