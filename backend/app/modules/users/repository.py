import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.rbac.models import Role, UserRole
from app.modules.users.models import User, UserInvitation


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_email_and_tenant(self, email: str, tenant_id: uuid.UUID):
        return self.session.execute(
            select(User).where(User.email == email, User.tenant_id == tenant_id)
        ).scalar_one_or_none()

    def get_by_id(self, user_id: uuid.UUID):
        return self.session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

    def get_by_id_and_tenant(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> User | None:

        return self.session.execute(
            select(User).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
            )
        ).scalar_one_or_none()

    def create(
        self,
        tenant_id: uuid.UUID,
        email: str,
        full_name: str,
        password_hash: str | None,
        is_active: bool = True,
        created_by: uuid.UUID | None = None,
    ):
        user = User(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            is_active=is_active,
            created_by=created_by,
        )

        self.session.add(user)
        self.session.flush()

        return user

    def get_users(self, tenant_id: uuid, page: int, page_size: int):
        offset = (page - 1) * page_size

        query = (
            select(User, Role)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(User.tenant_id == tenant_id)
            .order_by(User.full_name.desc())
            .offset(offset)
            .limit(page_size)
        )

        rows = self.session.execute(query).all()

        count_query = (
            select(func.count(func.distinct(User.id)))
            .join(
                UserRole,
                UserRole.user_id == User.id,
            )
            .join(
                Role,
                Role.id == UserRole.role_id,
            )
            .where(User.tenant_id == tenant_id)
        )

        total = self.session.execute(count_query).scalar_one()

        return rows, total


class UserInvitationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        created_by: uuid.UUID,
    ) -> UserInvitation:
        user_invitation = UserInvitation(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_by=created_by,
        )

        self.session.add(user_invitation)
        self.session.flush()

        return user_invitation

    def get_by_token_hash(self, token_hash: str) -> UserInvitation | None:
        return self.session.execute(
            select(UserInvitation).where(UserInvitation.token_hash == token_hash)
        ).scalar_one_or_none()

    def mark_as_used(self, invitation: UserInvitation) -> None:
        invitation.used_at = datetime.now(UTC)

        self.session.flush()
