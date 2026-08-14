import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.customer import CustomerCreate
from app.schemas.expense import ExpenseCreate
from app.schemas.purchase import PurchaseCreate
from app.schemas.sale import SaleCreate


def _now():
    return datetime.now(UTC)


def _product_id():
    return uuid.uuid4()


def test_sale_accepts_valid_payload():
    sale = SaleCreate(
        items=[
            {
                "product_id": _product_id(),
                "quantity": 3,
                "unit_price": Decimal("100"),
                "total_amount": Decimal("300"),
            }
        ],
        sale_date=_now(),
    )
    assert sale.items[0].quantity == 3
    assert sale.items[0].total_amount == Decimal("300")


def test_sale_rejects_zero_quantity():
    with pytest.raises(ValidationError):
        SaleCreate(
            items=[
                {
                    "product_id": _product_id(),
                    "quantity": 0,
                    "unit_price": Decimal("100"),
                    "total_amount": Decimal("300"),
                }
            ],
            sale_date=_now(),
        )


def test_sale_rejects_negative_price():
    with pytest.raises(ValidationError):
        SaleCreate(
            items=[
                {
                    "product_id": _product_id(),
                    "quantity": 2,
                    "unit_price": Decimal("-1"),
                    "total_amount": Decimal("300"),
                }
            ],
            sale_date=_now(),
        )


def test_sale_rejects_empty_items():
    with pytest.raises(ValidationError):
        SaleCreate(items=[], sale_date=_now())


def test_purchase_rejects_blank_supplier():
    with pytest.raises(ValidationError):
        PurchaseCreate(
            supplier_name="   ",
            items=[
                {
                    "product_id": _product_id(),
                    "quantity": 5,
                    "purchase_price": Decimal("10"),
                    "total_amount": Decimal("50"),
                }
            ],
            purchase_date=_now(),
        )


def test_purchase_rejects_zero_quantity():
    with pytest.raises(ValidationError):
        PurchaseCreate(
            supplier_name="Supplier",
            items=[
                {
                    "product_id": _product_id(),
                    "quantity": 0,
                    "purchase_price": Decimal("10"),
                    "total_amount": Decimal("50"),
                }
            ],
            purchase_date=_now(),
        )


def test_expense_rejects_zero_amount():
    with pytest.raises(ValidationError):
        ExpenseCreate(
            title="Rent",
            category="Miscellaneous",
            amount=Decimal("0"),
            expense_date=_now(),
        )


def test_expense_rejects_blank_title():
    with pytest.raises(ValidationError):
        ExpenseCreate(
            title="",
            category="Miscellaneous",
            amount=Decimal("100"),
            expense_date=_now(),
        )


def test_customer_rejects_blank_name():
    with pytest.raises(ValidationError):
        CustomerCreate(name="", phone="+92 300 1234567")
