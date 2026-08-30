from sqlalchemy.orm import Session
from app.modules.auth.dependencies import get_current_user
from app.core.db import get_db_session
from fastapi import Depends, HTTPException, status
from app.modules.users.models import User
from dataclasses import dataclass
from app.modules.rbac.service import get_permission_codes_for_user

@dataclass
class AuthContext:
    user: User
    session: Session
    permissions: set[str]

def requires_permission(permission_code: str):

    def checker(
        session: Session = Depends(get_db_session),
        user: User = Depends(get_current_user),
    ) -> AuthContext:

        permissions = get_permission_codes_for_user(
            user.id
        )

        if permission_code not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return AuthContext(
            user=user,
            session=session,
            permissions=permissions,
        )

    return checker