import json
import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.config import settings
from app.models.customer import Customer
from app.models.expense import Expense
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.sale import Sale
from app.models.user import User
from app.schemas.ai import AICommand
from app.services import ai as ai_service


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


class SequencedFakeClient:
    def __init__(self, contents: list[str | None]):
        self.contents = contents
        self.calls = 0

    async def _create(self, **kwargs):
        self.calls += 1
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.contents[self.calls - 1])
                )
            ]
        )

    @property
    def chat(self):
        return SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )


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


async def _make_product(db, name: str = "Coke", stock: int = 100) -> Product:
    product = Product(
        name=name,
        sku=f"SKU-{uuid.uuid4().hex[:8]}",
        category="Beverages",
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


async def _count(db, model) -> int:
    result = await db.execute(select(model))
    return len(list(result.scalars().all()))


async def test_propose_sale_returns_confirmation_without_writing(db):
    user = await _make_user(db)
    await _make_product(db, name="Coke", stock=100)

    client = _fake_client(
        {
            "intent": "sale",
            "product_name": "Coke",
            "quantity": 20,
            "unit_price": None,
            "total_amount": None,
            "customer_name": "Ali",
            "supplier_name": None,
            "title": None,
            "category": None,
            "notes": None,
            "date": None,
        }
    )
    proposal = await ai_service.propose(db, user, "Sold 20 Coke to Ali", client)

    assert proposal.requires_confirmation is True
    assert "Sale: 20 x Coke" in proposal.message
    assert "Rs 150.00" in proposal.message
    assert "Rs 3,000.00" in proposal.message
    assert await _count(db, Sale) == 0
    assert await _count(db, Customer) == 0


async def test_execute_sale_creates_sale_and_decreases_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, name="Coke", stock=100)

    command = AICommand(
        intent="sale", product_name="Coke", quantity=20
    )
    result = await ai_service.execute(db, user, command)

    assert await _count(db, Sale) == 1
    assert result.message.startswith("Sale recorded: 20 x Coke")
    product = (await db.execute(select(Product).where(Product.id == product.id))).scalar_one()
    assert product.stock_quantity == 80


async def test_execute_sale_auto_creates_customer(db):
    user = await _make_user(db)
    await _make_product(db, name="Coke", stock=50)

    command = AICommand(
        intent="sale", product_name="Coke", quantity=5, customer_name="Ali"
    )
    result = await ai_service.execute(db, user, command)

    assert await _count(db, Customer) == 1
    customer = (await db.execute(select(Customer))).scalar_one()
    assert customer.name == "Ali"
    assert customer.phone.startswith("ai-")
    assert "Ali" in result.message


async def test_execute_sale_reuses_existing_customer(db):
    user = await _make_user(db)
    await _make_product(db, name="Coke", stock=50)
    customer = Customer(
        name="Ali", phone="+92 300 1234567", user_id=user.id
    )
    db.add(customer)
    await db.commit()

    command = AICommand(
        intent="sale", product_name="Coke", quantity=5, customer_name="Ali"
    )
    await ai_service.execute(db, user, command)

    assert await _count(db, Customer) == 1


async def test_execute_purchase_increases_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, name="Rice", stock=10)

    command = AICommand(
        intent="purchase", product_name="Rice", quantity=30, supplier_name="Wholesaler"
    )
    result = await ai_service.execute(db, user, command)

    assert await _count(db, Purchase) == 1
    assert result.message.startswith("Purchase recorded: 30 x Rice")
    product = (await db.execute(select(Product).where(Product.id == product.id))).scalar_one()
    assert product.stock_quantity == 40


async def test_execute_expense_creates_expense(db):
    user = await _make_user(db)

    command = AICommand(
        intent="expense", title="Electricity bill", total_amount=Decimal("5000")
    )
    result = await ai_service.execute(db, user, command)

    assert await _count(db, Expense) == 1
    expense = (await db.execute(select(Expense))).scalar_one()
    assert expense.category == "Miscellaneous"
    assert "Electricity bill" in result.message


async def test_propose_inquiry_answers_without_confirmation(db):
    user = await _make_user(db)
    await _make_product(db, name="Coke", stock=120)

    client = _fake_client(
        {
            "intent": "inquiry",
            "product_name": "Coke",
            "quantity": None,
            "unit_price": None,
            "total_amount": None,
            "customer_name": None,
            "supplier_name": None,
            "title": None,
            "category": None,
            "notes": None,
            "date": None,
        }
    )
    proposal = await ai_service.propose(db, user, "How much Coke stock is left?", client)

    assert proposal.requires_confirmation is False
    assert "120 Pack" in proposal.message


