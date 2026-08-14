import json
import uuid
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.config import settings
from app.models.customer import Customer
from app.models.product import Product
from app.models.purchase import Purchase, PurchaseItem
from app.models.sale import Sale, SaleItem
from app.models.user import User
from app.schemas.ai import AICommand, AIItem
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


async def _make_product(
    db, user: User, name: str = "Coke", stock: int = 100
) -> Product:
    product = Product(
        user_id=user.id,
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


def _base_command(intent: str) -> dict:
    return {
        "intent": intent,
        "items": [],
        "customer_name": None,
        "supplier_name": None,
        "title": None,
        "category": None,
        "notes": None,
        "date": None,
    }


async def test_propose_sale_returns_confirmation_without_writing(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=100)

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "Coke",
            "quantity": 20,
            "unit_price": None,
            "total_amount": None,
        }
    ]
    command["customer_name"] = "Ali"
    proposal = await ai_service.propose(
        db, user, "Sold 20 Coke to Ali", _fake_client(command)
    )

    assert proposal.requires_confirmation is True
    assert "Sale: 20 x Coke" in proposal.message
    assert "Rs 150.00" in proposal.message
    assert "Rs 3,000.00" in proposal.message
    assert proposal.command.items[0].product_id is not None
    assert await _count(db, Sale) == 0
    assert await _count(db, Customer) == 0


async def test_propose_multi_product_sale_lists_all_items(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=100)
    await _make_product(db, user, name="Rice", stock=100)

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "Coke",
            "quantity": 20,
            "unit_price": None,
            "total_amount": None,
        },
        {
            "product_name": "Rice",
            "quantity": 10,
            "unit_price": None,
            "total_amount": None,
        },
    ]
    proposal = await ai_service.propose(
        db, user, "sold 20 Coke and 10 Rice", _fake_client(command)
    )

    assert proposal.requires_confirmation is True
    assert "20 x Coke" in proposal.message
    assert "10 x Rice" in proposal.message
    assert "Total: Rs" in proposal.message
    assert len(proposal.command.items) == 2
    assert all(item.product_id for item in proposal.command.items)
    assert await _count(db, Sale) == 0


async def test_execute_multi_product_sale_creates_items_and_decreases_stock(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=100)
    await _make_product(db, user, name="Rice", stock=100)

    command = AICommand(
        intent="sale",
        items=[
            AIItem(product_name="Coke", quantity=20),
            AIItem(product_name="Rice", quantity=10),
        ],
    )
    result = await ai_service.execute(db, user, command)

    assert await _count(db, Sale) == 1
    assert await _count(db, SaleItem) == 2
    assert "20 x Coke" in result.message
    assert "10 x Rice" in result.message

    sale = (await db.execute(select(Sale))).scalar_one()
    assert sale.total_amount == Decimal("4500.00")

    stock = {
        p.name: p.stock_quantity
        for p in (await db.execute(select(Product))).scalars().all()
    }
    assert stock["Coke"] == 80
    assert stock["Rice"] == 90


async def test_propose_multi_sale_partial_when_one_product_unknown(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=100)

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "Coke",
            "quantity": 20,
            "unit_price": None,
            "total_amount": None,
        },
        {
            "product_name": "Notebooks",
            "quantity": 5,
            "unit_price": None,
            "total_amount": None,
        },
    ]
    proposal = await ai_service.propose(
        db, user, "sold 20 Coke and 5 Notebooks", _fake_client(command)
    )

    assert proposal.requires_confirmation is True
    assert "Coke" in proposal.message
    assert proposal.issues is not None
    assert proposal.issues[0].kind == "not_found"
    assert proposal.issues[0].name == "Notebooks"
    assert len(proposal.command.items) == 1
    assert proposal.command.items[0].product_name == "Coke"
    assert await _count(db, Sale) == 0


async def test_propose_multi_sale_errors_when_one_unavailable_stock(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=100)
    await _make_product(db, user, name="Rice", stock=2)

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "Coke",
            "quantity": 20,
            "unit_price": None,
            "total_amount": None,
        },
        {
            "product_name": "Rice",
            "quantity": 5,
            "unit_price": None,
            "total_amount": None,
        },
    ]
    with pytest.raises(HTTPException) as exc:
        await ai_service.propose(
            db, user, "sold 20 Coke and 5 Rice", _fake_client(command)
        )

    assert exc.value.status_code == 400
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert "Rice" in detail["title"]
    assert await _count(db, Sale) == 0


