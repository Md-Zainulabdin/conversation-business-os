import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select

from app.core.config import settings
from app.models.customer import Customer
from app.models.expense import Expense
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.sale import Sale
from app.models.user import User
from app.schemas.ai import MAX_AMOUNT, MAX_QUANTITY, AICommand, AIItem
from app.services import ai as ai_service
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


class CapturingClient:
    def __init__(self, content: str):
        self.content = content
        self.calls: list[dict] = []

    async def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content)
                )
            ]
        )

    @property
    def chat(self):
        return SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )


def _fake_client(command: dict) -> FakeGroqClient:
    return FakeGroqClient(json.dumps(command))


@pytest.fixture(autouse=True)
def _groq_key(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key")


@pytest.fixture(autouse=True)
def _reset_stores():
    ai_session_store._sessions.clear()
    idempotency_store._results.clear()
    yield


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
    db, user: User, name: str = "Coke", stock: int = 100, unit: str = "Pack",
    selling_price: str = "150",
) -> Product:
    product = Product(
        user_id=user.id,
        name=name,
        sku=f"SKU-{uuid.uuid4().hex[:8]}",
        category="Beverages",
        unit=unit,
        purchase_price=Decimal("100"),
        selling_price=Decimal(selling_price),
        stock_quantity=stock,
        minimum_stock=10,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def _make_customer(db, user: User, name: str) -> Customer:
    customer = Customer(
        name=name,
        phone=f"+92-{uuid.uuid4().hex[:9]}",
        user_id=user.id,
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


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
        "total_amount": None,
    }


async def _product_stock(db, product_id) -> int:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one().stock_quantity


# --- Partial success (spec 3, 4, 5) ---------------------------------------


async def test_propose_partial_sale_lists_found_and_not_found(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100)

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "Rice",
            "quantity": 10,
            "unit_price": None,
            "total_amount": None,
        },
        {
            "product_name": "Sprite",
            "quantity": 20,
            "unit_price": None,
            "total_amount": None,
        },
    ]
    proposal = await ai_service.propose(
        db, user, "Sold 10 packs of Rice and 20 bottles of Sprite", _fake_client(command)
    )

    assert proposal.requires_confirmation is True
    assert "I can record:" in proposal.message
    assert "10 x Rice" in proposal.message
    assert "I can't record:" in proposal.message
    assert "Sprite" in proposal.message
    assert proposal.issues is not None
    assert [(i.kind, i.name) for i in proposal.issues] == [("not_found", "Sprite")]
    assert len(proposal.command.items) == 1
    assert proposal.command.items[0].product_name == "Rice"
    assert await _count(db, Sale) == 0
    sprite = await db.execute(select(Product).where(Product.name == "Sprite"))
    assert sprite.scalar_one_or_none() is None


async def test_execute_partial_sale_records_only_valid_item(db):
    user = await _make_user(db)
    rice = await _make_product(db, user, name="Rice", stock=100)

    command = AICommand(
        intent="sale", items=[AIItem(product_name="Rice", quantity=10)]
    )
    proposal = await ai_service.propose(
        db, user, "Sold 10 Rice and 20 Sprite", _fake_client(
            {
                **command.model_dump(),
                "items": [
                    {"product_name": "Rice", "quantity": 10},
                    {"product_name": "Sprite", "quantity": 20},
                ],
            }
        )
    )
    result = await ai_service.execute(db, user, proposal.command)

    assert await _count(db, Sale) == 1
    sale = (await db.execute(select(Sale))).scalar_one()
    assert len(sale.items) == 1
    assert sale.items[0].product_id == rice.id
    assert await _product_stock(db, rice.id) == 90
    assert "10 x Rice" in result.message
    products = await db.execute(select(Product))
    assert len(list(products.scalars().all())) == 1


async def test_propose_all_unknown_products_blocks(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100)

    command = _base_command("sale")
    command["items"] = [
        {"product_name": "Sprite", "quantity": 10, "unit_price": None, "total_amount": None},
        {"product_name": "Fanta", "quantity": 5, "unit_price": None, "total_amount": None},
    ]
    proposal = await ai_service.propose(
        db, user, "Sold 10 Sprite and 5 Fanta", _fake_client(command)
    )

    assert proposal.requires_confirmation is False
    assert proposal.command.items == []
    assert "Sprite" in proposal.message and "Fanta" in proposal.message
    assert len(proposal.issues) == 2
    assert await _count(db, Sale) == 0


