import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    sku: str
    category: str
    unit: str
    purchase_price: Decimal = Decimal("0")
    selling_price: Decimal = Decimal("0")
    stock_quantity: int = 0
    minimum_stock: int = 0


class ProductUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    category: str | None = None
    unit: str | None = None
    purchase_price: Decimal | None = None
    selling_price: Decimal | None = None
    stock_quantity: int | None = None
    minimum_stock: int | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    sku: str
    category: str
    unit: str
    purchase_price: Decimal
    selling_price: Decimal
    stock_quantity: int
    minimum_stock: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
