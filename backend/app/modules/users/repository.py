import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.users.models import User

class UserRepository:
    def __init__(self, session: Session):
        self.session = session
        
    def get_by_email_and_tenant(self, email: str, tenant_id: uuid.UUID):
        return self.session.execute(
          select(User).where(
            User.email == email,
            User.tenant_id == tenant_id
          )
        ).scalar_one_or_none()
        
    def get_by_id(self, user_id:uuid.UUID):
        return self.session.execute(
            select(User).where(User.user_id == user_id)
        ).scalar_one_or_none()
        
    def create(self, tenant_id: uuid.UUID, email: str, full_name: str, password_hash: str):
        user = User(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            password_hash=password_hash
        )
        
        self.session.add(user)
        
        return user
            
        
      