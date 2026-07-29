from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import category as category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await category_service.list_categories(db)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await category_service.get_category(db, category_id)


@router.post("/", response_model=CategoryResponse, status_code=201)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await category_service.create_category(db, data)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await category_service.update_category(db, category_id, data)


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await category_service.delete_category(db, category_id)
