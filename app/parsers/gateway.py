import logging
import time
import requests
from app.parsers.sp_service_tyumen_parse import sp_service_tyumen  # pylint: disable=unused-import
from app.parsers.sp_service_ekaterinburg_parse import sp_service_ekaterinburg  # pylint: disable=unused-import
from app.parsers.rasstoyaniya_net_parse import rasstoyaniya_net  # pylint: disable=unused-import
from app.parsers.sib_express_parse import sib_express  # pylint: disable=unused-import
from app.parsers.svs import get_orders, set_orders
# Получаем логгер по его имени
logger = logging.getLogger('parser')


partners = {
    "sp_service_tyumen": "26d49356-559c-11eb-80ef-74d43522d93b",
    "sp_service_ekaterinburg": "1d4be527-c61e-11e7-9bdb-74d43522d93b",
    "sib_express": "33c8793d-96c2-11e7-b541-00252274a609",
    "rasstoyaniya_net": "b3116f3b-9f4a-11e7-a536-00252274a609"
}


def parser_main():
    for key, value in partners.items():
        orders = get_orders(value)
        # Проверка и вызов функции по имени ключа
        function = globals().get(key)
        if not function:
            logger.error(f"Функция {key} не найдена.")
            continue
        for order in orders:
            order_number = order.get('number')
            if not order_number:
                logger.warning("Номер заказа отсутствует в данных.")
                continue
            try:
                info = function(order_number)

                if value == "26d49356-559c-11eb-80ef-74d43522d93b" or value == "1d4be527-c61e-11e7-9bdb-74d43522d93b":
                    if info['Status'] == "Delivered":
                        order_id = order.get('id')
                        set_orders(info, order_id)
                elif value == "b3116f3b-9f4a-11e7-a536-00252274a609":
                    if info['Status'] == "Доставлено":
                        order_id = order.get('id')
                        set_orders(info, order_id)
                        # Здесь вы можете обрабатывать полученную информацию (info) по своему усмотрению
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error for order {order_number}: {e}")
                # Можно реализовать дополнительную обработку, например, сохранить неуспешный заказ для повторной попытки
            except Exception as e:
                logger.error(f"Error processing order {order_number}: {e}")
            # Задержка между запросами (например, 2 секунды)
            time.sleep(15)
