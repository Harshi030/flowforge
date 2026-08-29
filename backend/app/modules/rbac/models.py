import uuid
from sqlalchemy import String,UniqueConstraint,ForeignKey,Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models import Base, UUIDPrimaryKeyMixin, TimestampMixin

class Permission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "permissions"
    
    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )
    
class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("tenant_id","name"),)
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"),nullable=False)
    name: Mapped[str] = mapped_column(String(50),nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean,default=False,nullable=False)
    
class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[uuid.UUID] = mapped_column(
      ForeignKey("roles.id", ondelete="CASCADE"),
      primary_key=True,
    ) 
    permission_id: Mapped[uuid.UUID] = mapped_column(
      ForeignKey("permissions.id", ondelete="CASCADE"),
      primary_key=True
    )
    
class UserRole(Base):
    __tablename__ = "user_roles"
    user_id: Mapped[uuid.UUID] = mapped_column(
      ForeignKey("users.id", ondelete="CASCADE"),
      primary_key=True
    )
    
    role_id: Mapped[uuid.UUID] = mapped_column(
      ForeignKey("roles.id", ondelete="CASCADE"),
      primary_key=True
    )
    
