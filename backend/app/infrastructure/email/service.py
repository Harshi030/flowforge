from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from app.infrastructure.email.provider import EmailProvider
from app.core.config import Settings

settings = Settings()

TEMPLATE_DIR = Path(__file__).parent / "templates"

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR)
)

class EmailService:
  def __init__(self, provider: EmailProvider):
    self.provider = provider
    
  def send_registration_approval(
    self,
    to: str,
    company_name: str,
    email: str,
    full_name: str,
    approval_token: str,
  ) -> None: 
    template = jinja_env.get_template(
      "registration_approval.html"
    )
    
    approval_url = (
        f"{settings.backend_url}"
        f"/api/v1/registration/approve"
        f"?token={approval_token}"
    )
    
    html = template.render(
      company_name=company_name,
      email=email,
      full_name=full_name,
      approval_url=approval_url,
      expiry_days=settings.registration_approval_expire_days,
    )
    
    self.provider.send(
      to=to,
      subject="New Tenant Registration Requires Approval",
      html=html
    )
    
  def send_expense_submitted(
    self,
    to: str,
    recipient_name: str,
    employee_name: str,
    amount: str,
    currency: str,
    description: str,
  ) -> None:
    template = jinja_env.get_template(
      "expense_submitted.html"
    )
    
    html = template.render(
      recipient_name=recipient_name,
      employee_name=employee_name,
      amount=amount,
      currency=currency,
      description=description,
    )
    
    self.provider.send(
        to=to,
        subject="Expense Requires Approval",
        html=html,
    )
      
  def send_expense_approved(
    self,
    to: str,
    employee_name: str,
    amount: str,
    currency: str,
  ) -> None:
    
    template = jinja_env.get_template(
      "expense_approved.html"
    )
    
    html = template.render(
      employee_name=employee_name,
      amount=amount,
      currency=currency,
    )
    
    self.provider.send(
      to=to,
      subject="Expense Approved",
      html=html,
    )
    
  def send_expense_rejected(
    self,
    to: str,
    employee_name: str,
    amount: str,
    currency: str,
    rejection_reason: str,
  ) -> None:

    template = jinja_env.get_template(
      "expense_rejected.html"
    )

    html = template.render(
      employee_name=employee_name,
      amount=amount,
      currency=currency,
      rejection_reason=rejection_reason,
    )

    self.provider.send(
      to=to,
      subject="Expense Rejected",
      html=html,
    )
    
  def send_payment_paid(
    self,
    to: str,
    employee_name: str,
    amount: str,
    currency: str,
  ) -> None:

    template = jinja_env.get_template(
      "payment_paid.html"
    )

    html = template.render(
      employee_name=employee_name,
      amount=amount,
      currency=currency,
    )

    self.provider.send(
      to=to,
      subject="Expense Payment Completed",
      html=html,
    )
  
  def send_expense_ready_for_payment(
    self,
    to: str,
    recipient_name: str,
    employee_name: str,
    amount: str,
    currency: str,
    description: str,
) -> None:
    template = jinja_env.get_template(
      "expense_ready_for_payment.html"
    )

    html = template.render(
      recipient_name=recipient_name,
      employee_name=employee_name,
      amount=amount,
      currency=currency,
      description=description,
    )

    self.provider.send(
      to=to,
      subject="Approved Expense Ready for Payment",
      html=html,
    )
    