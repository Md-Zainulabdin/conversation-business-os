import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.product import Product
from app.models.sale import Sale
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleUpdate


async def _enrich_sales(db: AsyncSession, sales: list[Sale]) -> list[dict]:
    if not sales:
        return []

    product_ids = {sale.product_id for sale in sales}
    product_names: dict[uuid.UUID, str] = {}
    product_result = await db.execute(
        select(Product.id, Product.name).where(Product.id.in_(product_ids))
    )
    product_names.update(product_result.all())

    customer_ids = {sale.customer_id for sale in sales if sale.customer_id}
    customer_names: dict[uuid.UUID, str] = {}
    if customer_ids:
        customer_result = await db.execute(
            select(Customer.id, Customer.name).where(Customer.id.in_(customer_ids))
        )
        customer_names.update(customer_result.all())

    return [
        {
            **{c.name: getattr(sale, c.name) for c in sale.__table__.columns},
            "product_name": product_names.get(sale.product_id, "Unknown"),
            "customer_name": (
                customer_names.get(sale.customer_id) if sale.customer_id else None
            ),
        }
        for sale in sales
    ]


async def _enrich_sale(db: AsyncSession, sale: Sale) -> dict:
    return (await _enrich_sales(db, [sale]))[0]


async def list_sales(db: AsyncSession, current_user: User) -> list[dict]:
    result = await db.execute(
        select(Sale)
        .where(Sale.user_id == current_user.id)
        .order_by(Sale.sale_date.desc())
    )
    sales = list(result.scalars().all())
    return await _enrich_sales(db, sales)


async def get_sale(
    db: AsyncSession, sale_id: uuid.UUID, current_user: User
) -> dict:
    result = await db.execute(
        select(Sale).where(Sale.id == sale_id, Sale.user_id == current_user.id)
    )
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return await _enrich_sale(db, sale)


async def create_sale(
    db: AsyncSession, data: SaleCreate, current_user: User
) -> dict:
    product = await db.execute(
        select(Product).where(Product.id == data.product_id)
    )
    product = product.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock_quantity < data.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {product.stock_quantity}, requested: {data.quantity}",
        )

    sale = Sale(**data.model_dump(), user_id=current_user.id)
    product.stock_quantity -= data.quantity

    db.add(sale)
    try:
        await db.commit()
        await db.refresh(sale)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create sale") from None
    return await _enrich_sale(db, sale)


async def update_sale(
    db: AsyncSession, sale_id: uuid.UUID, data: SaleUpdate, current_user: User
) -> dict:
    result = await db.execute(
        select(Sale).where(Sale.id == sale_id, Sale.user_id == current_user.id)
    )
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    old_product = await db.execute(
        select(Product).where(Product.id == sale.product_id)
    )
    old_product = old_product.scalar_one_or_none()

    new_quantity = data.quantity if data.quantity is not None else sale.quantity
    new_product_id = (
        data.product_id if data.product_id is not None else sale.product_id
    )
    product_changed = new_product_id != sale.product_id

    if product_changed:
        if old_product:
            old_product.stock_quantity += sale.quantity

        new_product = await db.execute(
            select(Product).where(Product.id == new_product_id)
        )
        new_product = new_product.scalar_one_or_none()
        if not new_product:
            raise HTTPException(status_code=404, detail="Product not found")
        if new_product.stock_quantity < new_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {new_product.stock_quantity}, requested: {new_quantity}",
            )
        new_product.stock_quantity -= new_quantity
    else:
        quantity_diff = new_quantity - sale.quantity
        if quantity_diff > 0 and old_product:
            if old_product.stock_quantity < quantity_diff:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock. Available: {old_product.stock_quantity}, need extra: {quantity_diff}",
                )
            old_product.stock_quantity -= quantity_diff
        elif quantity_diff < 0 and old_product:
            old_product.stock_quantity += abs(quantity_diff)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sale, field, value)

    try:
        await db.commit()
        await db.refresh(sale)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update sale") from None
    return await _enrich_sale(db, sale)


async def delete_sale(
    db: AsyncSession, sale_id: uuid.UUID, current_user: User
) -> None:
    result = await db.execute(
        select(Sale).where(Sale.id == sale_id, Sale.user_id == current_user.id)
    )
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    product = await db.execute(select(Product).where(Product.id == sale.product_id))
    product = product.scalar_one_or_none()
    if product:
        product.stock_quantity += sale.quantity

    try:
        await db.delete(sale)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete sale") from None