async def test_execute_sale_rejects_insufficient_stock(db):
    user = await _make_user(db)
    await _make_product(db, name="Coke", stock=2)

    command = AICommand(
        intent="sale", product_name="Coke", quantity=5
    )
    with pytest.raises(HTTPException) as exc:
        await ai_service.execute(db, user, command)

    assert exc.value.status_code == 400
    assert await _count(db, Sale) == 0


async def test_propose_unknown_product_returns_404(db):
    user = await _make_user(db)
    await _make_product(db, name="Coke", stock=100)

    client = _fake_client(
        {
            "intent": "sale",
            "product_name": "Nonexistent",
            "quantity": 5,
            "unit_price": None,
            "total_amount": None,
            "customer_name": None,
            "supplier_name": None,
            "title": None,
            "category": None,
            "notes": None,
            "date": None,
        }
    )
    with pytest.raises(HTTPException) as exc:
        await ai_service.propose(db, user, "Sold 5 Nonexistent", client)

    assert exc.value.status_code == 404
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert "isn't in your catalog" in detail["title"]
    assert "Coke" in detail["options"]


async def test_propose_missing_groq_key_returns_503(monkeypatch, db):
    user = await _make_user(db)
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")

    with pytest.raises(HTTPException) as exc:
        await ai_service.propose(db, user, "Sold 5 Coke")

    assert exc.value.status_code == 503


async def test_propose_sale_ambiguous_returns_disambiguation(db):
    user = await _make_user(db)
    await _make_product(db, name="Super Basmati Rice 5kg", stock=100)
    await _make_product(db, name="Golden Basmati Rice 5kg", stock=50)

    client = _fake_client(
        {
            "intent": "sale",
            "product_name": "rice",
            "quantity": 20,
            "unit_price": None,
            "total_amount": None,
            "customer_name": None,
            "supplier_name": None,
            "title": None,
            "category": None,
            "notes": None,
            "date": None,
        }
    )
    proposal = await ai_service.propose(db, user, "Sold 20 packs of rice", client)

    assert proposal.requires_confirmation is False
    assert proposal.disambiguation is not None
    assert len(proposal.disambiguation) == 2
    names = {c.name for c in proposal.disambiguation}
    assert names == {"Golden Basmati Rice 5kg", "Super Basmati Rice 5kg"}
    assert proposal.command.product_id is None
    assert await _count(db, Sale) == 0


async def test_resolve_picks_product_and_returns_confirmation(db):
    user = await _make_user(db)
    golden = await _make_product(db, name="Golden Basmati Rice 5kg", stock=50)
    await _make_product(db, name="Super Basmati Rice 5kg", stock=100)

    command = AICommand(intent="sale", product_name="rice", quantity=20)
    proposal = await ai_service.resolve(db, user, command, str(golden.id))

    assert proposal.requires_confirmation is True
    assert "Golden Basmati Rice 5kg" in proposal.message
    assert proposal.command.product_id == str(golden.id)
    assert await _count(db, Sale) == 0


async def test_execute_sale_uses_chosen_product_id(db):
    user = await _make_user(db)
    golden = await _make_product(db, name="Golden Basmati Rice 5kg", stock=50)
    await _make_product(db, name="Super Basmati Rice 5kg", stock=100)

    command = AICommand(
        intent="sale",
        product_name="rice",
        product_id=str(golden.id),
        quantity=20,
    )
    result = await ai_service.execute(db, user, command)

    assert await _count(db, Sale) == 1
    sale = (await db.execute(select(Sale))).scalar_one()
    assert str(sale.product_id) == str(golden.id)
    assert result.message.startswith("Sale recorded: 20 x Golden Basmati Rice 5kg")
    refreshed = (
        await db.execute(select(Product).where(Product.id == golden.id))
    ).scalar_one()
    assert refreshed.stock_quantity == 30
    assert result.message.endswith("Stock left: 30 Pack.")


async def test_parse_retries_on_empty_generation_content(db):
    user = await _make_user(db)
    await _make_product(db, name="Coke", stock=100)

    command = {
        "intent": "sale",
        "product_name": "Coke",
        "quantity": 5,
        "unit_price": None,
        "total_amount": None,
        "customer_name": None,
        "supplier_name": None,
        "title": None,
        "category": None,
        "notes": None,
        "date": None,
    }
    client = SequencedFakeClient([None, json.dumps(command)])
    proposal = await ai_service.propose(db, user, "Sold 5 Coke", client)

    assert client.calls == 2
    assert proposal.requires_confirmation is True
    assert "Sale: 5 x Coke" in proposal.message
