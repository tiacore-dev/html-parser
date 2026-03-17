import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.handlers.auth_handler import check_api_key
from app.parsers import parse_main
from app.utils.driver import selenium_driver

parsing_router = APIRouter()


class ParserDebugRequest(BaseModel):
    parser_key: str = Field(..., description="Ключ парсера, например vip_mail_ufa")
    order_number: str = Field(..., min_length=1, description="Номер заказа для ручного теста")


@parsing_router.get("/dev/parsers")
async def list_parsers(_=Depends(check_api_key)):
    return {"parsers": parse_main.get_parser_debug_list()}


@parsing_router.get("/dev/parsers/{parser_key}/orders")
async def get_parser_orders(parser_key: str, _=Depends(check_api_key)):
    parser_orders = parse_main.get_parser_orders_for_debug(parser_key)
    if parser_orders is None:
        raise HTTPException(status_code=404, detail=f"Парсер '{parser_key}' не найден")

    orders = parser_orders["orders"]
    if isinstance(orders, dict) and orders.get("error"):
        raise HTTPException(status_code=502, detail=orders["error"])

    return {
        "parser_key": parser_orders["parser_key"],
        "partner_id": parser_orders["partner_id"],
        "parser_name": parser_orders["parser_name"],
        "total": len(orders) if isinstance(orders, list) else 0,
        "orders": [
            {
                "order_id": order.get("id"),
                "order_number": order.get("number"),
                "raw_order": order,
            }
            for order in orders
        ]
        if isinstance(orders, list)
        else [],
    }


@parsing_router.post("/dev/parsers/run")
async def run_parser_debug(payload: ParserDebugRequest, _=Depends(check_api_key)):
    parser_info = parse_main.get_parser_for_debug(payload.parser_key)
    if parser_info is None:
        raise HTTPException(status_code=404, detail=f"Парсер '{payload.parser_key}' не найден")

    parser = parser_info["parser"]

    def _run_parser():
        with selenium_driver() as driver:
            raw_data = parser.parse(payload.order_number, driver)
            processed_data = None if raw_data in (None, {}, []) else parser.process_delivered_info(raw_data)
            return {
                "parser_key": payload.parser_key,
                "partner_id": parser_info["partner_id"],
                "parser_name": parser.name,
                "order_number": payload.order_number,
                "raw_data": raw_data,
                "processed_data": processed_data,
            }

    return await asyncio.to_thread(_run_parser)


@parsing_router.post("/dev/parsers/{parser_key}/run-all")
async def run_parser_all_orders(parser_key: str, _=Depends(check_api_key)):
    result = await parse_main.run_parser_for_debug(parser_key)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Парсер '{parser_key}' не найден")

    summary = result["summary"]
    if summary.get("error"):
        raise HTTPException(status_code=502, detail=summary["error"])

    return result
