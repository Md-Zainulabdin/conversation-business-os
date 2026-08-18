import asyncio
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

# Valid MP3 magic bytes for testing (ID3v2 header)
FAKE_AUDIO_MP3 = b"ID3\x03\x00\x00\x00\x00\x00fake-audio-data"


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


class VoiceFakeClient:
    def __init__(self, transcript: str, command: dict):
        self._transcript = transcript
        self._command = command
        self.transcription_calls = 0
        self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self._transcribe))

    async def _transcribe(self, **kwargs):
        self.transcription_calls += 1
        return SimpleNamespace(text=self._transcript)

    @property
    def chat(self):
        return SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    async def _create(self, **kwargs):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(self._command))
                )
            ]
        )


async def test_voice_propose_sale_matches_typed_text(db):
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
    client = VoiceFakeClient("Sold 20 packs of Coke", command)
    transcript, proposal = await ai_service.transcribe_and_propose(
        db, user, FAKE_AUDIO_MP3, "recording.mp3", client=client
    )

    assert client.transcription_calls == 1
    assert transcript == "Sold 20 packs of Coke"
    assert proposal.requires_confirmation is True
    assert "Sale: 20 x Coke" in proposal.message
    assert await _count(db, Sale) == 0


async def test_voice_propose_and_execute_records_sale(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Coke", stock=100)

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "Coke",
            "quantity": 10,
            "unit_price": None,
            "total_amount": None,
        }
    ]
    client = VoiceFakeClient("Sold 10 packs of Coke", command)
    transcript, proposal = await ai_service.transcribe_and_propose(
        db, user, FAKE_AUDIO_MP3, "recording.mp3", client=client
    )
    result = await ai_service.execute(db, user, proposal.command)

    assert await _count(db, Sale) == 1
    sale = (await db.execute(select(Sale))).scalar_one()
    assert sale.items[0].quantity == 10
    assert result.message.startswith("Sale recorded: 10 x Coke")


async def test_voice_ambiguous_product_asks_which_one(db):
    user = await _make_user(db)
    await _make_product(db, user, name="Golden Basmati Rice 5kg", stock=50)
    await _make_product(db, user, name="Super Basmati Rice 5kg", stock=100)

    command = _base_command("sale")
    command["items"] = [
        {
            "product_name": "rice",
            "quantity": 20,
            "unit_price": None,
            "total_amount": None,
        }
    ]
    client = VoiceFakeClient("Sold 20 packs of rice", command)
    transcript, proposal = await ai_service.transcribe_and_propose(
        db, user, FAKE_AUDIO_MP3, "recording.mp3", client=client
    )

    assert proposal.disambiguation is not None
    assert len(proposal.disambiguation) == 2
    assert await _count(db, Sale) == 0


async def test_voice_empty_transcript_is_rejected(db):
    user = await _make_user(db)

    client = VoiceFakeClient("   ", _base_command("other"))
    with pytest.raises(HTTPException) as exc:
        await ai_service.transcribe_and_propose(
            db, user, FAKE_AUDIO_MP3, "recording.mp3", client=client
        )
    assert exc.value.status_code == 400
    assert "could not hear" in exc.value.detail["title"]


class OversizedAudioFakeClient:
    def __init__(self):
        self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self._transcribe))

    async def _transcribe(self, **kwargs):
        return SimpleNamespace(text="test")

    @property
    def chat(self):
        return SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    async def _create(self, **kwargs):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(_base_command("other")))
                )
            ]
        )


async def test_voice_oversized_audio_rejected(db):
    user = await _make_user(db)
    oversized_audio = b"x" * (25 * 1024 * 1024 + 1)

    client = OversizedAudioFakeClient()
    with pytest.raises(HTTPException) as exc:
        await ai_service.transcribe_and_propose(
            db, user, oversized_audio, "recording.mp3", client=client
        )
    assert exc.value.status_code == 400
    assert "too large" in exc.value.detail["title"]


async def test_voice_invalid_magic_bytes_rejected(db):
    user = await _make_user(db)
    fake_audio = b"not-audio-data"

    class InvalidMagicClient:
        def __init__(self):
            self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self._transcribe))

        async def _transcribe(self, **kwargs):
            return SimpleNamespace(text="test")

        @property
        def chat(self):
            return SimpleNamespace(
                completions=SimpleNamespace(create=self._create)
            )

        async def _create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=json.dumps(_base_command("other")))
                    )
                ]
            )

    client = InvalidMagicClient()
    with pytest.raises(HTTPException) as exc:
        await ai_service.transcribe_and_propose(
            db, user, fake_audio, "recording.mp3", client=client
        )
    assert exc.value.status_code == 400
    assert "format does not match" in exc.value.detail["title"]


async def test_voice_transcription_timeout_handled(db, monkeypatch):
    user = await _make_user(db)
    from app.core.config import settings
    monkeypatch.setattr(settings, "TRANSCRIPTION_TIMEOUT_SECONDS", 0.01)

    class TimeoutClient:
        def __init__(self):
            self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self._transcribe))

        async def _transcribe(self, **kwargs):
            await asyncio.sleep(0.1)
            return SimpleNamespace(text="test")

        @property
        def chat(self):
            return SimpleNamespace(
                completions=SimpleNamespace(create=self._create)
            )

        async def _create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=json.dumps(_base_command("other")))
                    )
                ]
            )

    client = TimeoutClient()
    with pytest.raises(HTTPException) as exc:
        await ai_service.transcribe_and_propose(
            db, user, FAKE_AUDIO_MP3, "recording.mp3", client=client
        )
    assert exc.value.status_code == 400
    assert "timed out" in exc.value.detail["title"]


async def test_voice_filename_sanitization(db):
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
    client = VoiceFakeClient("Sold 5 Coke", command)

    malicious_filename = "../../../etc/passwd.mp3"
    transcript, proposal = await ai_service.transcribe_and_propose(
        db, user, FAKE_AUDIO_MP3, malicious_filename, client=client
    )

    assert transcript == "Sold 5 Coke"
    assert proposal.requires_confirmation is True