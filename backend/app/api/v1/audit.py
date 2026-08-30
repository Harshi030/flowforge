import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.modules.rbac.dependencies import requires_permission, AuthContext
from app.modules.audit.schemas import PaginatedAuditLogResponse
from app.modules.audit import service as audit_service

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

@router.get(
  "/logs",
  response_model=PaginatedAuditLogResponse,
  status_code=200
)
def get_audit_logs(
  page: int = Query(1, ge=1),
  page_size: int = Query(20, ge=1, le=100),
  action: str | None = None,
  entity_type: str | None = None,
  user_id: uuid.UUID | None = None,
  auth: AuthContext = Depends(
    requires_permission("audit:read")
  )
):
  return audit_service.get_audit_logs(
    session=auth.session,
    tenant_id=auth.user.tenant_id,
    page=page,
    page_size=page_size,
    action=action,
    entity_type=entity_type,
    user_id=user_id,
  )