import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.models.customer import Customer
from app.models.product import Product
from app.models.user import User
from app.schemas.customer import CustomerCreate
from app.schemas.product import ProductCreate
from app.schemas.purchase import PurchaseCreate, PurchaseItemCreate
from app.schemas.sale import SaleCreate, SaleItemCreate
from app.services import ai as ai_service
from app.services import customer as customer_service
from app.services import product as product_service
from app.services import purchase as purchase_service
from app.services import sale as sale_service
from app.services import stats as stats_service
from app.services.ai_session import ai_session_store, idempotency_store


class FakeGroqClient:
    def __init__(self, content: str):
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )
        self._content = content

    async def _create(self, **kwargs):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self._content)
                )
            ]
        )


def _fake_client(command: dict) -> FakeGroqClient:
    return FakeGroqClient(json.dumps(command))


@pytest.fixture(autouse=True)
def _groq_key(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")


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


async def _make_product(db, user: User, stock: int) -> Product:
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


def _inquiry_command(name: str) -> dict:
    return {
        "intent": "inquiry",
        "items": [{"product_name": name}],
        "customer_name": None,
        "supplier_name": None,
        "title": None,
        "category": None,
        "notes": None,
        "date": None,
        "total_amount": None,
    }


async def test_inquiry_only_sees_own_business_stock(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)
    product_a = await _make_product(db, user_a, stock=100)
    await _make_product(db, user_b, stock=500)

    inquiry = await ai_service.propose(
        db,
        user_a,
        "How much stock do I have?",
        _fake_client(_inquiry_command(product_a.name)),
    )

    assert f"{product_a.name}: 100 Pack in stock" in inquiry.message
    assert "500" not in inquiry.message


async def test_list_products_is_scoped_per_user(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)
    product_a = await _make_product(db, user_a, stock=100)
    product_b = await _make_product(db, user_b, stock=100)

    list_a = await product_service.list_products(db, user_a)
    list_b = await product_service.list_products(db, user_b)

    assert [p.id for p in list_a] == [product_a.id]
    assert [p.id for p in list_b] == [product_b.id]


async def test_get_product_denies_other_users_product(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)
    product_a = await _make_product(db, user_a, stock=100)

    with pytest.raises(HTTPException) as exc:
        await product_service.get_product(db, product_a.id, user_b)
    assert exc.value.status_code == 404


async def test_stats_stock_is_scoped_per_user(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)
    await _make_product(db, user_a, stock=100)
    await _make_product(db, user_b, stock=500)

    overview_a = await stats_service.get_overview(db, user_a)
    overview_b = await stats_service.get_overview(db, user_b)

    assert overview_a["stock_items"] == 100
    assert overview_b["stock_items"] == 500


async def test_sale_cannot_reference_other_users_product(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)
    product_a = await _make_product(db, user_a, stock=100)

    data = SaleCreate(
        items=[
            SaleItemCreate(
                product_id=product_a.id,
                quantity=5,
                unit_price=Decimal("150"),
                total_amount=Decimal("750"),
            )
        ],
        sale_date=datetime.now(UTC),
    )
    with pytest.raises(HTTPException) as exc:
        await sale_service.create_sale(db, data, user_b)
    assert exc.value.status_code == 404


async def test_purchase_cannot_reference_other_users_product(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)
    product_a = await _make_product(db, user_a, stock=100)

    data = PurchaseCreate(
        supplier_name="Supplier",
        items=[
            PurchaseItemCreate(
                product_id=product_a.id,
                quantity=5,
                purchase_price=Decimal("100"),
                total_amount=Decimal("500"),
            )
        ],
        purchase_date=datetime.now(UTC),
    )
    with pytest.raises(HTTPException) as exc:
        await purchase_service.create_purchase(db, data, user_b)
    assert exc.value.status_code == 404


async def test_same_sku_allowed_for_different_users(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)

    await product_service.create_product(
        db, ProductCreate(name="Rice", sku="SKU-1", category="Grains", unit="Pack"), user_a
    )
    await product_service.create_product(
        db, ProductCreate(name="Rice", sku="SKU-1", category="Grains", unit="Pack"), user_b
    )


async def test_same_sku_denied_for_same_user(db):
    user = await _make_user(db)
    await product_service.create_product(
        db, ProductCreate(name="Rice", sku="SKU-1", category="Grains", unit="Pack"), user
    )
    with pytest.raises(HTTPException) as exc:
        await product_service.create_product(
            db, ProductCreate(name="Rice", sku="SKU-1", category="Grains", unit="Pack"), user
        )
    assert exc.value.status_code == 409


async def test_same_phone_allowed_for_different_users(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)

    await customer_service.create_customer(
        db, CustomerCreate(name="Ali", phone="+92 300 1234567"), user_a
    )
    await customer_service.create_customer(
        db, CustomerCreate(name="Ali", phone="+92 300 1234567"), user_b
    )


async def test_same_phone_denied_for_same_user(db):
    user = await _make_user(db)
    await customer_service.create_customer(
        db, CustomerCreate(name="Ali", phone="+92 300 1234567"), user
    )
    with pytest.raises(HTTPException) as exc:
        await customer_service.create_customer(
            db, CustomerCreate(name="Ali", phone="+92 300 1234567"), user
        )
    assert exc.value.status_code == 409


async def test_sale_cannot_reference_other_users_customer(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)
    product = await _make_product(db, user_b, stock=100)
    customer_a = Customer(
        user_id=user_a.id,
        name="Ali",
        phone=f"+92 300 {uuid.uuid4().hex[:7]}",
    )
    db.add(customer_a)
    await db.commit()
    await db.refresh(customer_a)

    data = SaleCreate(
        customer_id=customer_a.id,
        items=[
            SaleItemCreate(
                product_id=product.id,
                quantity=5,
                unit_price=Decimal("150"),
                total_amount=Decimal("750"),
            )
        ],
        sale_date=datetime.now(UTC),
    )
    with pytest.raises(HTTPException) as exc:
        await sale_service.create_sale(db, data, user_b)
    assert exc.value.status_code == 404


async def test_sessions_are_scoped_per_user(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)

    ai_session_store.push(f"{user_a.id}:conv", "user", "secret of user A")
    history_b = ai_session_store.get_history(f"{user_b.id}:conv")

    assert history_b == []
    assert len(ai_session_store.get_history(f"{user_a.id}:conv")) == 1
    ai_session_store._sessions.clear()


async def test_idempotency_is_scoped_per_user(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)

    response_a = ai_service.AIExecuteResponse(message="recorded A", record={})
    idempotency_store.set(f"{user_a.id}:key", response_a)

    assert idempotency_store.get(f"{user_b.id}:key") is None
    assert idempotency_store.get(f"{user_a.id}:key") == response_a
    idempotency_store._results.clear()