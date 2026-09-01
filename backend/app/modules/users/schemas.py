import uuid

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    tenant_id: uuid.UUID
    is_active: bool

    model_config = {"from_attributes": True}


class AcceptInvitationRequest(BaseModel):
    token: str
    password: str


class AcceptInvitationResponse(BaseModel):
    message: str


class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    role_id: uuid.UUID


class CreateUserResponse(BaseModel):
    user_id: uuid.UUID
    message: str
    invitation_token: str | None = None


class GetUsersResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    is_active: bool
    roles: list[str]


class PaginatedUsersResponse(BaseModel):
    items: list[GetUsersResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class UpdateUserRequest(BaseModel):
    full_name: str | None = None
    role_ids: list[uuid.UUID] | None = None
    is_active: bool | None = None


class UpdateUserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    is_active: bool
