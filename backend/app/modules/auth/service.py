import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.auth.schemas import RegisterTenantRequest
from app.modules.tenants.models import Tenant
from app.modules.users.models import User

class SlugAlreadyExistsError(Exception):
    pass
  
def _make_slug(company_name: str) -> str:
    slug = company_name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")
  
def register_tenant(session:Session,data:RegisterTenantRequest) -> tuple[Tenant, User]:
    slug = _make_slug(data.company_name)
    
    is_slug_exists = session.execute(
      select(Tenant).where(Tenant.slug == slug)
    ).scalar_one_or_none()
    
    if is_slug_exists:
        raise SlugAlreadyExistsError(f"Slug {slug} already exists.")
    
    tenant = Tenant(
      name= data.company_name,
      slug=slug
    )
    
    session.add(tenant)
    
    session.flush()
    
    user = User(
      tenant_id=tenant.id,
      email=data.email,
      full_name=data.full_name,
      password_hash=hash_password(data.password)
    )
    
    session.add(user)
    
    session.commit()
    
    return tenant, user
  

    