import uuid
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.modules.payments.models import Payment

class PaymentRepository:
  def __init__(self, session: Session):
    self.session = session
    
  def create(
    self,
    tenant_id: uuid.UUID,
    expense_id: uuid.UUID,
    amount: Decimal,
    currency: str,
    created_by: uuid.UUID
  ) -> Payment:
    
    payment = Payment(
      tenant_id=tenant_id,
      expense_id=expense_id,
      amount=amount,
      currency=currency,
      created_by=created_by
    )
    
    self.session.add(payment)
    
    self.session.flush()
    
    return payment
  
  def get_by_expense_id(
    self,
    expense_id: uuid.UUID,
    tenant_id: uuid.UUID
  ) -> Payment | None:
    return self.session.execute(
      select(Payment)
      .where(
        Payment.expense_id == expense_id,
        Payment.tenant_id == tenant_id
      )
    ).scalar_one_or_none()
    
  def get_by_id_and_tenant(
    self,
    payment_id: uuid.UUID,
    tenant_id: uuid.UUID
  ) -> Payment | None:
    return self.session.execute(
      select(Payment)
      .where(
        Payment.id == payment_id,
        Payment.tenant_id == tenant_id
      )
    ).scalar_one_or_none()
    
  def update(
    self,
    payment: Payment
  ) -> None:
    self.session.add(payment)
    self.session.flush()
    
  def get_payments(
    self,
    tenant_id: uuid.UUID,
    page: int,
    page_size: int,
    status: str | None = None
  ) -> tuple[list[Payment], int]:
    
    offset = (page - 1) * page_size
    
    query = (
      select(Payment)
      .where(Payment.tenant_id == tenant_id)
    )
    
    count_query = (
      select(func.count(Payment.id))
      .where(Payment.tenant_id == tenant_id)
    )
    
    if status is not None:
      query = query.where(
        Payment.status == status
      )
      
      count_query = count_query.where(
        Payment.status == status
      )
      
    query = (
      query
      .order_by(Payment.created_at.desc())
      .offset(offset)
      .limit(page_size)
    )
    
    rows = self.session.execute(query).scalars().all()
    
    total = self.session.execute(count_query).scalar_one()
    
    return rows, total
  