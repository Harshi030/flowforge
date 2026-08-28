import uuid

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    tenant_id: uuid.UUID
    is_active: bool

    model_config = {"from_attributes": True}