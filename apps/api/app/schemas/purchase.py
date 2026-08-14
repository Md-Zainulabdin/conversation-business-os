import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from app.schemas.validators import (
    validate_non_negative,
    validate_quantity,
    validate_required_str,
)


class PurchaseItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int
    purchase_price: Decimal
    total_amount: Decimal

    _validate_quantity = field_validator("quantity")(validate_quantity)
    _validate_prices = field_validator("purchase_price", "total_amount")(
        validate_non_negative
    )


class PurchaseCreate(BaseModel):
    supplier_name: str
    items: Annotated[list[PurchaseItemCreate], Field(min_length=1)]
    purchase_date: datetime
    notes: str | None = None

    _validate_supplier = field_validator("supplier_name")(validate_required_str)


class PurchaseItemUpdate(BaseModel):
    product_id: uuid.UUID
    quantity: int
    purchase_price: Decimal
    total_amount: Decimal

    _validate_quantity = field_validator("quantity")(validate_quantity)
    _validate_prices = field_validator("purchase_price", "total_amount")(
        validate_non_negative
    )


class PurchaseUpdate(BaseModel):
    supplier_name: str | None = None
    items: list[PurchaseItemUpdate] | None = None
    purchase_date: datetime | None = None
    notes: str | None = None

    _validate_supplier = field_validator("supplier_name")(validate_required_str)


class PurchaseItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    quantity: int
    purchase_price: Decimal
    total_amount: Decimal

    model_config = {"from_attributes": True}


class PurchaseResponse(BaseModel):
    id: uuid.UUID
    supplier_name: str
    total_amount: Decimal
    purchase_date: datetime
    notes: str | None
    items: list[PurchaseItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}