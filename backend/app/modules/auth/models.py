import uuid

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RefreshToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"

    jti: Mapped[uuid.UUID] = mapped_column(unique=True, index=True)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
