import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from app.schemas.validators import validate_non_negative, validate_quantity


class SaleItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    total_amount: Decimal

    _validate_quantity = field_validator("quantity")(validate_quantity)
    _validate_prices = field_validator("unit_price", "total_amount")(validate_non_negative)


class SaleCreate(BaseModel):
    customer_id: uuid.UUID | None = None
    items: Annotated[list[SaleItemCreate], Field(min_length=1)]
    sale_date: datetime
    notes: str | None = None


class SaleItemUpdate(BaseModel):
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    total_amount: Decimal

    _validate_quantity = field_validator("quantity")(validate_quantity)
    _validate_prices = field_validator("unit_price", "total_amount")(validate_non_negative)


class SaleUpdate(BaseModel):
    customer_id: uuid.UUID | None = None
    items: list[SaleItemUpdate] | None = None
    sale_date: datetime | None = None
    notes: str | None = None


class SaleItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    total_amount: Decimal

    model_config = {"from_attributes": True}


class SaleResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID | None
    customer_name: str | None
    total_amount: Decimal
    sale_date: datetime
    notes: str | None
    items: list[SaleItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}