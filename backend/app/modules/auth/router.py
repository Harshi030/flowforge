from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.modules.auth import service
from app.modules.auth.schemas import RegisterTenantRequest, RegisterTenantResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", response_model=RegisterTenantResponse, status_code=201,)
def register_tenant(
    data: RegisterTenantRequest,
    session: Session = Depends(get_db_session),
):
    try:
        tenant,user = service.register_tenant(session, data)
    except service.SlugAlreadyExistsError:
      raise HTTPException(status_code=409, detail="Company name already taken")
    return RegisterTenantResponse(tenant_id=tenant.id, user_id=user.id, slug=tenant.slug)