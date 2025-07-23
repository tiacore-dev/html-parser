import asyncio

import requests
from loguru import logger

from app.database.models import ParsingLog
from app.handlers.telegram_handler import send_report_to_telegram
from app.parsers.arsexpress_parser import ArsexpressParser
from app.parsers.avis_logistics_parser import AvisLogisticsParser
from app.parsers.base_parser import BaseParser
from app.parsers.bizon_parser import BizonExpressParser
from app.parsers.plex_post_parser import PlexPostParser
from app.parsers.rasstoyaniya_net_parser import RasstoyaniyaNetParser
from app.parsers.sib_express_parser import SibExpressParser
from app.parsers.sp_service_ekaterinburg_parser import SPServiceEkaterinburgParser
from app.parsers.sp_service_tyumen_parser import SPServiceTyumenParser
from app.parsers.svs import get_orders, set_orders
from app.parsers.vip_mail_ufa_parser import VIPMailUfaParser
from app.utils.driver import selenium_driver


async def save_log(partner_id, order_id, order_number, parser_name, success, status=None, error_message=None, raw_data=None):
    await ParsingLog.create(
        partner_id=partner_id,
        order_id=order_id,
        order_number=order_number,
        parser_name=parser_name,
        success=success,
        status=status,
        error_message=error_message,
        raw_data=raw_data,
    )


partners = {
    "90b470a2-a775-11e7-ad08-74d43522d93b": VIPMailUfaParser(),
    "1034e0be-855a-11ea-80dd-74d43522d93b": ArsexpressParser(),
    "b3116f3b-9f4a-11e7-a536-00252274a609": RasstoyaniyaNetParser(),
    "d56a2a0c-6339-11e8-80b5-74d43522d93b": PlexPostParser(),
    "6208860c-f583-11ef-9de4-a1ec92d2beb8": BizonExpressParser(),
    "076db763-9c54-11e7-aa9c-00252274a609": AvisLogisticsParser(),
    "26d49356-559c-11eb-80ef-74d43522d93b": SPServiceTyumenParser(),
    "33c8793d-96c2-11e7-b541-00252274a609": SibExpressParser(),
    "1d4be527-c61e-11e7-9bdb-74d43522d93b": SPServiceEkaterinburgParser(),
}


async def process_orders_for_partner(partner_id, parser: BaseParser):
    logger.info(f"🔍 Обработка заказов для партнёра: {parser.name} ({partner_id})")
    orders = get_orders(partner_id)

    total = 0
    parsed = 0
    delivered = 0
    undelivered = 0
    failed = 0

    if not orders:
        logger.warning(f"Нет заказов для партнёра {parser.name}")
        await save_log(partner_id, None, "", parser.name, success=False, error_message="Нет заказов")
        return {"partner_id": partner_id, "name": parser.name, "total": 0, "parsed": 0, "delivered": 0, "undelivered": 0, "failed": 0}

    for order in orders:
        total += 1
        order_id = order.get("id")
        order_number = order.get("number")

        if not order_number:
            logger.warning(f"⚠️ Отсутствует номер заказа для партнёра {partner_id}")
            await save_log(partner_id, order_id, None, parser.name, success=False, error_message="Отсутствует номер заказа")
            failed += 1
            continue

        try:
            with selenium_driver() as driver:
                info = parser.parse(order_number, driver)
                result = parser.process_delivered_info(info) if info else None

                if result is None:
                    logger.warning(f"⚠️ Пустой результат для заказа {order_number}")
                    await save_log(partner_id, order_id, order_number, parser.name, success=False, status="Пустой результат", raw_data=info or [])
                    failed += 1
                    continue

                parsed += 1
                status = result.get("status", "").lower()

                # Отправка данных
                if status in {"доставлено", "выдано"}:
                    if set_orders(result, order_id, parser.name):
                        delivered += 1
                    else:
                        failed += 1  # не удалось установить статус
                else:
                    undelivered += 1  # корректный результат, но ещё не доставлено

                await save_log(
                    partner_id,
                    order_id,
                    order_number,
                    parser.name,
                    success=True,
                    status=result.get("status", "Нет статуса"),
                    raw_data=info or [],
                )

        except Exception as e:
            handle_error(order_number, e)
            await save_log(partner_id, order_id, order_number, parser.name, success=False, error_message=str(e))
            failed += 1

        await asyncio.sleep(15)

    return {
        "partner_id": partner_id,
        "name": parser.name,
        "total": total,
        "parsed": parsed,
        "delivered": delivered,
        "undelivered": undelivered,
        "failed": failed,
    }


def handle_error(order_number, error):
    if isinstance(error, requests.exceptions.ConnectionError):
        logger.error(f"Connection error for order {order_number}: {error}")
    else:
        logger.error(f"Error processing order {order_number}: {error}")


async def parser_main():
    logger.info("🚀 Последовательная обработка всех партнёров")
    summary = []

    for partner_id, parser in partners.items():
        try:
            result = await process_orders_for_partner(partner_id, parser)
            summary.append(result)
        except Exception as e:
            logger.exception(f"❌ Ошибка при обработке партнёра {partner_id}: {e}")
            summary.append(
                {
                    "partner_id": partner_id,
                    "name": parser.name,
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "error": str(e),
                }
            )

    await send_report_to_telegram(summary)
