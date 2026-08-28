from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.tenants.models import Tenant

class TenantRepository:
    def __init__(self, session: Session):
        self.session = session
      
    def get_by_slug(self, slug: str):
        return self.session.execute(
          select(Tenant).where(Tenant.slug == slug)
        ).scalar_one_or_none()
         
        
    def create(self,name: str, slug: str):
        tenant = Tenant(
            name=name,
            slug=slug
        ) 
        
        self.session.add(tenant)
        self.session.flush()
        
        return tenant