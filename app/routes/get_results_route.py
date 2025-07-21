from fastapi import APIRouter, Depends
from tortoise.expressions import Q

from app.database.models import ParsingLog
from app.handlers.auth_handler import check_api_key
from app.pydantic_models.result_models import ParsingLogFilterSchema, ParsingLogListResponseSchema, ParsingLogSchema

# Создаем роутеры
parse_router = APIRouter()


@parse_router.get("/logs", response_model=ParsingLogListResponseSchema)
async def get_logs(filters: ParsingLogFilterSchema = Depends(), _=Depends(check_api_key)):
    query = Q()

    if filters.date_from:
        query &= Q(parsed_at__gte=filters.date_from)
    if filters.date_to:
        query &= Q(parsed_at__lte=filters.date_to)
    if filters.partner_id:
        query &= Q(partner_id=filters.partner_id)
    if filters.order_number:
        query &= Q(order_number__icontains=filters.order_number)
    if filters.parser_name:
        query &= Q(parser_name__icontains=filters.parser_name)
    if filters.success is not None:
        query &= Q(success=filters.success)
    if filters.status:
        query &= Q(status__icontains=filters.status)

    total = await ParsingLog.filter(query).count()
    logs = await ParsingLog.filter(query).order_by("-parsed_at").limit(100)

    return ParsingLogListResponseSchema(total=total, logs=[ParsingLogSchema.model_validate({**log.__dict__, "raw_data": log.raw_data if isinstance(log.raw_data, dict) else None}) for log in logs])
