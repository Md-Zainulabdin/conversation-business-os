import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleUpdate


def _sale_dict(sale: Sale, product_names: dict, customer_names: dict) -> dict:
    return {
        "id": sale.id,
        "customer_id": sale.customer_id,
        "customer_name": (
            customer_names.get(sale.customer_id) if sale.customer_id else None
        ),
        "total_amount": sale.total_amount,
        "sale_date": sale.sale_date,
        "notes": sale.notes,
        "created_at": sale.created_at,
        "updated_at": sale.updated_at,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product_names.get(item.product_id, "Unknown"),
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_amount": item.total_amount,
            }
            for item in sale.items
        ],
    }


async def _enrich_sales(db: AsyncSession, sales: list[Sale]) -> list[dict]:
    if not sales:
        return []

    product_ids = {
        item.product_id for sale in sales for item in sale.items
    }
    product_names: dict[uuid.UUID, str] = {}
    if product_ids:
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

    return [_sale_dict(sale, product_names, customer_names) for sale in sales]


async def _enrich_sale(db: AsyncSession, sale: Sale) -> dict:
    return (await _enrich_sales(db, [sale]))[0]


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


async def _validate_sale_items(
    db: AsyncSession, items: list, current_user: User
) -> dict[uuid.UUID, Product]:
    product_ids = {item.product_id for item in items}
    products = await _load_products(db, product_ids, current_user)
    for item in items:
        product = products.get(item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient stock for {product.name}. "
                    f"Available: {product.stock_quantity}, requested: {item.quantity}"
                ),
            )
    return products


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


async def _validate_customer(
    db: AsyncSession, customer_id: uuid.UUID | None, current_user: User
) -> None:
    if customer_id is None:
        return
    result = await db.execute(
        select(Customer.id).where(
            Customer.id == customer_id, Customer.user_id == current_user.id
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Customer not found")


async def create_sale(
    db: AsyncSession, data: SaleCreate, current_user: User
) -> dict:
    products = await _validate_sale_items(db, data.items, current_user)
    await _validate_customer(db, data.customer_id, current_user)

    total_amount = sum(
        (item.total_amount for item in data.items), Decimal("0")
    )
    sale = Sale(
        customer_id=data.customer_id,
        total_amount=total_amount,
        sale_date=data.sale_date,
        notes=data.notes,
        user_id=current_user.id,
    )
    db.add(sale)
    await db.flush()

    for item in data.items:
        db.add(
            SaleItem(
                sale_id=sale.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_amount=item.total_amount,
            )
        )
        products[item.product_id].stock_quantity -= item.quantity

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

    if data.customer_id is not None:
        await _validate_customer(db, data.customer_id, current_user)

    if data.items is not None:
        if not data.items:
            raise HTTPException(
                status_code=400, detail="A sale needs at least one product"
            )

        old_stock: dict[uuid.UUID, int] = {}
        for item in sale.items:
            old_stock[item.product_id] = (
                old_stock.get(item.product_id, 0) + item.quantity
            )
        old_products = await _load_products(db, set(old_stock), current_user)
        for product_id, qty in old_stock.items():
            product = old_products.get(product_id)
            if product:
                product.stock_quantity += qty

        products = await _validate_sale_items(db, data.items, current_user)
        for item in data.items:
            products[item.product_id].stock_quantity -= item.quantity

        for item in list(sale.items):
            await db.delete(item)
        await db.flush()
        for item in data.items:
            db.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_amount=item.total_amount,
                )
            )
        sale.total_amount = sum(
            (item.total_amount for item in data.items), Decimal("0")
        )

    update_data = data.model_dump(exclude_unset=True, exclude={"items"})
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

    stock: dict[uuid.UUID, int] = {}
    for item in sale.items:
        stock[item.product_id] = stock.get(item.product_id, 0) + item.quantity
    products = await _load_products(db, set(stock), current_user)
    for product_id, qty in stock.items():
        product = products.get(product_id)
        if product:
            product.stock_quantity += qty

    try:
        await db.delete(sale)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete sale") from None