import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class GetAuditLogResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)
  
  tenant_id: uuid.UUID
  user_id: uuid.UUID
  action: str
  entity_type: str
  entity_id: uuid.UUID
  details: dict | None
  created_at: datetime
  
class PaginatedAuditLogResponse(BaseModel):
  items: list[GetAuditLogResponse]
  page: int
  page_size: int
  total: int
  total_pages: int