import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.modules.users.repository import UserRepository

from app.core.db import get_db_session
from app.core.security import decode_token
from app.modules.users.models import User

bearer_scheme = HTTPBearer()

_credentials_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: Session = Depends(get_db_session),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.InvalidTokenError:      # covers expired AND tampered tokens
        raise _credentials_error
    
    if payload.get("type") != "access":
        raise _credentials_error

    user_id = payload.get("sub")
    if user_id is None:
        raise _credentials_error

    user_repository = UserRepository(session)
    
    user = user_repository.get_by_id(user_id)

    if user is None or not user.is_active:
        raise _credentials_error

    return user