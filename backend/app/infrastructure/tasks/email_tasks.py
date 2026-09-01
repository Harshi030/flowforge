from app.infrastructure.email.provider import ConsoleEmailProvider
from app.infrastructure.email.service import EmailService
from app.infrastructure.tasks.celery_app import celery_app


@celery_app.task
def send_registration_approval_email(
    to: str,
    company_name: str,
    email: str,
    full_name: str,
    approval_token: str,
):
    email_service = EmailService(ConsoleEmailProvider())

    email_service.send_registration_approval(
        to=to,
        company_name=company_name,
        email=email,
        full_name=full_name,
        approval_token=approval_token,
    )


@celery_app.task
def send_expense_submitted_email(
    to: str,
    recipient_name: str,
    employee_name: str,
    amount: str,
    currency: str,
    description: str,
):
    email_service = EmailService(ConsoleEmailProvider())

    email_service.send_expense_submitted(
        to=to,
        recipient_name=recipient_name,
        employee_name=employee_name,
        amount=amount,
        currency=currency,
        description=description,
    )


@celery_app.task
def send_expense_approved_email(
    to: str,
    employee_name: str,
    amount: str,
    currency: str,
):
    email_service = EmailService(ConsoleEmailProvider())

    email_service.send_expense_approved(
        to=to, employee_name=employee_name, amount=amount, currency=currency
    )


@celery_app.task
def send_expense_rejected_email(
    to: str,
    employee_name: str,
    amount: str,
    currency: str,
    rejection_reason: str,
):
    email_service = EmailService(ConsoleEmailProvider())

    email_service.send_expense_rejected(
        to=to,
        employee_name=employee_name,
        amount=amount,
        currency=currency,
        rejection_reason=rejection_reason,
    )


@celery_app.task
def send_payment_paid_email(
    to: str,
    employee_name: str,
    amount: str,
    currency: str,
):
    email_service = EmailService(ConsoleEmailProvider())

    email_service.send_payment_paid(
        to=to,
        employee_name=employee_name,
        amount=amount,
        currency=currency,
    )


@celery_app.task
def send_expense_ready_for_payment_email(
    to: str,
    recipient_name: str,
    employee_name: str,
    amount: str,
    currency: str,
    description: str,
):
    email_service = EmailService(ConsoleEmailProvider())

    email_service.send_expense_ready_for_payment(
        to=to,
        recipient_name=recipient_name,
        employee_name=employee_name,
        amount=amount,
        currency=currency,
        description=description,
    )
