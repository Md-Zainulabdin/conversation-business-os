import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate


async def list_products(db: AsyncSession, current_user: User) -> list[Product]:
    result = await db.execute(
        select(Product)
        .where(Product.user_id == current_user.id)
        .order_by(Product.name)
    )
    return list(result.scalars().all())


async def get_product(
    db: AsyncSession, product_id: uuid.UUID, current_user: User
) -> Product:
    result = await db.execute(
        select(Product).where(
            Product.id == product_id, Product.user_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


async def create_product(
    db: AsyncSession, data: ProductCreate, current_user: User
) -> Product:
    result = await db.execute(
        select(Product).where(
            Product.sku == data.sku, Product.user_id == current_user.id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Product with this SKU already exists")

    product = Product(**data.model_dump(), user_id=current_user.id)
    db.add(product)
    try:
        await db.commit()
        await db.refresh(product)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create product") from None
    return product


async def update_product(
    db: AsyncSession, product_id: uuid.UUID, data: ProductUpdate, current_user: User
) -> Product:
    product = await get_product(db, product_id, current_user)

    if data.sku is not None:
        result = await db.execute(
            select(Product).where(
                Product.sku == data.sku,
                Product.user_id == current_user.id,
                Product.id != product_id,
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="SKU already taken")
        product.sku = data.sku

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field != "sku":
            setattr(product, field, value)

    try:
        await db.commit()
        await db.refresh(product)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update product") from None
    return product


async def delete_product(
    db: AsyncSession, product_id: uuid.UUID, current_user: User
) -> None:
    product = await get_product(db, product_id, current_user)
    try:
        await db.delete(product)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete product") from None
