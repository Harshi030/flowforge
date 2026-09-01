import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from app.modules.payments import service as payment_service
from app.modules.payments.schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    GetPaymentResponse,
    PaginatedPaymentsResponse,
)
from app.modules.rbac.dependencies import AuthContext, requires_permission

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.post("/", response_model=CreatePaymentResponse, status_code=201)
def create_payment(
    data: CreatePaymentRequest,
    auth: AuthContext = Depends(requires_permission("payment:create")),
):
    try:
        return payment_service.create_payment(
            session=auth.session,
            tenant_id=auth.user.tenant_id,
            expense_id=data.expense_id,
            created_by=auth.user.id,
        )
    except payment_service.ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="Expense not found")
    except payment_service.ExpenseNotApprovedError:
        raise HTTPException(
            status_code=400, detail="Only approved expenses can be paid"
        )
    except payment_service.PaymentAlreadyExistsError:
        raise HTTPException(
            status_code=409, detail="Payment already exists for this expense"
        )


@router.get("/", response_model=PaginatedPaymentsResponse, status_code=200)
def get_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    auth: AuthContext = Depends(requires_permission("payment:read")),
):
    return payment_service.get_payments(
        session=auth.session,
        tenant_id=auth.user.tenant_id,
        page=page,
        page_size=page_size,
        status=status,
    )


@router.get("/{payment_id}", response_model=GetPaymentResponse, status_code=200)
def get_payment(
    payment_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("payment:read")),
):
    try:
        return payment_service.get_payment(
            session=auth.session, tenant_id=auth.user.tenant_id, payment_id=payment_id
        )
    except payment_service.PaymentNotFoundError:
        raise HTTPException(status_code=404, detail="Payment not found")


@router.post("/{payment_id}/pay", response_model=GetPaymentResponse, status_code=200)
def pay(
    payment_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("payment:process")),
):
    try:
        return payment_service.pay(
            session=auth.session,
            tenant_id=auth.user.tenant_id,
            payment_id=payment_id,
            updated_by=auth.user.id,
        )
    except payment_service.PaymentNotFoundError:
        raise HTTPException(status_code=404, detail="Payment not found")
    except payment_service.InvalidPaymentStateError:
        raise HTTPException(
            status_code=400, detail="Only pending payments can be marked as paid"
        )
