import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.groq import get_groq_client
from app.models.customer import Customer
from app.models.product import Product
from app.models.user import User
from app.schemas.ai import AI_COMMAND_SCHEMA, AICommand, AIExecuteResponse, AIProposalResponse
from app.schemas.expense import ExpenseCreate
from app.schemas.purchase import PurchaseCreate
from app.schemas.sale import SaleCreate
from app.services import expense as expense_service
from app.services import purchase as purchase_service
from app.services import sale as sale_service

INTENT_HELP_MESSAGE = (
    "I can record your sales, purchases and expenses, and answer stock questions. "
    "Examples:\n"
    "- 'Sold 20 packs of rice'\n"
    "- 'Bought 10 cartons of Coke'\n"
    "- 'Paid 5,000 for electricity'\n"
    "- 'How much Coke stock is left?'"
)


def _fmt_money(value: Decimal) -> str:
    return f"{value:,.2f}"


def _structured_error(
    status_code: int,
    *,
    title: str,
    hint: str | None = None,
    options: list[str] | None = None,
) -> HTTPException:
    detail: dict = {"title": title}
    if hint:
        detail["hint"] = hint
    if options:
        detail["options"] = options
    return HTTPException(status_code=status_code, detail=detail)


def _fmt_catalog(products: list[Product], customers: list[Customer]) -> tuple[str, str]:
    product_lines = [
        f"- {p.name} ({p.unit}, selling at Rs {_fmt_money(p.selling_price)})"
        for p in products
    ]
    customer_lines = [f"- {c.name}" for c in customers]
    products_text = "\n".join(product_lines) or "- (none)"
    customers_text = "\n".join(customer_lines) or "- (none)"
    return products_text, customers_text


def _system_prompt(products: list[Product], customers: list[Customer]) -> str:
    products_text, customers_text = _fmt_catalog(products, customers)
    return f"""You are an assistant embedded in a retail management system used by a shopkeeper in Pakistan.
The user sends short, informal English messages about their daily business.
Translate the message into a single structured command with no extra text.

Supported intents:
- "sale": a product was sold to a customer.
- "purchase": inventory was bought from a supplier.
- "expense": money was spent on something (rent, electricity, transport, salary, etc.).
- "inquiry": the user is asking a question about their stock, not recording anything.
- "other": anything else (greeting, help request, unrelated message).

Rules:
- quantity is a positive integer.
- unit_price is the price per unit; total_amount is the total for the whole transaction.
  When the user gives only a total, put it in total_amount. When they give only a per-unit price, put it in unit_price.
- Sale: product_name is the item sold, customer_name is the customer if mentioned, otherwise null.
- Purchase: product_name is the item bought, supplier_name is the supplier if mentioned, otherwise null.
- Expense: put the amount in total_amount, a short label in title, and the category in category
  (use one of: Electricity, Internet, Transport, Salary, Rent, Miscellaneous). Use "Miscellaneous" when unclear.
- Inquiry: put the product being asked about in product_name.
- notes: extra detail worth keeping, otherwise null.
- date: transaction date as ISO format YYYY-MM-DD if the user mentions one, otherwise null (meaning today).

The user's products and customers are listed below. Users often refer to products by short or brand names.
Map such names to the exact full name from the Products list (for example "coke" -> "Coca Cola 1.5L Bottle",
"rice" -> "Super Basmati Rice 5kg", "oil" -> "Refined Cooking Oil 3L"). Always use the exact name from the list
when the message refers to one of them. Only if the message clearly refers to something NOT in the lists,
extract the name as the user wrote it.

Products:
{products_text}

Customers:
{customers_text}
"""


async def _load_catalog(
    db: AsyncSession, current_user: User
) -> tuple[list[Product], list[Customer]]:
    product_result = await db.execute(select(Product).order_by(Product.name))
    products = list(product_result.scalars().all())

    customer_result = await db.execute(
        select(Customer)
        .where(Customer.user_id == current_user.id)
        .order_by(Customer.name)
    )
    customers = list(customer_result.scalars().all())
    return products, customers


async def _parse_command(
    client,
    message: str,
    products: list[Product],
    customers: list[Customer],
) -> AICommand:
    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": _system_prompt(products, customers)},
            {"role": "user", "content": message},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "ai_command",
                "strict": True,
                "schema": AI_COMMAND_SCHEMA,
            },
        },
        max_tokens=300,
    )

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=502, detail="AI returned an invalid response"
        ) from None

    try:
        return AICommand.model_validate(data)
    except ValidationError:
        raise HTTPException(
            status_code=502, detail="AI response could not be validated"
        ) from None


def _match_product(products: list[Product], name: str | None) -> Product:
    if not name:
        raise _structured_error(
            status_code=400,
            title="A product name is missing.",
            hint="Tell me which product, for example: 'Sold 20 packs of rice'.",
        )

    normalized = name.strip().lower()
    matches = [
        p
        for p in products
        if p.name.strip().lower() == normalized
        or normalized in p.name.strip().lower()
        or p.name.strip().lower() in normalized
    ]
    unique = {p.name: p for p in matches}
    if len(unique) == 1:
        return next(iter(unique.values()))
    if len(unique) > 1:
        candidates = sorted(unique)
        raise _structured_error(
            status_code=400,
            title="That matches more than one product.",
            hint="Which one did you mean?",
            options=candidates,
        )

    available = [p.name for p in products[:15]]
    raise _structured_error(
        status_code=404,
        title=f"Product '{name}' isn't in your catalog.",
        hint="Choose one of your products:",
        options=available,
    )


