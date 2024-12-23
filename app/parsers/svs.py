import os
import requests
from dotenv import load_dotenv

load_dotenv()


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
