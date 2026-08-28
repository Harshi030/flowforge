import uuid
import jwt
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.core.config import Settings

settings = Settings()

_hasher = PasswordHasher()

def hash_password(password: str) -> str:
  return _hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
  try:
    _hasher.verify(hashed_password, plain_password)
    return True
  except VerifyMismatchError:
    return False
  
def create_access_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
   now = datetime.now(timezone.utc)
   payload = {
      "sub": str(user_id),
      "tenant_id": str(tenant_id),
      "type":"access",
      "iat": now,
      "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
   }
   
   return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def create_refresh_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    payload = {
       "sub": str(user_id),
       "tenant_id": str(tenant_id),
       "type":"refresh",
       "iat": now,
       "jti":str(uuid.uuid4()),
       "exp": now + timedelta(days=settings.jwt_refresh_token_expire_days),
    }
    
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
  
def create_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> tuple[str, str]:
    access_token = create_access_token(user_id, tenant_id)
    refresh_token = create_refresh_token(user_id, tenant_id)
    
    return access_token,refresh_token

 
def decode_token(token: str) -> dict:
  return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])