async def test_execute_multi_purchase_increases_stock(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=100)
    await _make_product(db, user, name="Rice", stock=50)

    command = AICommand(
        intent="purchase",
        items=[
            AIItem(product_name="Coke", quantity=20),
            AIItem(product_name="Rice", quantity=30),
        ],
        supplier_name="Wholesaler",
    )
    result = await ai_service.execute(db, user, command)

    assert await _count(db, Purchase) == 1
    assert await _count(db, PurchaseItem) == 2
    assert "20 x Coke" in result.message
    assert "30 x Rice" in result.message

    stock = {
        p.name: p.stock_quantity
        for p in (await db.execute(select(Product))).scalars().all()
    }
    assert stock["Coke"] == 120
    assert stock["Rice"] == 80


async def test_execute_sale_creates_sale_and_decreases_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, user, name="Coke", stock=100)

    command = AICommand(
        intent="sale", items=[AIItem(product_name="Coke", quantity=20)]
    )
    result = await ai_service.execute(db, user, command)

    assert await _count(db, Sale) == 1
    assert result.message.startswith("Sale recorded: 20 x Coke")
    product = (await db.execute(select(Product).where(Product.id == product.id))).scalar_one()
    assert product.stock_quantity == 80


async def test_execute_purchase_increases_stock(db):
    user = await _make_user(db)
    product = await _make_product(db, user, name="Rice", stock=10)

    command = AICommand(
        intent="purchase",
        items=[AIItem(product_name="Rice", quantity=30)],
        supplier_name="Wholesaler",
    )
    result = await ai_service.execute(db, user, command)

    assert await _count(db, Purchase) == 1
    assert result.message.startswith("Purchase recorded: 30 x Rice")
    product = (await db.execute(select(Product).where(Product.id == product.id))).scalar_one()
    assert product.stock_quantity == 40


async def test_execute_sale_rejects_insufficient_stock(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=2)

    command = AICommand(
        intent="sale", items=[AIItem(product_name="Coke", quantity=5)]
    )
    with pytest.raises(HTTPException) as exc:
        await ai_service.execute(db, user, command)

    assert exc.value.status_code == 400
    assert await _count(db, Sale) == 0


async def test_propose_unknown_product_blocks_without_writing(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=100)

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "Nonexistent",
            "quantity": 5,
            "unit_price": None,
            "total_amount": None,
        }
    ]
    proposal = await ai_service.propose(
        db, user, "Sold 5 Nonexistent", _fake_client(command)
    )

    assert proposal.requires_confirmation is False
    assert "isn't in your product catalog" in proposal.message
    assert proposal.issues[0].kind == "not_found"
    assert await _count(db, Sale) == 0


async def test_propose_sale_ambiguous_returns_disambiguation(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Super Basmati Rice 5kg", stock=100)
    await _make_product(db, user, name="Golden Basmati Rice 5kg", stock=50)

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "rice",
            "quantity": 20,
            "unit_price": None,
            "total_amount": None,
        }
    ]
    proposal = await ai_service.propose(
        db, user, "Sold 20 packs of rice", _fake_client(command)
    )

    assert proposal.requires_confirmation is False
    assert proposal.disambiguation is not None
    assert len(proposal.disambiguation) == 2
    names = {c.name for c in proposal.disambiguation}
    assert names == {"Golden Basmati Rice 5kg", "Super Basmati Rice 5kg"}
    assert proposal.command.items[0].product_id is None
    assert await _count(db, Sale) == 0