async def _resolve_customer(
    db: AsyncSession,
    current_user: User,
    customers: list[Customer],
    name: str | None,
) -> Customer | None:
    if not name:
        return None

    normalized = name.strip().lower()
    for customer in customers:
        if (
            customer.name.strip().lower() == normalized
            or normalized in customer.name.strip().lower()
            or customer.name.strip().lower() in normalized
        ):
            return customer

    customer = Customer(
        name=name.strip(),
        phone=f"ai-{uuid.uuid4().hex[:12]}",
        user_id=current_user.id,
    )
    db.add(customer)
    try:
        await db.commit()
        await db.refresh(customer)
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to create customer"
        ) from None
    return customer


def _resolve_prices(
    intent: str, command: AICommand, product: Product
) -> tuple[Decimal, Decimal]:
    default_price = (
        product.selling_price if intent == "sale" else product.purchase_price
    )
    unit_price = command.unit_price
    total_amount = command.total_amount

    if unit_price is None and total_amount is None:
        unit_price = default_price

    if unit_price is not None and total_amount is None and command.quantity:
        total_amount = unit_price * command.quantity
    elif total_amount is not None and unit_price is None and command.quantity:
        unit_price = total_amount / command.quantity

    if unit_price is None:
        raise _structured_error(
            status_code=400,
            title="I couldn't work out a price.",
            hint="Add a price, for example 'Sold 20 packs of rice at 300 each'.",
        )
    if total_amount is None:
        raise _structured_error(
            status_code=400,
            title="I couldn't work out the total amount.",
            hint="Add a price or total, for example 'Sold 20 packs of rice for 6,000'.",
        )
    return unit_price, total_amount


def _coerce_date(command: AICommand) -> datetime:
    date = command.date or datetime.now(UTC)
    if date.tzinfo is None:
        date = date.replace(tzinfo=UTC)
    return date


def _stock_answer(product: Product) -> str:
    return (
        f"{product.name}: {product.stock_quantity} {product.unit} in stock"
        f" (minimum {product.minimum_stock})."
    )


def _answer_inquiry(
    command: AICommand, products: list[Product]
) -> str:
    if not command.product_name:
        return (
            "Please ask about a specific product, for example: "
            "'How much Coke stock is left?'"
        )
    product = _match_product(products, command.product_name)
    return _stock_answer(product)


async def _propose_sale(
    command: AICommand,
    products: list[Product],
) -> str:
    product = _match_product(products, command.product_name)
    if command.quantity is None:
        raise _structured_error(
            status_code=400,
            title="I need a quantity for this sale.",
            hint="For example, 'Sold 20 packs of rice'.",
        )
    unit_price, total_amount = _resolve_prices("sale", command, product)

    customer_text = command.customer_name or "Walk-in customer"

    new_stock = product.stock_quantity - command.quantity
    if new_stock < 0:
        raise _structured_error(
            status_code=400,
            title=f"Not enough stock of {product.name}.",
            hint=(
                f"You have {product.stock_quantity} {product.unit} in stock, "
                f"but you asked to sell {command.quantity} {product.unit}."
            ),
        )

    command.unit_price = unit_price
    command.total_amount = total_amount
    command.product_unit = product.unit
    command.stock_after = new_stock

    return (
        f"Sale: {command.quantity} x {product.name} ({product.unit}) "
        f"at Rs {_fmt_money(unit_price)} = Rs {_fmt_money(total_amount)}. "
        f"Customer: {customer_text}. "
        f"Stock after: {new_stock} {product.unit}."
    )


async def _propose_purchase(
    command: AICommand, products: list[Product]
) -> str:
    product = _match_product(products, command.product_name)
    if command.quantity is None:
        raise _structured_error(
            status_code=400,
            title="I need a quantity for this purchase.",
            hint="For example, 'Bought 10 cartons of Coke'.",
        )
    unit_price, total_amount = _resolve_prices("purchase", command, product)
    supplier = command.supplier_name or "Unknown supplier"

    new_stock = product.stock_quantity + command.quantity
    command.unit_price = unit_price
    command.total_amount = total_amount
    command.product_unit = product.unit
    command.stock_after = new_stock
    return (
        f"Purchase: {command.quantity} x {product.name} ({product.unit}) "
        f"at Rs {_fmt_money(unit_price)} = Rs {_fmt_money(total_amount)}. "
        f"Supplier: {supplier}. "
        f"Stock after: {new_stock} {product.unit}."
    )


def _propose_expense(command: AICommand) -> str:
    if command.total_amount is None:
        raise _structured_error(
            status_code=400,
            title="I couldn't find an amount for this expense.",
            hint="For example, 'Paid 5,000 for electricity'.",
        )
    title = command.title or "Expense"
    category = command.category or "Miscellaneous"
    return (
        f"Expense: {title} ({category}) "
        f"= Rs {_fmt_money(command.total_amount)}."
    )


