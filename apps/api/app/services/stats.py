from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.expense import Expense
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.sale import Sale, SaleItem
from app.models.user import User


def _period_start(period: str) -> datetime:
    now = datetime.now(UTC)
    match period:
        case "24h":
            return now - timedelta(hours=24)
        case "7d":
            return now - timedelta(days=7)
        case "12m":
            return now - timedelta(days=365)
        case _:
            return now - timedelta(days=30)


async def get_overview(db: AsyncSession, current_user: User, period: str = "30d"):
    cutoff = _period_start(period)

    total_sales_result = await db.execute(
        select(func.coalesce(func.sum(Sale.total_amount), 0)).where(
            Sale.user_id == current_user.id, Sale.sale_date >= cutoff
        )
    )
    total_sales = float(total_sales_result.scalar())

    expenses_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.user_id == current_user.id, Expense.expense_date >= cutoff
        )
    )
    expenses_total = float(expenses_result.scalar())

    stock_result = await db.execute(
        select(func.coalesce(func.sum(Product.stock_quantity), 0)).where(
            Product.user_id == current_user.id
        )
    )
    stock_items = stock_result.scalar()

    customer_count_result = await db.execute(
        select(func.count(Customer.id)).where(Customer.user_id == current_user.id)
    )
    active_customers = customer_count_result.scalar()

    low_stock_result = await db.execute(
        select(Product).where(
            Product.user_id == current_user.id,
            Product.stock_quantity <= Product.minimum_stock,
        ).order_by(Product.stock_quantity.asc())
    )
    low_stock = low_stock_result.scalars().all()

    daily_sales_result = await db.execute(
        select(Sale.sale_date, Sale.total_amount).where(
            Sale.user_id == current_user.id, Sale.sale_date >= cutoff
        ).order_by(Sale.sale_date.asc())
    )
    daily_totals: dict[str, float] = {}
    for sale_date, amount in daily_sales_result.all():
        day = sale_date.date().isoformat()
        daily_totals[day] = daily_totals.get(day, 0.0) + float(amount)

    top_products_result = await db.execute(
        select(
            Product.name,
            func.sum(SaleItem.quantity),
            func.sum(SaleItem.total_amount),
        )
        .join(Sale, Sale.id == SaleItem.sale_id)
        .join(Product, Product.id == SaleItem.product_id)
        .where(
            Sale.user_id == current_user.id,
            Sale.sale_date >= cutoff,
        )
        .group_by(Product.id)
        .order_by(func.sum(SaleItem.total_amount).desc())
        .limit(5)
    )
    top_products = [
        {
            "name": name,
            "quantity": int(quantity or 0),
            "revenue": float(total or 0),
        }
        for name, quantity, total in top_products_result.all()
    ]

    top_customers_result = await db.execute(
        select(
            Customer.name,
            func.sum(Sale.total_amount),
        )
        .join(Sale, Sale.customer_id == Customer.id)
        .where(
            Sale.user_id == current_user.id,
            Sale.sale_date >= cutoff,
        )
        .group_by(Customer.id)
        .order_by(func.sum(Sale.total_amount).desc())
        .limit(5)
    )
    top_customers = [
        {"name": name, "spend": float(total or 0)}
        for name, total in top_customers_result.all()
    ]

    category_result = await db.execute(
        select(
            Product.category,
            func.sum(SaleItem.total_amount),
        )
        .join(Sale, Sale.id == SaleItem.sale_id)
        .join(Product, Product.id == SaleItem.product_id)
        .where(
            Sale.user_id == current_user.id,
            Sale.sale_date >= cutoff,
        )
        .group_by(Product.category)
        .order_by(func.sum(SaleItem.total_amount).desc())
    )
    category_breakdown = [
        {"category": category, "amount": float(total or 0)}
        for category, total in category_result.all()
    ]

    expense_category_result = await db.execute(
        select(
            Expense.category,
            func.sum(Expense.amount),
        )
        .where(
            Expense.user_id == current_user.id,
            Expense.expense_date >= cutoff,
        )
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
    )
    expense_breakdown = [
        {"category": category, "amount": float(total or 0)}
        for category, total in expense_category_result.all()
    ]

    sale_result = await db.execute(
        select(Sale).where(
            Sale.user_id == current_user.id, Sale.sale_date >= cutoff
        ).order_by(Sale.sale_date.desc()).limit(10)
    )
    sales = sale_result.scalars().all()

    purchase_result = await db.execute(
        select(Purchase).where(
            Purchase.user_id == current_user.id, Purchase.purchase_date >= cutoff
        ).order_by(Purchase.purchase_date.desc()).limit(10)
    )
    purchases = purchase_result.scalars().all()

    expense_result = await db.execute(
        select(Expense).where(
            Expense.user_id == current_user.id, Expense.expense_date >= cutoff
        ).order_by(Expense.expense_date.desc()).limit(10)
    )
    expenses = expense_result.scalars().all()

    transactions = []

    for s in sales:
        transactions.append({
            "id": str(s.id),
            "type": "Sale",
            "reference": f"Sale-{str(s.id)[:8]}",
            "entity": "Customer",
            "amount": s.total_amount,
            "status": "Completed",
            "date": s.sale_date,
        })

    for p in purchases:
        transactions.append({
            "id": str(p.id),
            "type": "Purchase",
            "reference": f"Purch-{str(p.id)[:8]}",
            "entity": p.supplier_name,
            "amount": p.total_amount,
            "status": "Completed",
            "date": p.purchase_date,
        })

    for e in expenses:
        transactions.append({
            "id": str(e.id),
            "type": "Expense",
            "reference": f"Exp-{str(e.id)[:8]}",
            "entity": e.category,
            "amount": e.amount,
            "status": "Paid",
            "date": e.expense_date,
        })

    transactions.sort(key=lambda t: t["date"], reverse=True)
    transactions = transactions[:20]

    return {
        "total_sales": total_sales,
        "expenses_total": expenses_total,
        "profit": total_sales - expenses_total,
        "stock_items": stock_items,
        "active_customers": active_customers,
        "low_stock_count": len(low_stock),
        "daily_sales": [
            {"date": day, "amount": amount}
            for day, amount in sorted(daily_totals.items())
        ],
        "low_stock": [
            {
                "id": str(p.id),
                "name": p.name,
                "sku": p.sku,
                "unit": p.unit,
                "stock_quantity": p.stock_quantity,
                "minimum_stock": p.minimum_stock,
            }
            for p in low_stock
        ],
        "top_products": top_products,
        "top_customers": top_customers,
        "category_breakdown": category_breakdown,
        "expense_breakdown": expense_breakdown,
        "transactions": [
            {**t, "amount": float(t["amount"])} for t in transactions
        ],
    }