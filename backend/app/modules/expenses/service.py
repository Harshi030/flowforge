import uuid
import math
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.modules.expenses.models import Expense
from app.modules.expenses.repository import ExpenseRepository
from app.modules.expenses.schemas import CreateExpenseRequest
from app.modules.audit import service as audit_service

class ExpenseNotFoundError(Exception):
  pass

class InvalidExpenseStateError(Exception):
  pass

class ExpenseSelfApprovalError(Exception):
  pass

class ExpenseSelfRejectError(Exception):
  pass

def create_expense(
  session: Session,
  user_id: uuid.UUID,
  tenant_id: uuid.UUID,
  data: CreateExpenseRequest
) -> Expense: 
  
  try:
    expense_repository = ExpenseRepository(session)
    
    expense = expense_repository.create(
      tenant_id=tenant_id,
      user_id=user_id,
      amount=data.amount,
      currency=data.currency,
      description=data.description,
      category=data.category,
    )
    
    details={
        "status": "draft",
        "amount": str(expense.amount),
        "currency": expense.currency,
    }
    
    audit_service.create_audit_log(
      session=session,
      tenant_id=tenant_id,
      user_id=user_id,
      action="EXPENSE_CREATED",
      entity_type="expense",
      entity_id=expense.id,
      details=details
    )
    
    session.commit()
    
    return expense
  except Exception:
    session.rollback()
    raise
  
def get_expenses(
  session: Session,
  tenant_id: uuid.UUID,
  user_id: uuid.UUID,
  permissions: set[str],
  page: int,
  page_size: int
) : 
  
  expense_repository = ExpenseRepository(session)
  
  can_read_all = "expense:read:all" in permissions
  can_read_approved = "expense:read:approved" in permissions
  
  expenses, total = expense_repository.get_expenses(
    tenant_id=tenant_id,
    page=page,
    page_size=page_size,
    user_id=None if can_read_all else user_id,
    status="approved" if can_read_approved and not can_read_all else None
  )
  
  total_pages = math.ceil(total / page_size) if total else 0
  
  return {
    "items": expenses,
    "page": page,
    "page_size": page_size,
    "total": total,
    "total_pages": total_pages,
  }
  
def get_expense(
  session: Session,
  expense_id: uuid.UUID,
  tenant_id: uuid.UUID,
  user_id: uuid.UUID,
  permissions: set[str]
) -> Expense:
  expense_repository = ExpenseRepository(session)
  
  expense = expense_repository.get_by_id_and_tenant(
    expense_id=expense_id,
    tenant_id=tenant_id
  )
  
  if expense is None:
    raise ExpenseNotFoundError()
  
  if "expense:read:all" in permissions:
    return expense
  
  if "expense:read:approved" in permissions:
    if expense.status != "approved":
      raise ExpenseNotFoundError()
    return expense

  if expense.user_id != user_id:
    raise ExpenseNotFoundError()

  return expense

def submit_expense(
  session: Session,
  expense_id: uuid.UUID,
  tenant_id: uuid.UUID,
  user_id: uuid.UUID
) -> Expense:
  try:
    expense_repository = ExpenseRepository(session)

    expense = expense_repository.get_by_id_and_tenant(
      expense_id=expense_id,
      tenant_id=tenant_id
    )

    if expense is None:
      raise ExpenseNotFoundError()

    if expense.user_id != user_id:
      raise ExpenseNotFoundError()

    if expense.status != "draft":
      raise InvalidExpenseStateError()

    previous_status = expense.status
    
    expense.status = "submitted"
    expense.submitted_at = datetime.now(timezone.utc)

    expense_repository.update(expense)
    
    details ={
      "previous_status": previous_status,
      "new_status": expense.status
    }
    
    audit_service.create_audit_log(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        action="EXPENSE_SUBMITTED",
        entity_type="expense",
        entity_id=expense.id,
        details=details
    )
    
    session.commit()

    return expense
  
  except Exception:
    session.rollback()
    raise

def approve_expense(
  session: Session,
  expense_id: uuid.UUID,
  tenant_id: uuid.UUID,
  approver_id: uuid.UUID
) -> Expense:
  
  try:
    expense_repository = ExpenseRepository(session)
    
    expense = expense_repository.get_by_id_and_tenant(
      expense_id=expense_id,
      tenant_id=tenant_id
    )
    
    if expense is None:
      raise ExpenseNotFoundError()
    
    if expense.status != "submitted":
      raise InvalidExpenseStateError()
    
    if expense.user_id == approver_id:
      raise ExpenseSelfApprovalError()
    
    previous_status = expense.status
    
    expense.status = "approved"
    expense.approved_at = datetime.now(timezone.utc)
    
    expense_repository.update(expense)
    
    details={
        "previous_status": previous_status,
        "new_status": expense.status,
    }
    
    audit_service.create_audit_log(
      session=session,
      tenant_id=tenant_id,
      user_id=approver_id,
      action="EXPENSE_APPROVED",
      entity_type="expense",
      entity_id=expense.id,
      details=details
    )
    
    session.commit()
    
    return expense
  except Exception:
    session.rollback()
    raise

def reject_expense(
  session: Session,
  expense_id: uuid.UUID,
  tenant_id: uuid.UUID,
  rejecter_id: uuid.UUID,
  reason: str
) -> Expense:
  try:
    expense_repository = ExpenseRepository(session)
    
    expense = expense_repository.get_by_id_and_tenant(
      expense_id=expense_id,
      tenant_id=tenant_id
    )
    
    if expense is None:
      raise ExpenseNotFoundError()
    
    if expense.status != "submitted":
      raise InvalidExpenseStateError()
    
    if expense.user_id == rejecter_id:
      raise ExpenseSelfRejectError()
    
    previous_status = expense.status
    
    expense.status = "rejected"
    expense.rejection_reason = reason
    expense.rejected_at = datetime.now(timezone.utc)
    
    expense_repository.update(expense)
    
    details={
        "previous_status": previous_status,
        "new_status": expense.status,
        "reason": reason,
    }
    
    audit_service.create_audit_log(
      session=session,
      tenant_id=tenant_id,
      user_id=rejecter_id,
      action="EXPENSE_REJECTED",
      entity_type="expense",
      entity_id=expense.id,
      details=details
    )
    
    session.commit()
    
    return expense
      
  except Exception:
    session.rollback()
    raise
  
  
  