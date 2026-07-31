import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.purchase import PurchaseCreate, PurchaseResponse, PurchaseUpdate
from app.services import purchase as purchase_service

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.get("", response_model=list[PurchaseResponse])
async def list_purchases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await purchase_service.list_purchases(db, current_user)


@router.get("/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase(
    purchase_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await purchase_service.get_purchase(db, purchase_id, current_user)


@router.post("", response_model=PurchaseResponse, status_code=201)
async def create_purchase(
    data: PurchaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await purchase_service.create_purchase(db, data, current_user)


@router.put("/{purchase_id}", response_model=PurchaseResponse)
async def update_purchase(
    purchase_id: uuid.UUID,
    data: PurchaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await purchase_service.update_purchase(db, purchase_id, data, current_user)


@router.delete("/{purchase_id}", status_code=204)
async def delete_purchase(
    purchase_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await purchase_service.delete_purchase(db, purchase_id, current_user)
