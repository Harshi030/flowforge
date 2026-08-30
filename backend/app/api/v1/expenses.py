import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from app.modules.rbac.dependencies import requires_permission, AuthContext
from app.modules.expenses import service as expense_service

from app.modules.expenses.schemas import CreateExpenseRequest, CreateExpenseResponse, PaginatedExpensesResponse, GetExpensesResponse, RejectExpenseRequest

router = APIRouter(prefix="/api/v1/expenses", tags=["expenses"])

@router.post(
  "/",
  response_model=CreateExpenseResponse,
  status_code=201
)
def create_expense(
  data: CreateExpenseRequest,
  auth: AuthContext = Depends(
    requires_permission("expense:create")
  )
):
  return expense_service.create_expense(
    session= auth.session,
    user_id=auth.user.id,
    tenant_id=auth.user.tenant_id,
    data=data
  )
  
@router.get(
  "/",
  response_model=PaginatedExpensesResponse,
  status_code=200
)
def get_expenses(
  page: int = Query(1, ge=1),
  page_size: int = Query(20, ge=1, le=100),
  auth: AuthContext = Depends(
      requires_permission("expense:read")
  ),
):
  return expense_service.get_expenses(
    session=auth.session,
    tenant_id=auth.user.tenant_id,
    user_id=auth.user.id,
    permissions=auth.permissions,
    page=page,
    page_size=page_size
  )

@router.get(
  "/{expense_id}",
  response_model=GetExpensesResponse,
  status_code=200
)
def get_expense(
  expense_id: uuid.UUID,
  auth: AuthContext = Depends(
    requires_permission("expense:read")
  )
):
  try:
    expense = expense_service.get_expense(
      session=auth.session,
      expense_id=expense_id,
      tenant_id=auth.user.tenant_id,
      user_id=auth.user.id,
      permissions=auth.permissions
    )
  except expense_service.ExpenseNotFoundError:
    raise HTTPException(
      status_code=404,
      detail="Expense not found"
    )
    
  return expense
  
@router.post(
  "/{expense_id}/submit",
  response_model=GetExpensesResponse,
  status_code=200
)
def submit_expense(
  expense_id: uuid.UUID,
  auth: AuthContext = Depends(
    requires_permission("expense:create")
  )
):
  try:
    expense = expense_service.submit_expense(
      session=auth.session,
      expense_id=expense_id,
      tenant_id=auth.user.tenant_id,
      user_id=auth.user.id
    )
  except expense_service.ExpenseNotFoundError:
    raise HTTPException(
      status_code=404,
      detail="Expense not found"
    )
  except expense_service.InvalidExpenseStateError:
    raise HTTPException(
      status_code=400,
      detail="Only draft expenses can be submitted"
    )
    
  return expense

@router.post(
  "/{expense_id}/approve",
  response_model=GetExpensesResponse,
  status_code=200
)
def approve_expense(
  expense_id: uuid.UUID,
  auth: AuthContext = Depends(
    requires_permission("expense:approve")
  )
):
  try:
    expense = expense_service.approve_expense(
      session=auth.session,
      expense_id=expense_id,
      tenant_id=auth.user.tenant_id,
      approver_id=auth.user.id
    )
  except expense_service.ExpenseNotFoundError:
    raise HTTPException(
      status_code=404,
      detail="Expense not found"
    )
  except expense_service.InvalidExpenseStateError:
    raise HTTPException(
      status_code=400,
      detail="Only submitted expenses can be approved"
    )
  except expense_service.ExpenseSelfApprovalError:
    raise HTTPException(
      status_code=400,
      detail="Creator cannot approve their own expense"
    )
  
  return expense

@router.post(
  "/{expense_id}/reject",
  response_model=GetExpensesResponse,
  status_code=200
)
def reject_expense(
  expense_id: uuid.UUID,
  data:RejectExpenseRequest,
  auth: AuthContext = Depends(
    requires_permission("expense:reject")
  )
):
  try:
    expense = expense_service.reject_expense(
      session=auth.session,
      expense_id=expense_id,
      tenant_id=auth.user.tenant_id,
      rejecter_id=auth.user.id,
      reason=data.reason
    )
  except expense_service.ExpenseNotFoundError:
    raise HTTPException(
      status_code=404,
      detail="Expense not found"
    )
  except expense_service.InvalidExpenseStateError:
    raise HTTPException(
      status_code=400,
      detail="Only submitted expenses can be rejected"
    )
  except expense_service.ExpenseSelfRejectError:
    raise HTTPException(
      status_code=400,
      detail="Creator cannot reject their own expense"
    )
  
  return expense
    