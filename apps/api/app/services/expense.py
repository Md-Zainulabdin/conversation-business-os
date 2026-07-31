import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


async def list_expenses(db: AsyncSession, current_user: User) -> list[Expense]:
    result = await db.execute(
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.expense_date.desc())
    )
    return list(result.scalars().all())


async def get_expense(
    db: AsyncSession, expense_id: uuid.UUID, current_user: User
) -> Expense:
    result = await db.execute(
        select(Expense).where(
            Expense.id == expense_id, Expense.user_id == current_user.id
        )
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


async def create_expense(
    db: AsyncSession, data: ExpenseCreate, current_user: User
) -> Expense:
    expense = Expense(**data.model_dump(), user_id=current_user.id)
    db.add(expense)
    try:
        await db.commit()
        await db.refresh(expense)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create expense") from None
    return expense


async def update_expense(
    db: AsyncSession, expense_id: uuid.UUID, data: ExpenseUpdate, current_user: User
) -> Expense:
    expense = await get_expense(db, expense_id, current_user)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(expense, field, value)

    try:
        await db.commit()
        await db.refresh(expense)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update expense") from None
    return expense


async def delete_expense(
    db: AsyncSession, expense_id: uuid.UUID, current_user: User
) -> None:
    expense = await get_expense(db, expense_id, current_user)
    try:
        await db.delete(expense)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete expense") from None
