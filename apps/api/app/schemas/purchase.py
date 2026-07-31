import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.schemas.validators import (
    validate_non_negative,
    validate_quantity,
    validate_required_str,
)


class PurchaseCreate(BaseModel):
    product_id: uuid.UUID
    supplier_name: str
    quantity: int
    purchase_price: Decimal
    total_amount: Decimal
    purchase_date: datetime
    notes: str | None = None

    _validate_quantity = field_validator("quantity")(validate_quantity)
    _validate_prices = field_validator("purchase_price", "total_amount")(validate_non_negative)
    _validate_supplier = field_validator("supplier_name")(validate_required_str)


class PurchaseUpdate(BaseModel):
    product_id: uuid.UUID | None = None
    supplier_name: str | None = None
    quantity: int | None = None
    purchase_price: Decimal | None = None
    total_amount: Decimal | None = None
    purchase_date: datetime | None = None
    notes: str | None = None

    _validate_quantity = field_validator("quantity")(validate_quantity)
    _validate_prices = field_validator("purchase_price", "total_amount")(validate_non_negative)
    _validate_supplier = field_validator("supplier_name")(validate_required_str)


class PurchaseResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    supplier_name: str
    quantity: int
    purchase_price: Decimal
    total_amount: Decimal
    purchase_date: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
