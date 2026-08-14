from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, field_validator

from app.schemas.validators import (
    MAX_AMOUNT,
    MAX_QUANTITY,
    validate_non_negative,
    validate_quantity,
    validate_required_str,
)

Intent = Literal["sale", "purchase", "expense", "inquiry", "other"]
IssueKind = Literal[
    "not_found", "invalid_unit", "invalid_quantity", "invalid_price", "no_catalog"
]

MAX_MESSAGE_LENGTH = 2000
MAX_ITEMS = 25

# Strict-mode JSON schema for Groq structured outputs. All keys are required
# (strict mode constraint); optional fields use nullable types. Items holds
# one entry per product, so multi-product commands produce multiple entries.
AI_COMMAND_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": ["sale", "purchase", "expense", "inquiry", "other"],
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_name": {"type": ["string", "null"]},
                    "quantity": {"type": ["integer", "null"]},
                    "unit": {"type": ["string", "null"]},
                    "unit_price": {"type": ["number", "null"]},
                    "total_amount": {"type": ["number", "null"]},
                },
                "required": [
                    "product_name",
                    "quantity",
                    "unit",
                    "unit_price",
                    "total_amount",
                ],
                "additionalProperties": False,
            },
        },
        "customer_name": {"type": ["string", "null"]},
        "supplier_name": {"type": ["string", "null"]},
        "title": {"type": ["string", "null"]},
        "category": {"type": ["string", "null"]},
        "notes": {"type": ["string", "null"]},
        "date": {"type": ["string", "null"]},
        "total_amount": {"type": ["number", "null"]},
    },
    "required": [
        "intent",
        "items",
        "customer_name",
        "supplier_name",
        "title",
        "category",
        "notes",
        "date",
        "total_amount",
    ],
    "additionalProperties": False,
}


class ProductCandidate(BaseModel):
    id: str
    name: str
    unit: str
    selling_price: Decimal
    purchase_price: Decimal
    stock_quantity: int


class ItemIssue(BaseModel):
    kind: IssueKind
    name: str
    quantity: int | None = None
    detail: str | None = None


class AIItem(BaseModel):
    product_name: str | None = None
    quantity: int | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    total_amount: Decimal | None = None
    product_id: str | None = None
    product_unit: str | None = None
    stock_after: int | None = None

    _validate_quantity = field_validator("quantity")(validate_quantity)
    _validate_prices = field_validator("unit_price", "total_amount")(
        validate_non_negative
    )
    _validate_name = field_validator("product_name")(validate_required_str)
    _validate_unit = field_validator("unit")(validate_required_str)


class AICommand(BaseModel):
    intent: Intent
    items: list[AIItem] = []
    customer_name: str | None = None
    supplier_name: str | None = None
    title: str | None = None
    category: str | None = None
    notes: str | None = None
    date: datetime | None = None
    total_amount: Decimal | None = None

    _validate_text = field_validator(
        "customer_name",
        "supplier_name",
        "title",
        "category",
        "notes",
    )(validate_required_str)
    _validate_expense_amount = field_validator("total_amount")(validate_non_negative)

    def first_item(self) -> AIItem | None:
        return self.items[0] if self.items else None


class AICommandRequest(BaseModel):
    message: str
    conversation_id: str | None = None

    _validate_message = field_validator("message")(validate_required_str)

    @field_validator("message")
    @classmethod
    def _limit_length(cls, v: str) -> str:
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"Message is too long (maximum {MAX_MESSAGE_LENGTH} characters)"
            )
        return v


class AIProposalResponse(BaseModel):
    command: AICommand
    requires_confirmation: bool
    message: str
    disambiguation: list[ProductCandidate] | None = None
    issues: list[ItemIssue] | None = None


class AIExecuteRequest(BaseModel):
    command: AICommand
    idempotency_key: str | None = None


class AIResolveRequest(BaseModel):
    command: AICommand
    product_id: str


class AIExecuteResponse(BaseModel):
    message: str
    record: dict


__all__ = [
    "AI_COMMAND_SCHEMA",
    "AICommand",
    "AICommandRequest",
    "AIExecuteRequest",
    "AIExecuteResponse",
    "AIItem",
    "AIProposalResponse",
    "AIResolveRequest",
    "ItemIssue",
    "MAX_AMOUNT",
    "MAX_ITEMS",
    "MAX_MESSAGE_LENGTH",
    "MAX_QUANTITY",
    "ProductCandidate",
]