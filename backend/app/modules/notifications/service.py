import uuid

from sqlalchemy.orm import Session

from app.infrastructure.tasks.email_tasks import (
    send_expense_approved_email,
    send_expense_ready_for_payment_email,
    send_expense_rejected_email,
    send_expense_submitted_email,
    send_payment_paid_email,
)
from app.modules.expenses.models import Expense
from app.modules.rbac.repository import RBACRepository
from app.modules.users.repository import UserRepository


def get_expense_approvers(
    session: Session,
    tenant_id: uuid.UUID,
):
    rbac_repository = RBACRepository(session)

    return rbac_repository.get_users_with_permission(
        tenant_id=tenant_id,
        permission="expense:approve",
    )


def get_payment_processors(
    session: Session,
    tenant_id: uuid.UUID,
):
    rbac_repository = RBACRepository(session)

    return rbac_repository.get_users_with_permission(
        tenant_id=tenant_id,
        permission="payment:create",
    )


def notify_expense_submitted(session: Session, expense: Expense):
    approvers = get_expense_approvers(session=session, tenant_id=expense.tenant_id)

    user_repository = UserRepository(session)

    employee = user_repository.get_by_id(expense.user_id)

    if employee is None:
        return

    for approver in approvers:
        send_expense_submitted_email.delay(
            to=approver.email,
            recipient_name=approver.full_name,
            employee_name=employee.full_name,
            amount=str(expense.amount),
            currency=expense.currency,
            description=expense.description,
        )


def notify_expense_approved(session: Session, expense: Expense):
    user_repository = UserRepository(session)

    employee = user_repository.get_by_id(expense.user_id)

    if employee is None:
        return

    send_expense_approved_email.delay(
        to=employee.email,
        employee_name=employee.full_name,
        amount=str(expense.amount),
        currency=expense.currency,
    )


def notify_expense_rejected(session: Session, expense: Expense):
    user_repository = UserRepository(session)

    employee = user_repository.get_by_id(expense.user_id)

    if employee is None:
        return

    send_expense_rejected_email.delay(
        to=employee.email,
        employee_name=employee.full_name,
        amount=str(expense.amount),
        currency=expense.currency,
        rejection_reason=expense.rejection_reason,
    )


def notify_payment_paid(session: Session, expense: Expense):
    user_repository = UserRepository(session)

    employee = user_repository.get_by_id(expense.user_id)

    if employee is None:
        return

    send_payment_paid_email.delay(
        to=employee.email,
        employee_name=employee.full_name,
        amount=str(expense.amount),
        currency=expense.currency,
    )


def notify_finance_expense_approved(
    session: Session,
    expense: Expense,
):
    finance_users = get_payment_processors(
        session=session,
        tenant_id=expense.tenant_id,
    )

    user_repository = UserRepository(session)

    employee = user_repository.get_by_id(expense.user_id)

    if employee is None:
        return

    for finance_user in finance_users:
        send_expense_ready_for_payment_email.delay(
            to=finance_user.email,
            recipient_name=finance_user.full_name,
            employee_name=employee.full_name,
            amount=str(expense.amount),
            currency=expense.currency,
            description=expense.description,
        )
