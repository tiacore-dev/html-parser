import logging
import time
import requests
from app.parsers.sp_service_tyumen_parse import sp_service_tyumen  # pylint: disable=unused-import
from app.parsers.sp_service_ekaterinburg_parse import sp_service_ekaterinburg  # pylint: disable=unused-import
from app.parsers.rasstoyaniya_net_parse import rasstoyaniya_net  # pylint: disable=unused-import
from app.parsers.sib_express_parse import sib_express  # pylint: disable=unused-import
from app.parsers.svs import get_orders, set_orders

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

                if info:

                    if value == "26d49356-559c-11eb-80ef-74d43522d93b":
                        if info and info['Date parcel received']:
                            result = {
                                "date": f"{info['Date parcel received']} {info['Time parcel received']}",
                                "receipient": f"{info['Delivery info']}",
                                "Status": info['Status']
                            }
                        else:
                            result = None
                        if result['Status'] == "Delivered":
                            order_id = order.get('id')
                            name = "СП-Сервис Тюмень"
                            set_orders(result, order_id, name)

                    elif value == "1d4be527-c61e-11e7-9bdb-74d43522d93b":
                        if info and info['Date parcel received']:
                            result = {
                                "date": f"{info['Date parcel received']} {info['Time parcel received']}",
                                "receipient": f"{info['Delivery info']}",
                                "Status": info['Status']
                            }
                        else:
                            result = None
                        if result['Status'] == "Delivered":
                            order_id = order.get('id')
                            name = "СП-Сервис Екатеринбург"
                            set_orders(result, order_id, name)

                    elif value == "b3116f3b-9f4a-11e7-a536-00252274a609":
                        if info:
                            result = {
                                "date": f"{info['Дата доставки']}",
                                "receipient": f"{info['Получатель']}",
                                "Status": f"{info['Статус']}"
                            }
                        else:
                            result = None
                        if result['Status'] == "Доставлена" or result['Status'] == "Доставлено":
                            order_id = order.get('id')
                            name = "Расстояния нет"
                            set_orders(result, order_id, name)

                    elif value == "33c8793d-96c2-11e7-b541-00252274a609":
                        if info:
                            for key, value in info.items():
                                rec = value.split(' ')
                                result = {
                                    "date": key,
                                    "receipient": rec[2] if len(rec) > 2 else (rec[1] if len(rec) > 1 else None),
                                    "Status": rec[0] if len(rec) > 0 else None
                                }
                        else:
                            result = None
                        if result['Status'] == "Доставлено":
                            order_id = order.get('id')
                            name = "Сибирский Экспресс"
                            set_orders(result, order_id, name)

            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error for order {order_number}: {e}")
                # Можно реализовать дополнительную обработку, например, сохранить неуспешный заказ для повторной попытки
            except Exception as e:
                logger.error(f"Error processing order {order_number}: {e}")
            # Задержка между запросами (например, 2 секунды)
            time.sleep(15)
