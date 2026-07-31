from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.expense import Expense
from app.models.product import Product
from app.models.purchase import Purchase
from app.models.sale import Sale
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
    total_sales = total_sales_result.scalar()

    stock_result = await db.execute(
        select(func.coalesce(func.sum(Product.stock_quantity), 0))
    )
    stock_items = stock_result.scalar()

    customer_count_result = await db.execute(
        select(func.count(Customer.id)).where(Customer.user_id == current_user.id)
    )
    active_customers = customer_count_result.scalar()

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
        "total_sales": float(total_sales),
        "stock_items": stock_items,
        "active_customers": active_customers,
        "transactions": [
            {**t, "amount": float(t["amount"])} for t in transactions
        ],
    }
