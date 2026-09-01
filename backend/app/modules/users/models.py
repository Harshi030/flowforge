import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import (
    Base,
    CreatedByMixin,
    TimestampMixin,
    UpdatedByMixin,
    UUIDPrimaryKeyMixin,
)


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, CreatedByMixin, UpdatedByMixin):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    email: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        default=True,
    )


class UserInvitation(Base, UUIDPrimaryKeyMixin, TimestampMixin, CreatedByMixin):
    __tablename__ = "user_invitations"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
