import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from app.schemas.validators import validate_positive_amount, validate_required_str


class ExpenseCreate(BaseModel):
    title: str
    category: str
    amount: Decimal
    expense_date: datetime
    notes: str | None = None

    _validate_amount = field_validator("amount")(validate_positive_amount)
    _validate_title = field_validator("title", "category")(validate_required_str)


class ExpenseUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    amount: Decimal | None = None
    expense_date: datetime | None = None
    notes: str | None = None

    _validate_amount = field_validator("amount")(validate_positive_amount)
    _validate_title = field_validator("title", "category")(validate_required_str)


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    title: str
    category: str
    amount: Decimal
    expense_date: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
