import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.purchase import Purchase
from app.models.user import User
from app.schemas.purchase import PurchaseCreate, PurchaseUpdate


async def _enrich_purchase(db: AsyncSession, purchase: Purchase) -> dict:
    product_result = await db.execute(
        select(Product.name).where(Product.id == purchase.product_id)
    )
    product_name = product_result.scalar_one_or_none() or "Unknown"

    return {
        **{c.name: getattr(purchase, c.name) for c in purchase.__table__.columns},
        "product_name": product_name,
    }


async def list_purchases(db: AsyncSession, current_user: User) -> list[dict]:
    result = await db.execute(
        select(Purchase)
        .where(Purchase.user_id == current_user.id)
        .order_by(Purchase.purchase_date.desc())
    )
    purchases = list(result.scalars().all())
    return [await _enrich_purchase(db, p) for p in purchases]


async def get_purchase(
    db: AsyncSession, purchase_id: uuid.UUID, current_user: User
) -> dict:
    result = await db.execute(
        select(Purchase).where(
            Purchase.id == purchase_id, Purchase.user_id == current_user.id
        )
    )
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return await _enrich_purchase(db, purchase)


async def create_purchase(
    db: AsyncSession, data: PurchaseCreate, current_user: User
) -> dict:
    product = await db.execute(
        select(Product).where(Product.id == data.product_id)
    )
    product = product.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    purchase = Purchase(**data.model_dump(), user_id=current_user.id)
    product.stock_quantity += data.quantity

    db.add(purchase)
    try:
        await db.commit()
        await db.refresh(purchase)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create purchase") from None
    return await _enrich_purchase(db, purchase)


async def update_purchase(
    db: AsyncSession, purchase_id: uuid.UUID, data: PurchaseUpdate, current_user: User
) -> dict:
    result = await db.execute(
        select(Purchase).where(
            Purchase.id == purchase_id, Purchase.user_id == current_user.id
        )
    )
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")

    old_product = await db.execute(
        select(Product).where(Product.id == purchase.product_id)
    )
    old_product = old_product.scalar_one_or_none()

    new_quantity = data.quantity if data.quantity is not None else purchase.quantity
    new_product_id = (
        data.product_id if data.product_id is not None else purchase.product_id
    )
    product_changed = new_product_id != purchase.product_id

    if product_changed:
        if old_product:
            old_product.stock_quantity -= purchase.quantity

        new_product = await db.execute(
            select(Product).where(Product.id == new_product_id)
        )
        new_product = new_product.scalar_one_or_none()
        if not new_product:
            raise HTTPException(status_code=404, detail="Product not found")
        new_product.stock_quantity += new_quantity
    else:
        quantity_diff = new_quantity - purchase.quantity
        if old_product:
            old_product.stock_quantity += quantity_diff

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(purchase, field, value)

    try:
        await db.commit()
        await db.refresh(purchase)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update purchase") from None
    return await _enrich_purchase(db, purchase)


async def delete_purchase(
    db: AsyncSession, purchase_id: uuid.UUID, current_user: User
) -> None:
    result = await db.execute(
        select(Purchase).where(
            Purchase.id == purchase_id, Purchase.user_id == current_user.id
        )
    )
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")

    product = await db.execute(
        select(Product).where(Product.id == purchase.product_id)
    )
    product = product.scalar_one_or_none()
    if product:
        product.stock_quantity -= purchase.quantity

    try:
        await db.delete(purchase)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete purchase") from None
