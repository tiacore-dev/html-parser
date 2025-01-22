import logging
import time
import requests
from app.parsers.sp_service_tyumen_parse import sp_service_tyumen  # pylint: disable=unused-import
from app.parsers.sp_service_ekaterinburg_parse import sp_service_ekaterinburg  # pylint: disable=unused-import
from app.parsers.rasstoyaniya_net_parse import rasstoyaniya_net  # pylint: disable=unused-import
from app.parsers.sib_express_parse import sib_express, extract_delivered_info_sib  # pylint: disable=unused-import
from app.parsers.post_master_parse import post_master, extract_delivered_info_master  # pylint: disable=unused-import
from app.parsers.plex_post_parse import plex_post, extract_delivered_info_plex  # pylint: disable=unused-import
from app.parsers.vip_mail_ufa_parse import vip_mail_ufa, extract_delivered_info_vip_mail  # pylint: disable=unused-import
from app.parsers.svs import get_orders, set_orders

logger = logging.getLogger('parser')


partners = {
    "sp_service_tyumen": "26d49356-559c-11eb-80ef-74d43522d93b",
    "sp_service_ekaterinburg": "1d4be527-c61e-11e7-9bdb-74d43522d93b",
    "sib_express": "33c8793d-96c2-11e7-b541-00252274a609",
    "rasstoyaniya_net": "b3116f3b-9f4a-11e7-a536-00252274a609",
    "post_master": "1034e0be-855a-11ea-80dd-74d43522d93b",
    "plex_post": "d56a2a0c-6339-11e8-80b5-74d43522d93b",
    "vip_mail_ufa": "90b470a2-a775-11e7-ad08-74d43522d93b"
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
                        if info['Date parcel received']:
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
                        if info['Date parcel received']:
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
                        result = {
                            "date": f"{info['Дата доставки']}",
                            "receipient": f"{info['Получатель']}",
                            "Status": f"{info['Статус']}"
                        }
                        if (result['Status'] == "Доставлена" or result['Status'] == "Доставлено") and result['receipient'] != 'Сдано в ТК':
                            order_id = order.get('id')
                            name = "Расстояния нет"
                            set_orders(result, order_id, name)

                    elif value == "33c8793d-96c2-11e7-b541-00252274a609":
                        result = extract_delivered_info_sib(info)
                        if result:
                            order_id = order.get('id')
                            name = "Сибирский Экспресс"
                            set_orders(result, order_id, name)

                    elif value == "1034e0be-855a-11ea-80dd-74d43522d93b":
                        result = extract_delivered_info_master(info)
                        if result:
                            order_id = order.get('id')
                            name = "Пост Мастер"
                            set_orders(result, order_id, name)

                    elif value == "d56a2a0c-6339-11e8-80b5-74d43522d93b":
                        result = extract_delivered_info_plex(info)
                        if result:
                            order_id = order.get('id')
                            name = "Плекс Пост"
                            set_orders(result, order_id, name)

                    elif value == "90b470a2-a775-11e7-ad08-74d43522d93b":
                        result = extract_delivered_info_vip_mail(info)
                        if result:
                            order_id = order.get('id')
                            name = "ВипМайл Уфа"
                            set_orders(result, order_id, name)

            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error for order {order_number}: {e}")
                # Можно реализовать дополнительную обработку, например, сохранить неуспешный заказ для повторной попытки
            except Exception as e:
                logger.error(f"Error processing order {order_number}: {e}")
            # Задержка между запросами (например, 2 секунды)
            time.sleep(15)