async def test_execute_of_blocked_command_is_rejected(db):
    user = await _make_user(db)
    command = AICommand(intent="sale", items=[])
    with pytest.raises(HTTPException) as exc:
        await ai_service.execute(db, user, command)
    assert exc.value.status_code == 400
    assert await _count(db, Sale) == 0


# --- Customer safety (spec 21, 22, 23) -------------------------------------


async def test_unknown_customer_not_auto_created(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100)

    command = AICommand(
        intent="sale",
        items=[AIItem(product_name="Rice", quantity=5)],
        customer_name="Ahmed",
    )
    result = await ai_service.execute(db, user, command)

    sale = (await db.execute(select(Sale))).scalar_one()
    assert sale.customer_id is None
    assert await _count(db, Customer) == 0
    assert "walk-in sale" in result.message


async def test_propose_unknown_customer_reports_as_walk_in(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100)

    command = _base_command("sale")
    command["items"] = [{"product_name": "Rice", "quantity": 10}]
    command["customer_name"] = "Ahmed"
    proposal = await ai_service.propose(
        db, user, "Sold 10 Rice to Ahmed", _fake_client(command)
    )

    assert proposal.requires_confirmation is True
    assert "Ahmed isn't in your customer list" in proposal.message
    assert await _count(db, Customer) == 0


async def test_ambiguous_customer_raises_with_options(db):
    user = await _make_user(db)
    await _make_customer(db, user, "Ali Khan")
    await _make_customer(db, user, "Ali Ahmed")
    await _make_customer(db, user, "Ali Raza")
    await _make_product(db, user, name="Rice", stock=100)

    command = _base_command("sale")
    command["items"] = [{"product_name": "Rice", "quantity": 5}]
    command["customer_name"] = "Ali"
    with pytest.raises(HTTPException) as exc:
        await ai_service.propose(
            db, user, "Sold 5 Rice to Ali", _fake_client(command)
        )

    assert exc.value.status_code == 400
    options = exc.value.detail["options"]
    assert set(options) == {"Ali Khan", "Ali Ahmed", "Ali Raza"}


async def test_walk_in_sale_allowed(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100)

    result = await ai_service.execute(
        db,
        user,
        AICommand(intent="sale", items=[AIItem(product_name="Rice", quantity=3)]),
    )

    sale = (await db.execute(select(Sale))).scalar_one()
    assert sale.customer_id is None
    assert "Walk-in customer" in result.message


# --- Validation (spec 10, 11, 20, 51, 53) ---------------------------------


async def test_unit_mismatch_is_an_item_issue(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100, unit="kg")

    command = _base_command("sale")
    command["items"] = [
        {"product_name": "Rice", "quantity": 10, "unit": "bottles", "unit_price": None, "total_amount": None}
    ]
    proposal = await ai_service.propose(
        db, user, "Sold 10 bottles of Rice", _fake_client(command)
    )

    assert proposal.requires_confirmation is False
    assert proposal.issues[0].kind == "invalid_unit"
    assert "sold by kg, not bottles" in proposal.message


