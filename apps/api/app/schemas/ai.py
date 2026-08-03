from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, field_validator

from app.schemas.validators import (
    validate_non_negative,
    validate_quantity,
    validate_required_str,
)

Intent = Literal["sale", "purchase", "expense", "inquiry", "other"]

# Strict-mode JSON schema for Groq structured outputs. All keys are required
# (strict mode constraint); optional fields use nullable types.
AI_COMMAND_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": ["sale", "purchase", "expense", "inquiry", "other"],
        },
        "product_name": {"type": ["string", "null"]},
        "quantity": {"type": ["integer", "null"]},
        "unit_price": {"type": ["number", "null"]},
        "total_amount": {"type": ["number", "null"]},
        "customer_name": {"type": ["string", "null"]},
        "supplier_name": {"type": ["string", "null"]},
        "title": {"type": ["string", "null"]},
        "category": {"type": ["string", "null"]},
        "notes": {"type": ["string", "null"]},
        "date": {"type": ["string", "null"]},
    },
    "required": [
        "intent",
        "product_name",
        "quantity",
        "unit_price",
        "total_amount",
        "customer_name",
        "supplier_name",
        "title",
        "category",
        "notes",
        "date",
    ],
    "additionalProperties": False,
}


class AICommand(BaseModel):
    intent: Intent
    product_name: str | None = None
    quantity: int | None = None
    unit_price: Decimal | None = None
    total_amount: Decimal | None = None
    customer_name: str | None = None
    supplier_name: str | None = None
    title: str | None = None
    category: str | None = None
    notes: str | None = None
    date: datetime | None = None
    product_unit: str | None = None
    stock_after: int | None = None

    _validate_quantity = field_validator("quantity")(validate_quantity)
    _validate_prices = field_validator("unit_price", "total_amount")(
        validate_non_negative
    )
    _validate_text = field_validator(
        "product_name",
        "customer_name",
        "supplier_name",
        "title",
        "category",
        "notes",
    )(validate_required_str)


class AICommandRequest(BaseModel):
    message: str

    _validate_message = field_validator("message")(validate_required_str)


class AIProposalResponse(BaseModel):
    command: AICommand
    requires_confirmation: bool
    message: str


class AIExecuteRequest(BaseModel):
    command: AICommand


class AIExecuteResponse(BaseModel):
    message: str
    record: dict
