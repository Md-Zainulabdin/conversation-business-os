import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.purchase import Purchase, PurchaseItem
from app.models.user import User
from app.schemas.purchase import PurchaseCreate, PurchaseUpdate


def _purchase_dict(purchase: Purchase, product_names: dict) -> dict:
    return {
        "id": purchase.id,
        "supplier_name": purchase.supplier_name,
        "total_amount": purchase.total_amount,
        "purchase_date": purchase.purchase_date,
        "notes": purchase.notes,
        "created_at": purchase.created_at,
        "updated_at": purchase.updated_at,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product_names.get(item.product_id, "Unknown"),
                "quantity": item.quantity,
                "purchase_price": item.purchase_price,
                "total_amount": item.total_amount,
            }
            for item in purchase.items
        ],
    }


async def _enrich_purchases(
    db: AsyncSession, purchases: list[Purchase]
) -> list[dict]:
    if not purchases:
        return []

    product_ids = {
        item.product_id for purchase in purchases for item in purchase.items
    }
    product_names: dict[uuid.UUID, str] = {}
    if product_ids:
        product_result = await db.execute(
            select(Product.id, Product.name).where(Product.id.in_(product_ids))
        )
        product_names.update(product_result.all())

    return [_purchase_dict(purchase, product_names) for purchase in purchases]


async def _enrich_purchase(db: AsyncSession, purchase: Purchase) -> dict:
    return (await _enrich_purchases(db, [purchase]))[0]


async def _load_products(
    db: AsyncSession, product_ids: set[uuid.UUID], current_user: User
) -> dict[uuid.UUID, Product]:
    if not product_ids:
        return {}
    result = await db.execute(
        select(Product)
        .where(Product.id.in_(product_ids), Product.user_id == current_user.id)
        .with_for_update()
    )
    return {p.id: p for p in result.scalars().all()}


async def list_purchases(db: AsyncSession, current_user: User) -> list[dict]:
    result = await db.execute(
        select(Purchase)
        .where(Purchase.user_id == current_user.id)
        .order_by(Purchase.purchase_date.desc())
    )
    purchases = list(result.scalars().all())
    return await _enrich_purchases(db, purchases)


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
    product_ids = {item.product_id for item in data.items}
    products = await _load_products(db, product_ids, current_user)
    for item in data.items:
        if item.product_id not in products:
            raise HTTPException(status_code=404, detail="Product not found")

    total_amount = sum(
        (item.total_amount for item in data.items), Decimal("0")
    )
    purchase = Purchase(
        supplier_name=data.supplier_name,
        total_amount=total_amount,
        purchase_date=data.purchase_date,
        notes=data.notes,
        user_id=current_user.id,
    )
    db.add(purchase)
    await db.flush()

    for item in data.items:
        db.add(
            PurchaseItem(
                purchase_id=purchase.id,
                product_id=item.product_id,
                quantity=item.quantity,
                purchase_price=item.purchase_price,
                total_amount=item.total_amount,
            )
        )
        products[item.product_id].stock_quantity += item.quantity

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

    if data.items is not None:
        if not data.items:
            raise HTTPException(
                status_code=400, detail="A purchase needs at least one product"
            )

        old_stock: dict[uuid.UUID, int] = {}
        for item in purchase.items:
            old_stock[item.product_id] = (
                old_stock.get(item.product_id, 0) + item.quantity
            )
        old_products = await _load_products(db, set(old_stock), current_user)
        for product_id, qty in old_stock.items():
            product = old_products.get(product_id)
            if product:
                product.stock_quantity -= qty

        product_ids = {item.product_id for item in data.items}
        products = await _load_products(db, product_ids, current_user)
        for item in data.items:
            if item.product_id not in products:
                raise HTTPException(status_code=404, detail="Product not found")
            products[item.product_id].stock_quantity += item.quantity

        for item in list(purchase.items):
            await db.delete(item)
        await db.flush()
        for item in data.items:
            db.add(
                PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    purchase_price=item.purchase_price,
                    total_amount=item.total_amount,
                )
            )
        purchase.total_amount = sum(
            (item.total_amount for item in data.items), Decimal("0")
        )

    update_data = data.model_dump(exclude_unset=True, exclude={"items"})
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

    stock: dict[uuid.UUID, int] = {}
    for item in purchase.items:
        stock[item.product_id] = stock.get(item.product_id, 0) + item.quantity
    products = await _load_products(db, set(stock), current_user)
    for product_id, qty in stock.items():
        product = products.get(product_id)
        if product:
            product.stock_quantity -= qty

    try:
        await db.delete(purchase)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete purchase") from None