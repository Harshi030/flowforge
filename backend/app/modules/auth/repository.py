import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.auth.models import RefreshToken

class RefreshTokenRepository:
  def __init__(self, session: Session):
    self.session = session
    
  def get_by_jti(self, jti: uuid.UUID):
    return self.session.execute(
      select(RefreshToken).where(RefreshToken.jti == jti)
    ).scalar_one_or_none()
    
  def create(self,jti: uuid.UUID, user_id: uuid.UUID, tenant_id: uuid.UUID,expires_at:datetime):
    refresh_token = RefreshToken(
      jti=jti,
      user_id=user_id,
      tenant_id=tenant_id,
      expires_at=expires_at
    )
    
    self.session.add(refresh_token)
    self.session.flush()
    
    return refresh_token
  
  def revoke(self, jti: uuid.UUID):
    refresh_token = self.get_by_jti(jti)
    
    if refresh_token is None:
      return None
    
    refresh_token.revoked_at = datetime.now(timezone.utc)
    self.session.flush()
    
    return refresh_token
    
  
  