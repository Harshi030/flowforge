import uuid
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.modules.expenses.models import Expense

class ExpenseRepository:
  def __init__(self, session: Session):
    self.session = session
    
  def create(
    self,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    amount: Decimal,
    currency: str,
    description: str,
    category: str
  ) -> Expense:
    expense = Expense(
      tenant_id=tenant_id,
      user_id=user_id,
      amount=amount,
      currency=currency,
      description=description,
      category=category
    )
    
    self.session.add(expense)
    
    self.session.flush()
    
    return expense
  
  def get_by_id_and_tenant(
    self,
    expense_id: uuid.UUID,
    tenant_id: uuid.UUID
  )  -> Expense | None:
    return self.session.execute(
       select(Expense).where(Expense.id == expense_id,Expense.tenant_id == tenant_id)
    ).scalar_one_or_none()
    
  def get_expenses(
    self,
    tenant_id: uuid.UUID,
    page: int,
    page_size:int,
    user_id: uuid.UUID | None = None,
    status: str | None = None
  ) -> tuple[list[Expense], int]:
    offset = (page - 1) * page_size
    
    query = (
      select(Expense)
      .where(Expense.tenant_id == tenant_id)
    )

    count_query = (
      select(func.count(Expense.id))
      .where(Expense.tenant_id == tenant_id)
    )
    
    if user_id is not None:
      query = query.where(
        Expense.user_id == user_id
      )

      count_query = count_query.where(
        Expense.user_id == user_id
      )
    
    if status is not None:
      query = query.where(
        Expense.status == status
      )
      
      count_query = count_query.where(
        Expense.status == status
      )

    query = (
      query
      .order_by(Expense.created_at.desc())
      .offset(offset)
      .limit(page_size)
    )

    rows = self.session.execute(query).scalars().all()

    total = self.session.execute(
      count_query
    ).scalar_one()

    return rows, total
  
  def update(
    self,
    expense: Expense
  ) -> None:
    self.session.add(expense)
    self.session.flush()