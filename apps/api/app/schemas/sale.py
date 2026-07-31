import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.schemas.validators import validate_non_negative, validate_quantity


class SaleCreate(BaseModel):
    customer_id: uuid.UUID | None = None
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    sale_date: datetime
    notes: str | None = None

    _validate_quantity = field_validator("quantity")(validate_quantity)
    _validate_prices = field_validator("unit_price", "total_amount")(validate_non_negative)


class SaleUpdate(BaseModel):
    customer_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    quantity: int | None = None
    unit_price: Decimal | None = None
    total_amount: Decimal | None = None
    sale_date: datetime | None = None
    notes: str | None = None

    _validate_quantity = field_validator("quantity")(validate_quantity)
    _validate_prices = field_validator("unit_price", "total_amount")(validate_non_negative)


class SaleResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID | None
    customer_name: str | None
    product_id: uuid.UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    sale_date: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
