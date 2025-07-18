from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ORMModel(BaseModel):
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        populate_by_name = True


class ParsingLogSchema(ORMModel):
    id: UUID = Field(..., alias="log_id")
    partner_id: UUID
    order_id: Optional[UUID] = None
    order_number: Optional[str] = None
    parser_name: str
    success: bool
    status: Optional[str] = None
    error_message: Optional[str] = None
    raw_data: Optional[dict] = None
    parsed_at: datetime


class ParsingLogListResponseSchema(ORMModel):
    total: int
    logs: List[ParsingLogSchema]


class ParsingLogFilterSchema(ORMModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    partner_id: Optional[UUID] = None
    order_number: Optional[str] = None
    parser_name: Optional[str] = None
    success: Optional[bool] = None
    status: Optional[str] = None
