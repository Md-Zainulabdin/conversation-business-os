from datetime import datetime

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    color: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