async def test_unit_plural_matches_singular_unit(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Super Basmati Rice 5kg", stock=100, unit="Pack")

    command = _base_command("sale")
    command["items"] = [
        {"product_name": "Super Basmati Rice 5kg", "quantity": 10, "unit": "packs", "unit_price": None, "total_amount": None}
    ]
    proposal = await ai_service.propose(
        db, user, "Sold 10 packs of Rice", _fake_client(command)
    )

    assert proposal.requires_confirmation is True
    assert proposal.issues is None
    assert "10 x Super Basmati Rice 5kg" in proposal.message
    assert len(proposal.command.items) == 1
    assert proposal.command.items[0].product_id is not None
    assert await _count(db, Sale) == 0


async def test_missing_quantity_is_an_item_issue(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100)

    command = _base_command("sale")
    command["items"] = [{"product_name": "Rice", "quantity": None}]
    proposal = await ai_service.propose(
        db, user, "Sold Rice", _fake_client(command)
    )

    assert proposal.requires_confirmation is False
    assert proposal.issues[0].kind == "invalid_quantity"
    assert "I need a quantity" in proposal.message
    assert await _count(db, Sale) == 0


@pytest.mark.parametrize("quantity", [0, -5, MAX_QUANTITY + 1])
def test_invalid_and_huge_quantities_rejected(quantity):
    with pytest.raises(ValidationError):
        AIItem(product_name="Rice", quantity=quantity)


def test_huge_amount_rejected():
    with pytest.raises(ValidationError):
        AICommand(intent="expense", total_amount=MAX_AMOUNT + Decimal("1"))


def test_fractional_quantity_not_allowed():
    with pytest.raises(ValidationError):
        AIItem(product_name="Rice", quantity=2.5)


async def test_stock_shortfall_is_hard_failure(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=15, unit="kg")

    command = AICommand(
        intent="sale", items=[AIItem(product_name="Rice", quantity=20)]
    )
    with pytest.raises(HTTPException) as exc:
        await ai_service.execute(db, user, command)

    assert exc.value.status_code == 400
    assert await _count(db, Sale) == 0
    product = (await db.execute(select(Product).where(Product.name == "Rice"))).scalar_one()
    assert product.stock_quantity == 15


async def test_stock_exact_match_allows_zero(db):
    user = await _make_user(db)
    product = await _make_product(db, user, name="Rice", stock=20)

    await ai_service.execute(
        db,
        user,
        AICommand(intent="sale", items=[AIItem(product_name="Rice", quantity=20)]),
    )

    assert await _product_stock(db, product.id) == 0


async def test_duplicate_product_lines_record_once(db):
    user = await _make_user(db)
    product = await _make_product(db, user, name="Rice", stock=100)

    result = await ai_service.execute(
        db,
        user,
        AICommand(
            intent="sale",
            items=[
                AIItem(product_name="Rice", quantity=5),
                AIItem(product_name="Rice", quantity=3),
            ],
        ),
    )

    assert await _count(db, Sale) == 1
    sale = (await db.execute(select(Sale))).scalar_one()
    assert len(sale.items) == 2
    assert sale.total_amount == Decimal(
        f"{(5 + 3) * 150}.00"
    )
    assert await _product_stock(db, product.id) == 92
    assert "8 x Rice" not in result.message


async def test_price_deviation_is_surfaced_not_silent(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100, selling_price="200")

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "Rice",
            "quantity": 10,
            "unit_price": 500,
            "total_amount": None,
        }
    ]
    proposal = await ai_service.propose(
        db, user, "Sold 10 Rice for 500", _fake_client(command)
    )

    assert "(catalog Rs 200.00)" in proposal.message


async def test_future_date_rejected(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100)

    tomorrow = datetime.now(UTC) + timedelta(days=1)
    command = AICommand(
        intent="sale",
        items=[AIItem(product_name="Rice", quantity=5)],
        date=tomorrow,
    )
    with pytest.raises(HTTPException) as exc:
        await ai_service.execute(db, user, command)

    assert exc.value.status_code == 400
    assert await _count(db, Sale) == 0


# --- Expense (spec 26, 27) -------------------------------------------------


async def test_expense_recorded(db):
    user = await _make_user(db)

    result = await ai_service.execute(
        db,
        user,
        AICommand(
            intent="expense",
            title="Electricity bill",
            category="Electricity",
            total_amount=Decimal("5000"),
        ),
    )

    assert await _count(db, Expense) == 1
    expense = (await db.execute(select(Expense))).scalar_one()
    assert expense.category == "Electricity"
    assert expense.amount == Decimal("5000")
    assert "Expense recorded" in result.message


async def test_expense_without_explicit_category_flagged_miscellaneous(db):
    user = await _make_user(db)

    command = _base_command("expense")
    command["title"] = "Shop"
    command["category"] = "Miscellaneous"
    command["total_amount"] = 5000
    proposal = await ai_service.propose(
        db, user, "Paid 5000 for the shop", _fake_client(command)
    )

    assert proposal.requires_confirmation is True
    assert "(Miscellaneous)" in proposal.message


# --- Unsupported / negation (spec 33, 34, 35, 56, 58, 73, 74, 75) ---------


async def test_unsupported_topic_gets_useful_explanation(db):
    user = await _make_user(db)

    command = _base_command("other")
    command["notes"] = "weather"
    proposal = await ai_service.propose(
        db, user, "What is the weather today?", _fake_client(command)
    )

    assert proposal.requires_confirmation is False
    assert "can't help with that" in proposal.message
    assert await _count(db, Sale) == 0
    assert await _count(db, Expense) == 0
    assert await _count(db, Purchase) == 0


