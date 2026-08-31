import uuid
import math

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.modules.payments.models import Payment
from app.modules.payments.repository import PaymentRepository
from app.modules.expenses.service import ExpenseNotFoundError
from app.modules.audit import service as audit_service
from app.modules.expenses.repository import ExpenseRepository
from app.modules.notifications import service as notification_service

class ExpenseNotApprovedError(Exception):
  pass

class PaymentAlreadyExistsError(Exception):
  pass

class PaymentNotFoundError(Exception):
  pass

class InvalidPaymentStateError(Exception):
  pass


def create_payment(
  session: Session,
  tenant_id: uuid.UUID,
  expense_id: uuid.UUID,
  created_by: uuid.UUID
) -> Payment:
  try:
    expense_repository = ExpenseRepository(session)
    
    expense = expense_repository.get_by_id_and_tenant(
      expense_id=expense_id,
      tenant_id=tenant_id
    ) 
    
    if expense is None:
      raise ExpenseNotFoundError()
    
    if expense.status != "approved":
      raise ExpenseNotApprovedError()
    
    payment_repository = PaymentRepository(session)
    
    existing_payment  = payment_repository.get_by_expense_id(
      expense_id=expense_id,
      tenant_id=tenant_id
    )
    
    if existing_payment  is not None:
      raise PaymentAlreadyExistsError()
    
    payment = payment_repository.create(
      tenant_id=tenant_id,
      expense_id=expense.id,
      amount=expense.amount,
      currency=expense.currency,
      created_by=created_by
    )
    
    details = {
      "status":"pending",
      "amount":str(expense.amount),
      "currency":expense.currency
    }
    
    audit_service.create_audit_log(
      session=session,
      tenant_id=tenant_id,
      user_id=created_by,
      action="PAYMENT_CREATED",
      entity_type="payment",
      entity_id=payment.id,
      details=details
    )
    
    session.commit()
    
    return payment
  except Exception:
    session.rollback()
    raise
  
def get_payments(
  session: Session,
  tenant_id: uuid.UUID,
  page: int,
  page_size: int,
  status: str | None
) :
  payment_repository = PaymentRepository(session)
  
  payments, total = payment_repository.get_payments(
    tenant_id=tenant_id,
    page=page,
    page_size=page_size,
    status=status
  )
  
  total_pages = math.ceil(total / page_size ) if total else 0
  
  return {
    "items": payments,
    "page": page,
    "page_size": page_size,
    "total": total,
    "total_pages": total_pages,
  }
  
def get_payment(
  session: Session,
  tenant_id: uuid.UUID,
  payment_id: uuid.UUID
) -> Payment:
  payment_repository = PaymentRepository(session)
  
  payment = payment_repository.get_by_id_and_tenant(
    payment_id=payment_id,
    tenant_id=tenant_id
  )
  
  if payment is None:
    raise PaymentNotFoundError()
  
  return payment

def pay(
  session: Session,
  tenant_id: uuid.UUID,
  payment_id: uuid.UUID,
  updated_by: uuid.UUID
) -> Payment:
  try:
    payment_repository = PaymentRepository(session)
    
    payment = payment_repository.get_by_id_and_tenant(
      payment_id=payment_id,
      tenant_id=tenant_id
    )
    
    if payment is None:
      raise PaymentNotFoundError()
    
    if payment.status != "pending":
      raise InvalidPaymentStateError()
    
    previous_status = payment.status
    
    payment.status = "paid"
    payment.paid_at = datetime.now(timezone.utc)
    payment.updated_by = updated_by
    payment.updated_at = datetime.now(timezone.utc)
    
    details = {
      "previous_status": previous_status,
      "new_status": payment.status
    }
    
    audit_service.create_audit_log(
      session=session,
      tenant_id=tenant_id,
      user_id=updated_by,
      action="PAYMENT_PAID",
      entity_type="payment",
      entity_id=payment.id,
      details=details
    )

    session.commit()
    
    expense_repository = ExpenseRepository(session)
        
    expense = expense_repository.get_by_id_and_tenant(
      expense_id=payment.expense_id,
      tenant_id=tenant_id
    ) 
    notification_service.notify_payment_paid(
      session=session,
      expense=expense
    )
        
    
    return payment
  except Exception:
    session.rollback()
    raise