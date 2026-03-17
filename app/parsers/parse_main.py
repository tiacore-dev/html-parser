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


async def save_log(
    partner_id, order_id, order_number, parser_name, success, status=None, error_message=None, raw_data=None
):
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


PARSER_REGISTRY = {
    "vip_mail_ufa": {"partner_id": "90b470a2-a775-11e7-ad08-74d43522d93b", "parser": VIPMailUfaParser()},
    "arsexpress": {"partner_id": "1034e0be-855a-11ea-80dd-74d43522d93b", "parser": ArsexpressParser()},
    "rasstoyaniya_net": {"partner_id": "b3116f3b-9f4a-11e7-a536-00252274a609", "parser": RasstoyaniyaNetParser()},
    "plex_post": {"partner_id": "d56a2a0c-6339-11e8-80b5-74d43522d93b", "parser": PlexPostParser()},
    "bizon_express": {"partner_id": "6208860c-f583-11ef-9de4-a1ec92d2beb8", "parser": BizonExpressParser()},
    "avis_logistics": {"partner_id": "076db763-9c54-11e7-aa9c-00252274a609", "parser": AvisLogisticsParser()},
    "sp_service_tyumen": {"partner_id": "26d49356-559c-11eb-80ef-74d43522d93b", "parser": SPServiceTyumenParser()},
    "sib_express": {"partner_id": "33c8793d-96c2-11e7-b541-00252274a609", "parser": SibExpressParser()},
    "sp_service_ekaterinburg": {
        "partner_id": "1d4be527-c61e-11e7-9bdb-74d43522d93b",
        "parser": SPServiceEkaterinburgParser(),
    },
}

partners = {item["partner_id"]: item["parser"] for item in PARSER_REGISTRY.values()}


def get_parser_debug_list():
    return [
        {"parser_key": parser_key, "partner_id": parser_info["partner_id"], "parser_name": parser_info["parser"].name}
        for parser_key, parser_info in PARSER_REGISTRY.items()
    ]


def get_parser_for_debug(parser_key: str):
    return PARSER_REGISTRY.get(parser_key)


def get_parser_orders_for_debug(parser_key: str):
    parser_info = get_parser_for_debug(parser_key)
    if parser_info is None:
        return None

    orders = get_orders(parser_info["partner_id"])
    return {
        "parser_key": parser_key,
        "partner_id": parser_info["partner_id"],
        "parser_name": parser_info["parser"].name,
        "orders": orders,
    }


async def process_orders_for_partner(partner_id, parser: BaseParser, orders=None):
    logger.info(f"🔍 Обработка заказов для партнёра: {parser.name} ({partner_id})")
    if orders is None:
        orders = get_orders(partner_id)

    if isinstance(orders, dict) and orders.get("error"):
        logger.warning(f"Не удалось получить заказы для партнёра {parser.name}: {orders['error']}")
        await save_log(partner_id, None, "", parser.name, success=False, error_message=orders["error"])
        return {
            "partner_id": partner_id,
            "name": parser.name,
            "total": 0,
            "parsed": 0,
            "delivered": 0,
            "undelivered": 0,
            "failed": 0,
            "error": orders["error"],
        }

    total = 0
    parsed = 0
    delivered = 0
    undelivered = 0
    failed = 0

    if not orders:
        logger.warning(f"Нет заказов для партнёра {parser.name}")
        await save_log(partner_id, None, "", parser.name, success=False, error_message="Нет заказов")
        return {
            "partner_id": partner_id,
            "name": parser.name,
            "total": 0,
            "parsed": 0,
            "delivered": 0,
            "undelivered": 0,
            "failed": 0,
        }

    for order in orders:
        total += 1
        order_id = order.get("id")
        order_number = order.get("number")

        if not order_number:
            logger.warning(f"⚠️ Отсутствует номер заказа для партнёра {partner_id}")
            await save_log(
                partner_id, order_id, None, parser.name, success=False, error_message="Отсутствует номер заказа"
            )
            failed += 1
            continue

        try:
            with selenium_driver() as driver:
                info = parser.parse(order_number, driver)

                if info is None:
                    logger.warning(f"❌ Ошибка парсинга для заказа {order_number}")
                    await save_log(
                        partner_id,
                        order_id,
                        order_number,
                        parser.name,
                        success=False,
                        status="Ошибка парсинга",
                        raw_data={},
                    )
                    failed += 1
                    continue

                if not info:  # ловит {} и None
                    logger.info(f"🔍 Заказ {order_number} не найден")
                    await save_log(
                        partner_id, order_id, order_number, parser.name, success=True, status="Не найден", raw_data={}
                    )
                    undelivered += 1
                    continue

                parsed += 1
                result = parser.process_delivered_info(info)

                if result is None:
                    logger.warning(f"⚠️ Пустой результат для заказа {order_number}")
                    undelivered += 1
                    await save_log(
                        partner_id,
                        order_id,
                        order_number,
                        parser.name,
                        success=True,
                        status="Не доставлено",
                        raw_data=info,
                    )
                    continue

                if await set_orders(result, order_id, order_number, partner_id, parser.name):
                    delivered += 1
                else:
                    logger.warning(f"⚠️ Не удалось установить статус у {order_number}")
                    failed += 1

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


async def run_parser_for_debug(parser_key: str):
    parser_info = get_parser_for_debug(parser_key)
    if parser_info is None:
        return None

    orders = get_orders(parser_info["partner_id"])
    if isinstance(orders, dict) and orders.get("error"):
        return {
            "parser_key": parser_key,
            "partner_id": parser_info["partner_id"],
            "parser_name": parser_info["parser"].name,
            "summary": await process_orders_for_partner(parser_info["partner_id"], parser_info["parser"], orders=orders),
        }

    return {
        "parser_key": parser_key,
        "partner_id": parser_info["partner_id"],
        "parser_name": parser_info["parser"].name,
        "summary": await process_orders_for_partner(parser_info["partner_id"], parser_info["parser"], orders=orders),
    }


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
