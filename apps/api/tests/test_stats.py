import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.models.customer import Customer
from app.models.expense import Expense
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.user import User
from app.services import stats as stats_service


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
    db, user: User, *, stock: int = 0, minimum: int = 0, category: str = "Grains"
) -> Product:
    product = Product(
        user_id=user.id,
        name=f"Product-{uuid.uuid4().hex[:8]}",
        sku=f"SKU-{uuid.uuid4().hex[:8]}",
        category=category,
        unit="Pack",
        purchase_price=Decimal("100"),
        selling_price=Decimal("150"),
        stock_quantity=stock,
        minimum_stock=minimum,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def _make_customer(db, user: User) -> Customer:
    customer = Customer(
        user_id=user.id,
        name=f"Customer-{uuid.uuid4().hex[:8]}",
        phone=f"+92 300 {uuid.uuid4().hex[:7]}",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


async def _make_sale(
    db,
    user: User,
    product: Product,
    customer: Customer,
    *,
    quantity: int = 5,
    days_ago: int = 0,
) -> Sale:
    unit_price = Decimal("150")
    sale = Sale(
        user_id=user.id,
        customer_id=customer.id,
        total_amount=unit_price * quantity,
        sale_date=datetime.now(UTC) - timedelta(days=days_ago),
    )
    sale.items = [
        SaleItem(
            product_id=product.id,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=unit_price * quantity,
        )
    ]
    db.add(sale)
    await db.commit()
    await db.refresh(sale)
    return sale


async def _make_expense(
    db, user: User, *, amount: str = "500", days_ago: int = 0
) -> Expense:
    expense = Expense(
        user_id=user.id,
        title="Electricity bill",
        category="Electricity",
        amount=Decimal(amount),
        expense_date=datetime.now(UTC) - timedelta(days=days_ago),
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


async def test_overview_reports_profit(db):
    user = await _make_user(db)
    product = await _make_product(db, user, stock=100)
    customer = await _make_customer(db, user)

    await _make_sale(db, user, product, customer, quantity=10)
    await _make_expense(db, user, amount="500")

    overview = await stats_service.get_overview(db, user)

    assert overview["total_sales"] == 1500.0
    assert overview["expenses_total"] == 500.0
    assert overview["profit"] == 1000.0


async def test_overview_profit_can_be_negative(db):
    user = await _make_user(db)
    product = await _make_product(db, user, stock=100)
    customer = await _make_customer(db, user)

    await _make_sale(db, user, product, customer, quantity=2)
    await _make_expense(db, user, amount="1000")

    overview = await stats_service.get_overview(db, user)

    assert overview["total_sales"] == 300.0
    assert overview["profit"] == -700.0


async def test_overview_ignores_sales_outside_period(db):
    user = await _make_user(db)
    product = await _make_product(db, user, stock=100)
    customer = await _make_customer(db, user)

    await _make_sale(db, user, product, customer, quantity=10, days_ago=0)
    await _make_sale(db, user, product, customer, quantity=10, days_ago=40)

    overview = await stats_service.get_overview(db, user, period="30d")

    assert overview["total_sales"] == 1500.0


async def test_low_stock_flags_products_at_or_below_threshold(db):
    user = await _make_user(db)
    await _make_product(db, user, stock=0, minimum=5)
    await _make_product(db, user, stock=5, minimum=5)
    await _make_product(db, user, stock=6, minimum=5)

    overview = await stats_service.get_overview(db, user)

    assert overview["low_stock_count"] == 2
    assert {p["stock_quantity"] for p in overview["low_stock"]} == {0, 5}


async def test_daily_sales_summary_buckets_by_day(db):
    user = await _make_user(db)
    product = await _make_product(db, user, stock=100)
    customer = await _make_customer(db, user)

    await _make_sale(db, user, product, customer, quantity=10, days_ago=0)
    await _make_sale(db, user, product, customer, quantity=10, days_ago=1)

    overview = await stats_service.get_overview(db, user)

    assert len(overview["daily_sales"]) == 2
    assert sum(d["amount"] for d in overview["daily_sales"]) == 3000.0


async def test_top_products_ranked_by_revenue(db):
    user = await _make_user(db)
    product_a = await _make_product(db, user, stock=100, category="Grains")
    product_b = await _make_product(db, user, stock=100, category="Drinks")
    customer = await _make_customer(db, user)

    await _make_sale(db, user, product_b, customer, quantity=10)
    await _make_sale(db, user, product_a, customer, quantity=2)

    overview = await stats_service.get_overview(db, user)

    assert [p["name"] for p in overview["top_products"]] == [
        product_b.name,
        product_a.name,
    ]
    assert overview["top_products"][0]["revenue"] == 1500.0


async def test_top_customers_ranked_by_spend(db):
    user = await _make_user(db)
    product = await _make_product(db, user, stock=100)
    customer_a = await _make_customer(db, user)
    customer_b = await _make_customer(db, user)

    await _make_sale(db, user, product, customer_a, quantity=10)
    await _make_sale(db, user, product, customer_b, quantity=2)

    overview = await stats_service.get_overview(db, user)

    assert [c["name"] for c in overview["top_customers"]] == [
        customer_a.name,
        customer_b.name,
    ]
    assert overview["top_customers"][0]["spend"] == 1500.0


async def test_category_breakdown_sums_by_product_category(db):
    user = await _make_user(db)
    grains = await _make_product(db, user, stock=100, category="Grains")
    drinks = await _make_product(db, user, stock=100, category="Drinks")
    customer = await _make_customer(db, user)

    await _make_sale(db, user, grains, customer, quantity=10)
    await _make_sale(db, user, drinks, customer, quantity=2)

    overview = await stats_service.get_overview(db, user)

    breakdown = {c["category"]: c["amount"] for c in overview["category_breakdown"]}
    assert breakdown["Grains"] == 1500.0
    assert breakdown["Drinks"] == 300.0


async def test_expense_breakdown_sums_by_category(db):
    user = await _make_user(db)
    await _make_expense(db, user, amount="500")
    await _make_expense(db, user, amount="200")

    overview = await stats_service.get_overview(db, user)

    assert overview["expense_breakdown"] == [
        {"category": "Electricity", "amount": 700.0}
    ]


async def test_report_data_is_scoped_per_user(db):
    user_a = await _make_user(db)
    user_b = await _make_user(db)
    product_a = await _make_product(db, user_a, stock=100)
    product_b = await _make_product(db, user_b, stock=100)
    customer_a = await _make_customer(db, user_a)
    customer_b = await _make_customer(db, user_b)

    await _make_sale(db, user_a, product_a, customer_a, quantity=10)
    await _make_sale(db, user_b, product_b, customer_b, quantity=2)
    await _make_expense(db, user_a, amount="500")

    overview_a = await stats_service.get_overview(db, user_a)
    overview_b = await stats_service.get_overview(db, user_b)

    assert overview_a["total_sales"] == 1500.0
    assert overview_b["total_sales"] == 300.0
    assert overview_a["profit"] == 1000.0
    assert overview_b["profit"] == 300.0
    assert [c["name"] for c in overview_a["top_customers"]] == [customer_a.name]
    assert [c["name"] for c in overview_b["top_customers"]] == [customer_b.name]