async def test_destructive_requests_do_not_execute(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100)

    command = _base_command("other")
    command["notes"] = "delete all products"
    proposal = await ai_service.propose(
        db, user, "Delete all products", _fake_client(command)
    )

    assert "can't help with that" in proposal.message
    assert await _count(db, Product) == 1
    assert await _count(db, Sale) == 0


async def test_mixed_intent_message_is_declined(db):
    user = await _make_user(db)

    command = _base_command("other")
    command["notes"] = "mixed operations"
    proposal = await ai_service.propose(
        db, user, "Sold 10 rice, bought 20 coke and paid 5000 electricity",
        _fake_client(command),
    )

    assert proposal.requires_confirmation is False
    assert "more than one operation" in proposal.message
    assert await _count(db, Sale) == 0


# --- Idempotency (spec 40, 41) ---------------------------------------------


async def test_same_idempotency_key_executes_once(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100)

    command = AICommand(
        intent="sale", items=[AIItem(product_name="Rice", quantity=10)]
    )
    first = await ai_service.execute(db, user, command, idempotency_key="k1")
    second = await ai_service.execute(db, user, command, idempotency_key="k1")

    assert first.message == second.message
    assert await _count(db, Sale) == 1


async def test_different_idempotency_keys_allow_separate_sales(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100)

    command = AICommand(
        intent="sale", items=[AIItem(product_name="Rice", quantity=10)]
    )
    await ai_service.execute(db, user, command, idempotency_key="k1")
    await ai_service.execute(db, user, command, idempotency_key="k2")

    assert await _count(db, Sale) == 2


# --- Conversation context (spec 30, 32) -------------------------------------


async def test_context_is_included_for_same_conversation(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Rice", stock=100)

    follow_up_command = {
        **_base_command("sale"),
        "items": [{"product_name": "Rice", "quantity": 10}],
    }
    client = CapturingClient(json.dumps(follow_up_command))

    await ai_service.propose(
        db, user, "How much Rice do I have?", client, conversation_id="c1"
    )
    await ai_service.propose(
        db, user, "Sell 10.", client, conversation_id="c1"
    )

    system_prompt = client.calls[1]["messages"][0]["content"]
    user_message = client.calls[1]["messages"][1]["content"]
    assert "How much Rice do I have?" in system_prompt
    assert user_message == "Sell 10."


async def test_context_is_not_shared_across_conversations(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=100)

    follow_up_command = {
        **_base_command("sale"),
        "items": [{"product_name": "Coke", "quantity": 10}],
    }
    client = CapturingClient(json.dumps(follow_up_command))

    await ai_service.propose(
        db, user, "How much Rice do I have?", client, conversation_id="a"
    )
    await ai_service.propose(
        db, user, "How much Coke do I have?", client, conversation_id="b"
    )

    system_prompt = client.calls[1]["messages"][0]["content"]
    user_message = client.calls[1]["messages"][1]["content"]
    assert "How much Rice do I have?" not in system_prompt
    assert user_message == "How much Coke do I have?"


# --- Consistency & DB as source of truth (spec 63, 64, 66) -----------------


async def test_failed_sale_leaves_state_unchanged_and_inquiry_sees_it(db):
    user = await _make_user(db)
    product = await _make_product(db, user, name="Rice", stock=15)

    with pytest.raises(HTTPException):
        await ai_service.execute(
            db,
            user,
            AICommand(intent="sale", items=[AIItem(product_name="Rice", quantity=20)]),
        )
    assert await _product_stock(db, product.id) == 15
    assert await _count(db, Sale) == 0

    inquiry = await ai_service.execute(
        db,
        user,
        AICommand(
            intent="inquiry",
            items=[AIItem(product_name="Rice")],
        ),
    )
    assert "15" in inquiry.message


async def test_successful_sale_then_inquiry_reads_database(db):
    user = await _make_user(db)
    product = await _make_product(db, user, name="Rice", stock=100)

    await ai_service.execute(
        db,
        user,
        AICommand(intent="sale", items=[AIItem(product_name="Rice", quantity=10)]),
    )
    assert await _product_stock(db, product.id) == 90

    inquiry = await ai_service.execute(
        db,
        user,
        AICommand(intent="inquiry", items=[AIItem(product_name="Rice")]),
    )
    assert "90" in inquiry.message