import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.product import Product
from app.models.user import User
from app.schemas.purchase import PurchaseCreate
from app.schemas.sale import SaleCreate
from app.services import purchase as purchase_service
from app.services import sale as sale_service


async def _make_user(db) -> User:
    user = User(
        email=f"user-{uuid.uuid4().hex[:8]}@cbo.local",
        password_hash="hash",
        name="Tester",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _make_product(db, stock: int = 100) -> Product:
    product = Product(
        name=f"Product-{uuid.uuid4().hex[:8]}",
        sku=f"SKU-{uuid.uuid4().hex[:8]}",
        category="Grains",
        unit="Pack",
        purchase_price=Decimal("100"),
        selling_price=Decimal("150"),
        stock_quantity=stock,
        minimum_stock=10,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def _product_stock(db, product_id) -> int:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one().stock_quantity


def _sale(product_id, quantity):
    return SaleCreate(
        product_id=product_id,
        quantity=quantity,
        unit_price=Decimal("150"),
        total_amount=Decimal("150") * quantity,
        sale_date=datetime.now(UTC),
    )


def _purchase(product_id, quantity):
    return PurchaseCreate(
        product_id=product_id,
        supplier_name="Supplier",
        quantity=quantity,
        purchase_price=Decimal("100"),
        total_amount=Decimal("100") * quantity,
        purchase_date=datetime.now(UTC),
    )


async def test_purchase_increases_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, stock=10)

    await purchase_service.create_purchase(db, _purchase(product.id, 5), user)

    assert await _product_stock(db, product.id) == 15


async def test_sale_decreases_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, stock=10)

    await sale_service.create_sale(db, _sale(product.id, 3), user)

    assert await _product_stock(db, product.id) == 7


async def test_sale_rejects_insufficient_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, stock=2)

    with pytest.raises(HTTPException) as exc:
        await sale_service.create_sale(db, _sale(product.id, 5), user)

    assert exc.value.status_code == 400
    assert await _product_stock(db, product.id) == 2


async def test_delete_sale_restores_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, stock=10)

    sale = await sale_service.create_sale(db, _sale(product.id, 4), user)
    assert await _product_stock(db, product.id) == 6

    await sale_service.delete_sale(db, sale["id"], user)

    assert await _product_stock(db, product.id) == 10


async def test_delete_purchase_reduces_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, stock=10)

    purchase = await purchase_service.create_purchase(db, _purchase(product.id, 6), user)
    assert await _product_stock(db, product.id) == 16

    await purchase_service.delete_purchase(db, purchase["id"], user)

    assert await _product_stock(db, product.id) == 10
