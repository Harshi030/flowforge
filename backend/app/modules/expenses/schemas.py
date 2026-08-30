import uuid
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime

class CreateExpenseRequest(BaseModel):
  amount: Decimal = Field(gt=0 ,decimal_places=2)
  currency: str = Field(min_length=3, max_length=3)
  description: str = Field(min_length=1, max_length=500)
  category: str = Field(min_length=1, max_length=50)
  
class CreateExpenseResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)
  
  id: uuid.UUID
  tenant_id: uuid.UUID
  user_id: uuid.UUID
  amount: Decimal
  currency: str
  description: str
  category: str
  status: str
  
class GetExpensesResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)
  
  id: uuid.UUID
  tenant_id: uuid.UUID
  user_id: uuid.UUID
  amount: Decimal
  currency: str
  description: str
  category: str
  status: str
  rejection_reason: str | None
  submitted_at: datetime | None
  approved_at: datetime | None
  rejected_at: datetime | None

class PaginatedExpensesResponse(BaseModel):
  items: list[GetExpensesResponse]
  page: int
  page_size: int
  total: int
  total_pages: int
  
class RejectExpenseRequest(BaseModel):
  reason: str = Field(min_length=1, max_length=500)