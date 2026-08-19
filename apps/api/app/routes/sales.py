import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.pagination import Page
from app.schemas.sale import SaleCreate, SaleResponse, SaleUpdate
from app.services import sale as sale_service

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("", response_model=Page[SaleResponse])
async def list_sales(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    items, total = await sale_service.list_sales(
        db, current_user, limit=limit, offset=offset
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await sale_service.get_sale(db, sale_id, current_user)


@router.post("", response_model=SaleResponse, status_code=201)
async def create_sale(
    data: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await sale_service.create_sale(db, data, current_user)


@router.put("/{sale_id}", response_model=SaleResponse)
async def update_sale(
    sale_id: uuid.UUID,
    data: SaleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await sale_service.update_sale(db, sale_id, data, current_user)


@router.delete("/{sale_id}", status_code=204)
async def delete_sale(
    sale_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await sale_service.delete_sale(db, sale_id, current_user)
