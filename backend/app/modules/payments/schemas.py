import uuid
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict

class CreatePaymentRequest(BaseModel):
  expense_id: uuid.UUID

class CreatePaymentResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)
  
  id: uuid.UUID
  expense_id: uuid.UUID
  amount: Decimal
  currency: str
  status: str
  created_at: datetime
  
class GetPaymentResponse(BaseModel):
  model_config = ConfigDict(from_attributes=True)
  
  id: uuid.UUID
  tenant_id: uuid.UUID
  expense_id: uuid.UUID
  amount: Decimal
  currency: str
  status: str
  paid_at: datetime
  created_at: uuid
  
class PaginatedPaymentsResponse(BaseModel):
  items: list[GetPaymentResponse]
  page: int
  page_size: int
  total: int
  total_pages: int