async def propose(
    db: AsyncSession,
    current_user: User,
    message: str,
    client=None,
) -> AIProposalResponse:
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI assistant is not configured (GROQ_API_KEY missing)",
        )

    client = client or get_groq_client()
    products, customers = await _load_catalog(db, current_user)
    command = await _parse_command(client, message, products, customers)

    if command.intent == "inquiry":
        return AIProposalResponse(
            command=command,
            requires_confirmation=False,
            message=_answer_inquiry(command, products),
        )
    if command.intent == "other":
        return AIProposalResponse(
            command=command,
            requires_confirmation=False,
            message=INTENT_HELP_MESSAGE,
        )
    if command.intent == "sale":
        message = await _propose_sale(command, products)
    elif command.intent == "purchase":
        message = await _propose_purchase(command, products)
    else:
        message = _propose_expense(command)

    return AIProposalResponse(
        command=command, requires_confirmation=True, message=message
    )


async def _execute_sale(
    db: AsyncSession,
    current_user: User,
    command: AICommand,
    products: list[Product],
    customers: list[Customer],
) -> tuple[str, dict]:
    product = _match_product(products, command.product_name)
    if command.quantity is None:
        raise _structured_error(
            status_code=400,
            title="I need a quantity for this sale.",
        )
    unit_price, total_amount = _resolve_prices("sale", command, product)
    customer = await _resolve_customer(
        db, current_user, customers, command.customer_name
    )

    data = SaleCreate(
        product_id=product.id,
        customer_id=customer.id if customer else None,
        quantity=command.quantity,
        unit_price=unit_price,
        total_amount=total_amount,
        sale_date=_coerce_date(command),
        notes=command.notes,
    )
    record = await sale_service.create_sale(db, data, current_user)

    customer_text = customer.name if customer else "Walk-in customer"
    message = (
        f"Sale recorded: {command.quantity} x {product.name} ({product.unit}) "
        f"at Rs {_fmt_money(unit_price)} = Rs {_fmt_money(total_amount)}. "
        f"Customer: {customer_text}. "
        f"Stock left: {product.stock_quantity} {product.unit}."
    )
    return message, record


async def _execute_purchase(
    db: AsyncSession,
    current_user: User,
    command: AICommand,
    products: list[Product],
) -> tuple[str, dict]:
    product = _match_product(products, command.product_name)
    if command.quantity is None:
        raise _structured_error(
            status_code=400,
            title="I need a quantity for this purchase.",
        )
    unit_price, total_amount = _resolve_prices("purchase", command, product)
    supplier_name = command.supplier_name or "Unknown"

    data = PurchaseCreate(
        product_id=product.id,
        supplier_name=supplier_name,
        quantity=command.quantity,
        purchase_price=unit_price,
        total_amount=total_amount,
        purchase_date=_coerce_date(command),
        notes=command.notes,
    )
    record = await purchase_service.create_purchase(db, data, current_user)

    message = (
        f"Purchase recorded: {command.quantity} x {product.name} ({product.unit}) "
        f"at Rs {_fmt_money(unit_price)} = Rs {_fmt_money(total_amount)}. "
        f"Supplier: {supplier_name}. "
        f"Stock left: {product.stock_quantity} {product.unit}."
    )
    return message, record


async def _execute_expense(
    db: AsyncSession,
    current_user: User,
    command: AICommand,
) -> tuple[str, dict]:
    if command.total_amount is None:
        raise _structured_error(
            status_code=400,
            title="I couldn't find an amount for this expense.",
        )
    data = ExpenseCreate(
        title=command.title or "Expense",
        category=command.category or "Miscellaneous",
        amount=command.total_amount,
        expense_date=_coerce_date(command),
        notes=command.notes,
    )
    expense = await expense_service.create_expense(db, data, current_user)

    record = {
        "id": str(expense.id),
        "title": expense.title,
        "category": expense.category,
        "amount": str(expense.amount),
        "expense_date": expense.expense_date.isoformat(),
    }
    message = (
        f"Expense recorded: {expense.title} ({expense.category}) "
        f"= Rs {_fmt_money(expense.amount)}."
    )
    return message, record


async def execute(
    db: AsyncSession,
    current_user: User,
    command: AICommand,
    client=None,
) -> AIExecuteResponse:
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="AI assistant is not configured (GROQ_API_KEY missing)",
        )

    products, customers = await _load_catalog(db, current_user)

    if command.intent == "inquiry":
        return AIExecuteResponse(
            message=_answer_inquiry(command, products), record={}
        )
    if command.intent == "other":
        return AIExecuteResponse(message=INTENT_HELP_MESSAGE, record={})
    if command.intent == "sale":
        message, record = await _execute_sale(
            db, current_user, command, products, customers
        )
    elif command.intent == "purchase":
        message, record = await _execute_purchase(
            db, current_user, command, products
        )
    else:
        message, record = await _execute_expense(db, current_user, command)

    return AIExecuteResponse(message=message, record=record)
