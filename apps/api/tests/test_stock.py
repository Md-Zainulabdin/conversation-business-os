import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.product import Product
from app.models.purchase import PurchaseItem
from app.models.sale import SaleItem
from app.models.user import User
from app.schemas.purchase import PurchaseCreate, PurchaseItemCreate
from app.schemas.sale import SaleCreate, SaleItemCreate
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


async def _make_product(db, user: User, stock: int = 100) -> Product:
    product = Product(
        user_id=user.id,
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
        items=[
            SaleItemCreate(
                product_id=product_id,
                quantity=quantity,
                unit_price=Decimal("150"),
                total_amount=Decimal("150") * quantity,
            )
        ],
        sale_date=datetime.now(UTC),
    )


def _multi_sale(*pairs):
    return SaleCreate(
        items=[
            SaleItemCreate(
                product_id=product_id,
                quantity=quantity,
                unit_price=Decimal("150"),
                total_amount=Decimal("150") * quantity,
            )
            for product_id, quantity in pairs
        ],
        sale_date=datetime.now(UTC),
    )


def _purchase(product_id, quantity):
    return PurchaseCreate(
        supplier_name="Supplier",
        items=[
            PurchaseItemCreate(
                product_id=product_id,
                quantity=quantity,
                purchase_price=Decimal("100"),
                total_amount=Decimal("100") * quantity,
            )
        ],
        purchase_date=datetime.now(UTC),
    )


def _multi_purchase(*pairs):
    return PurchaseCreate(
        supplier_name="Supplier",
        items=[
            PurchaseItemCreate(
                product_id=product_id,
                quantity=quantity,
                purchase_price=Decimal("100"),
                total_amount=Decimal("100") * quantity,
            )
            for product_id, quantity in pairs
        ],
        purchase_date=datetime.now(UTC),
    )


async def test_purchase_increases_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, user, stock=10)

    await purchase_service.create_purchase(db, _purchase(product.id, 5), user)

    assert await _product_stock(db, product.id) == 15


async def test_sale_decreases_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, user, stock=10)

    await sale_service.create_sale(db, _sale(product.id, 3), user)

    assert await _product_stock(db, product.id) == 7


async def test_multi_everything(db):
    user = await _make_user(db)
    product_a = await _make_product(db, user, stock=100)
    product_b = await _make_product(db, user, stock=100)
    product_c = await _make_product(db, user, stock=100)

    sale = await sale_service.create_sale(
        db, _multi_sale((product_a.id, 10), (product_b.id, 5)), user
    )
    assert sale["total_amount"] == Decimal("2250.00")
    assert len(sale["items"]) == 2
    assert await _product_stock(db, product_a.id) == 90
    assert await _product_stock(db, product_b.id) == 95

    purchase = await purchase_service.create_purchase(
        db, _multi_purchase((product_b.id, 20), (product_c.id, 15)), user
    )
    assert purchase["total_amount"] == Decimal("3500.00")
    assert len(purchase["items"]) == 2
    assert await _product_stock(db, product_b.id) == 115
    assert await _product_stock(db, product_c.id) == 115

    rows = await db.execute(select(SaleItem))
    assert len(list(rows.scalars().all())) == 2
    rows = await db.execute(select(PurchaseItem))
    assert len(list(rows.scalars().all())) == 2


async def test_sale_rejects_insufficient_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, user, stock=2)

    with pytest.raises(HTTPException) as exc:
        await sale_service.create_sale(db, _sale(product.id, 5), user)

    assert exc.value.status_code == 400
    assert await _product_stock(db, product.id) == 2


async def test_sale_rejects_when_one_of_many_short(db):
    user = await _make_user(db)
    product_a = await _make_product(db, user, stock=100)
    product_b = await _make_product(db, user, stock=2)

    with pytest.raises(HTTPException) as exc:
        await sale_service.create_sale(
            db, _multi_sale((product_a.id, 10), (product_b.id, 5)), user
        )

    assert exc.value.status_code == 400
    assert await _product_stock(db, product_a.id) == 100
    assert await _product_stock(db, product_b.id) == 2


async def test_update_sale_replaces_items_and_adjusts_stock(db):
    user = await _make_user(db)
    product_a = await _make_product(db, user, stock=100)
    product_b = await _make_product(db, user, stock=100)
    product_c = await _make_product(db, user, stock=100)

    sale = await sale_service.create_sale(
        db, _multi_sale((product_a.id, 10), (product_b.id, 5)), user
    )
    assert await _product_stock(db, product_a.id) == 90

    from app.schemas.sale import SaleUpdate

    update = SaleUpdate(
        items=[
            {
                "product_id": product_c.id,
                "quantity": 7,
                "unit_price": Decimal("150"),
                "total_amount": Decimal("1050"),
            },
            {
                "product_id": product_a.id,
                "quantity": 3,
                "unit_price": Decimal("150"),
                "total_amount": Decimal("450"),
            },
        ],
        notes="changed",
    )
    await sale_service.update_sale(db, sale["id"], update, user)

    assert await _product_stock(db, product_a.id) == 97
    assert await _product_stock(db, product_b.id) == 100
    assert await _product_stock(db, product_c.id) == 93

    refreshed = await sale_service.get_sale(db, sale["id"], user)
    assert refreshed["total_amount"] == Decimal("1500.00")
    assert {item["product_id"] for item in refreshed["items"]} == {
        product_a.id,
        product_c.id,
    }


async def test_delete_sale_restores_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, user, stock=10)

    sale = await sale_service.create_sale(db, _sale(product.id, 4), user)
    assert await _product_stock(db, product.id) == 6

    await sale_service.delete_sale(db, sale["id"], user)

    assert await _product_stock(db, product.id) == 10


async def test_delete_multi_sale_restores_all_stock(db):
    user = await _make_user(db)
    product_a = await _make_product(db, user, stock=100)
    product_b = await _make_product(db, user, stock=100)

    sale = await sale_service.create_sale(
        db, _multi_sale((product_a.id, 10), (product_b.id, 5)), user
    )
    await sale_service.delete_sale(db, sale["id"], user)

    assert await _product_stock(db, product_a.id) == 100
    assert await _product_stock(db, product_b.id) == 100


async def test_delete_purchase_reduces_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, user, stock=10)

    purchase = await purchase_service.create_purchase(db, _purchase(product.id, 6), user)
    assert await _product_stock(db, product.id) == 16

    await purchase_service.delete_purchase(db, purchase["id"], user)

    assert await _product_stock(db, product.id) == 10