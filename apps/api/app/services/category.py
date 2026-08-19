import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


async def list_categories(
    db: AsyncSession, limit: int = 100, offset: int = 0
) -> tuple[list[Category], int]:
    total_result = await db.execute(select(func.count()).select_from(Category))
    total = total_result.scalar_one()
    result = await db.execute(
        select(Category).order_by(Category.name).limit(limit).offset(offset)
    )
    return list(result.scalars().all()), total


async def get_category(db: AsyncSession, category_id: uuid.UUID) -> Category:
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


async def create_category(db: AsyncSession, data: CategoryCreate) -> Category:
    result = await db.execute(select(Category).where(Category.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Category already exists")

    category = Category(name=data.name, description=data.description)
    db.add(category)
    try:
        await db.commit()
        await db.refresh(category)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create category") from None
    return category


async def update_category(
    db: AsyncSession, category_id: uuid.UUID, data: CategoryUpdate
) -> Category:
    category = await get_category(db, category_id)

    if data.name is not None:
        result = await db.execute(
            select(Category).where(Category.name == data.name, Category.id != category_id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Category name already taken")
        category.name = data.name
    if data.description is not None:
        category.description = data.description

    try:
        await db.commit()
        await db.refresh(category)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update category") from None
    return category


async def delete_category(db: AsyncSession, category_id: uuid.UUID) -> None:
    category = await get_category(db, category_id)
    try:
        await db.delete(category)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete category") from None
