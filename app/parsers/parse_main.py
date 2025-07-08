import logging
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from app.parsers.avis_logistics_parser import AvisLogisticsParser
from app.parsers.bizon_parser import BizonExpressParser
from app.parsers.plex_post_parser import PlexPostParser
from app.parsers.post_master_parser import PostMasterParser
from app.parsers.rasstoyaniya_net_parser import RasstoyaniyaNetParser
from app.parsers.sib_express_parser import SibExpressParser
from app.parsers.sp_service_ekaterinburg_parser import SPServiceEkaterinburgParser
from app.parsers.sp_service_tyumen_parser import SPServiceTyumenParser
from app.parsers.svs import get_orders, set_orders
from app.parsers.vip_mail_ufa_parser import VIPMailUfaParser

logger = logging.getLogger("parser")


partners = {
    "26d49356-559c-11eb-80ef-74d43522d93b": SPServiceTyumenParser(),
    "1d4be527-c61e-11e7-9bdb-74d43522d93b": SPServiceEkaterinburgParser(),
    "33c8793d-96c2-11e7-b541-00252274a609": SibExpressParser(),
    "b3116f3b-9f4a-11e7-a536-00252274a609": RasstoyaniyaNetParser(),
    "1034e0be-855a-11ea-80dd-74d43522d93b": PostMasterParser(),
    "d56a2a0c-6339-11e8-80b5-74d43522d93b": PlexPostParser(),
    "90b470a2-a775-11e7-ad08-74d43522d93b": VIPMailUfaParser(),
    "6208860c-f583-11ef-9de4-a1ec92d2beb8": BizonExpressParser(),
    "076db763-9c54-11e7-aa9c-00252274a609": AvisLogisticsParser(),
}


def process_orders_for_partner(partner_id, parser):
    """Обрабатывает заказы для одного партнёра последовательно."""
    orders = get_orders(partner_id)
    if not orders:
        logger.warning(f"No orders found for partner {partner_id}.")
        return

    for order in orders:
        order_number = order.get("number")
        if not order_number:
            logger.warning(f"Order number is missing for partner {partner_id}.")
            continue

        try:
            info = parser.parse(order_number)
            if info:
                result = parser.process_delivered_info(info)
                if result:
                    order_id = order.get("id")
                    set_orders(result, order_id, parser.name)
        except Exception as e:
            handle_error(order_number, e)

        # Задержка между запросами для одного партнёра
        time.sleep(15)


def handle_error(order_number, error):
    if isinstance(error, requests.exceptions.ConnectionError):
        logger.error(f"Connection error for order {order_number}: {error}")
    else:
        logger.error(f"Error processing order {order_number}: {error}")


def parser_main():
    """Запускает обработку партнёров асинхронно."""
    with ThreadPoolExecutor(max_workers=7) as executor:  # Один поток на партнёра
        executor.map(
            lambda partner: process_orders_for_partner(*partner),
            partners.items(),  # Передаём кортеж (partner_id, parser)
        )
