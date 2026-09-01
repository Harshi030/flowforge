from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.modules.rbac.service import get_permission_codes_for_user
from app.modules.users.models import User


@dataclass
class AuthContext:
    user: User
    session: Session
    permissions: set[str]


def requires_permission(*permission_codes: str):

    def checker(
        session: Session = Depends(get_db_session),
        user: User = Depends(get_current_user),
    ) -> AuthContext:

        permissions = get_permission_codes_for_user(session=session, user_id=user.id)

        if not any(permission in permissions for permission in permission_codes):
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