async def test_propose_sale_ambiguous_pack_of_rice_asks_which_rice(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coca Cola 1.5L Bottle", stock=100)
    await _make_product(db, user, name="Super Basmati Rice 5kg", stock=100)
    await _make_product(db, user, name="Golden Basmati Rice 5kg", stock=50)

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "coke",
            "quantity": 10,
            "unit_price": None,
            "total_amount": None,
        },
        {
            "product_name": "pack of rice",
            "quantity": 20,
            "unit_price": None,
            "total_amount": None,
        },
        {
            "product_name": "sting",
            "quantity": 3,
            "unit_price": None,
            "total_amount": None,
        },
    ]
    proposal = await ai_service.propose(
        db,
        user,
        "bought 10 coke and 20 pack of rice and 3 sting",
        _fake_client(command),
    )

    assert proposal.requires_confirmation is False
    assert proposal.disambiguation is not None
    assert len(proposal.disambiguation) == 2
    names = {c.name for c in proposal.disambiguation}
    assert names == {"Golden Basmati Rice 5kg", "Super Basmati Rice 5kg"}
    assert "pack of rice" in proposal.message.lower()
    assert "which one did you mean" in proposal.message.lower()
    assert await _count(db, Sale) == 0



    user = await _make_user(db)
    golden = await _make_product(db, user, name="Golden Basmati Rice 5kg", stock=50)
    await _make_product(db, user, name="Super Basmati Rice 5kg", stock=100)

    command = AICommand(
        intent="sale", items=[AIItem(product_name="rice", quantity=20)]
    )
    proposal = await ai_service.resolve(db, user, command, str(golden.id))

    assert proposal.requires_confirmation is True
    assert "Golden Basmati Rice 5kg" in proposal.message
    assert proposal.command.items[0].product_id == str(golden.id)
    assert await _count(db, Sale) == 0


async def test_resolve_multi_product_applies_selection_to_ambiguous_item(db):
    user = await _make_user(db)
    golden = await _make_product(db, user, name="Golden Basmati Rice 5kg", stock=50)
    await _make_product(db, user, name="Super Basmati Rice 5kg", stock=100)
    await _make_product(db, user, name="Coke", stock=100)

    command = AICommand(
        intent="sale",
        items=[
            AIItem(product_name="Coke", quantity=10),
            AIItem(product_name="rice", quantity=20),
        ],
    )
    proposal = await ai_service.resolve(db, user, command, str(golden.id))

    assert proposal.requires_confirmation is True
    assert proposal.command.items[0].product_id is not None
    assert proposal.command.items[1].product_id == str(golden.id)
    assert "Coke" in proposal.message
    assert "Golden Basmati Rice 5kg" in proposal.message


async def test_execute_sale_uses_chosen_product_id(db):
    user = await _make_user(db)
    golden = await _make_product(db, user, name="Golden Basmati Rice 5kg", stock=50)
    await _make_product(db, user, name="Super Basmati Rice 5kg", stock=100)

    command = AICommand(
        intent="sale",
        items=[AIItem(product_name="rice", quantity=20, product_id=str(golden.id))],
    )
    result = await ai_service.execute(db, user, command)

    assert await _count(db, Sale) == 1
    sale = (await db.execute(select(Sale))).scalar_one()
    assert str(sale.items[0].product_id) == str(golden.id)
    assert result.message.startswith("Sale recorded: 20 x Golden Basmati Rice 5kg")
    refreshed = (
        await db.execute(select(Product).where(Product.id == golden.id))
    ).scalar_one()
    assert refreshed.stock_quantity == 30
    assert result.message.endswith("Stock left: 30 Pack.")


async def test_parse_retries_on_empty_generation_content(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=100)

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "Coke",
            "quantity": 5,
            "unit_price": None,
            "total_amount": None,
        }
    ]
    client = SequencedFakeClient([None, json.dumps(command)])
    proposal = await ai_service.propose(db, user, "Sold 5 Coke", client)

    assert client.calls == 2
    assert proposal.requires_confirmation is True
    assert "Sale: 5 x Coke" in proposal.message


async def test_propose_inquiry_answers_without_confirmation(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=120)

    command = _base_command("inquiry")
    command["items"] = [
        {
            "product_name": "Coke",
            "quantity": None,
            "unit_price": None,
            "total_amount": None,
        }
    ]
    proposal = await ai_service.propose(
        db, user, "How much Coke stock is left?", _fake_client(command)
    )

    assert proposal.requires_confirmation is False
    assert "120 Pack" in proposal.message