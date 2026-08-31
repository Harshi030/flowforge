import uuid
import math
from sqlalchemy.orm import Session
from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditLogRepository

def create_audit_log(
  session: Session,
  tenant_id: uuid.UUID,
  user_id: uuid.UUID,
  action: str,
  entity_type: str,
  entity_id: uuid.UUID,
  details: dict | None = None
) -> AuditLog:
  audit_log_repository = AuditLogRepository(session)
  
  audit_log = audit_log_repository.create(
    tenant_id=tenant_id,
    user_id=user_id,
    action=action,
    entity_type=entity_type,
    entity_id=entity_id,
    details=details
  )
  
  return audit_log

def get_audit_logs(
  session: Session,
  tenant_id: uuid.UUID,
  page: int,
  page_size: int,
  action: str | None = None,
  entity_type: str | None = None,
  user_id: uuid.UUID | None = None,
):
  audit_log_repository = AuditLogRepository(session)
  
  rows, total = audit_log_repository.get_audit_logs(
    tenant_id=tenant_id,
    page=page,
    page_size=page_size,
    action=action,
    entity_type=entity_type,
    user_id=user_id
  )
  
  total_pages = math.ceil(total / page_size) if total else 0
  
  return {
    "items": rows,
    "page": page,
    "page_size": page_size,
    "total": total,
    "total_pages": total_pages,
  }
  
  