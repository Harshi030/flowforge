import uuid
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.modules.audit.models import AuditLog 

class AuditLogRepository:
  def __init__(self, session: Session):
    self.session = session
    
  def create(
    self,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    details:dict | None = None
  ) -> AuditLog:
    audit_log = AuditLog(
      tenant_id=tenant_id,
      user_id=user_id,
      action=action,
      entity_type=entity_type,
      entity_id=entity_id,
      details=details
    )
    
    self.session.add(audit_log)
    
    self.session.flush()
    
    return audit_log
  
  def get_audit_logs(
    self,
    tenant_id: uuid.UUID,
    page: int,
    page_size: int,
    action: str | None = None,
    entity_type: str | None = None,
    user_id: uuid.UUID | None = None,
  ) -> tuple[list[AuditLog],int] :
    
    offset = (page - 1) * page_size
    
    query = (
      select(AuditLog)
      .where(AuditLog.tenant_id == tenant_id)
      .order_by(AuditLog.created_at.desc())
      .offset(offset)
      .limit(page_size)
    )
    
    count_query = (
      select(func.count(AuditLog.id))
      .where(AuditLog.tenant_id == tenant_id)
    )
    
    if action:
      query = query.where(AuditLog.action == action)
      count_query = query.where(AuditLog.action == action)
      
    if entity_type:
      query = query.where(AuditLog.entity_type == entity_type)
      count_query = query.where(AuditLog.entity_type == entity_type)
      
    if user_id:
      query = query.where(AuditLog.user_id == user_id)
      count_query = query.where(AuditLog.user_id == user_id)
    
    rows = self.session.execute(query).scalars().all()
    
    total = self.session.execute(count_query).scalar_one()
    
    return rows, total
    