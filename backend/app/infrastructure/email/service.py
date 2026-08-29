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
    
    