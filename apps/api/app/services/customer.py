import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerUpdate


async def list_customers(
    db: AsyncSession, current_user: User, limit: int = 100, offset: int = 0
) -> tuple[list[Customer], int]:
    base = select(Customer).where(Customer.user_id == current_user.id)

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar_one()

    result = await db.execute(base.order_by(Customer.name).limit(limit).offset(offset))
    return list(result.scalars().all()), total


async def get_customer(
    db: AsyncSession, customer_id: uuid.UUID, current_user: User
) -> Customer:
    result = await db.execute(
        select(Customer).where(
            Customer.id == customer_id, Customer.user_id == current_user.id
        )
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


async def create_customer(
    db: AsyncSession, data: CustomerCreate, current_user: User
) -> Customer:
    result = await db.execute(
        select(Customer).where(
            Customer.phone == data.phone, Customer.user_id == current_user.id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="Customer with this phone already exists"
        )

    customer = Customer(**data.model_dump(), user_id=current_user.id)
    db.add(customer)
    try:
        await db.commit()
        await db.refresh(customer)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create customer") from None
    return customer


async def update_customer(
    db: AsyncSession, customer_id: uuid.UUID, data: CustomerUpdate, current_user: User
) -> Customer:
    customer = await get_customer(db, customer_id, current_user)

    update_data = data.model_dump(exclude_unset=True)

    if data.phone is not None:
        result = await db.execute(
            select(Customer).where(
                Customer.phone == data.phone,
                Customer.user_id == current_user.id,
                Customer.id != customer_id,
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Phone already taken")

    for field, value in update_data.items():
        setattr(customer, field, value)

    try:
        await db.commit()
        await db.refresh(customer)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update customer") from None
    return customer


async def delete_customer(
    db: AsyncSession, customer_id: uuid.UUID, current_user: User
) -> None:
    customer = await get_customer(db, customer_id, current_user)
    try:
        await db.delete(customer)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete customer") from None
