import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import (
    String,
    ForeignKey,
    Numeric,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import (
    Base,
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    CreatedByMixin,
    UpdatedByMixin
)

class Payment(
  Base,
  UUIDPrimaryKeyMixin,
  TimestampMixin,
  CreatedByMixin,
  UpdatedByMixin
):
  
  __tablename__ = "payments"
  
  tenant_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("tenants.id"),
    nullable=False
  )
  
  expense_id: Mapped[uuid.UUID] = mapped_column(
    ForeignKey("expenses.id"),
    nullable=False,
    unique=True
  )
  
  amount: Mapped[Decimal] = mapped_column(
    Numeric(12,2),
    nullable=False
  )
  
  currency: Mapped[str] = mapped_column(
    String(3),
    nullable=False
  )
  
  status: Mapped[str] = mapped_column(
    String(20),
    nullable=False,
    default="pending"
  )
  
  paid_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True
  )