import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.schemas.validators import validate_required_str


class CustomerCreate(BaseModel):
    name: str
    phone: str
    address: str | None = None

    _validate_name = field_validator("name")(validate_required_str)
    _validate_phone = field_validator("phone")(validate_required_str)


class CustomerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None

    _validate_name = field_validator("name")(validate_required_str)
    _validate_phone = field_validator("phone")(validate_required_str)


class CustomerResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    address: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
