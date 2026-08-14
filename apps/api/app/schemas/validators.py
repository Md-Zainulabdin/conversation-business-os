from decimal import Decimal

MAX_QUANTITY = 1_000_000
MAX_AMOUNT = Decimal("9999999999.99")


def validate_quantity(v: int | None) -> int | None:
    if v is not None and (v <= 0 or v > MAX_QUANTITY):
        raise ValueError("quantity must be between 1 and 1000000")
    return v


def validate_non_negative(v: Decimal | None) -> Decimal | None:
    if v is not None and v < 0:
        raise ValueError("value must be greater than or equal to 0")
    if v is not None and v > MAX_AMOUNT:
        raise ValueError("value is too large")
    return v


def validate_positive_amount(v: Decimal | None) -> Decimal | None:
    if v is not None and v <= 0:
        raise ValueError("amount must be greater than 0")
    return v


def validate_required_str(v: str | None) -> str | None:
    if v is not None and not v.strip():
        raise ValueError("field cannot be empty")
    return v
