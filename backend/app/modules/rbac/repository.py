import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.rbac.models import (
    Role,
    UserRole,
    RolePermission,
    Permission,
)


class RBACRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_role(
        self,
        tenant_id: uuid.UUID,
        name: str,
        is_system: bool = True,
    ) -> Role:

        role = Role(
            tenant_id=tenant_id,
            name=name,
            is_system=is_system,
        )

        self.session.add(role)
        self.session.flush()

        return role

    def get_permissions_by_codes(
        self,
        codes: list[str],
    ) -> list[Permission]:

        return self.session.execute(
            select(Permission).where(
                Permission.code.in_(codes)
            )
        ).scalars().all()

    def add_permissions_to_role(
        self,
        role: Role,
        permissions: list[Permission],
    ) -> None:

        for permission in permissions:
            role_permission = RolePermission(
                role_id=role.id,
                permission_id=permission.id,
            )

            self.session.add(role_permission)

    def assign_role_to_user(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> None:

        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
        )

        self.session.add(user_role)
        
    def get_permission_codes_for_user(
        self,
        user_id: uuid.UUID
    ) -> set[str]:
        query = (
            select(Permission.code)
            .distinct()
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        
        permissions = self.session.execute(query).scalars().all()
        
        return set(permissions)
    
    def get_role_by_tenant_id_and_role_id(self, tenant_id: uuid.UUID, role_id: uuid.UUID):
        return self.session.execute(
            select(Role).where(Role.tenant_id == tenant_id, Role.id == role_id)
        ).scalar_one_or_none() 
    
    def get_roles_by_ids_and_tenant(
        self,
        role_ids: list[uuid.UUID],
        tenant_id: uuid.UUID,
    ) -> list[Role]:

        return self.session.execute(
            select(Role).where(
                Role.id.in_(role_ids),
                Role.tenant_id == tenant_id,
            )
        ).scalars().all()
    
    def get_roles_for_user(
        self,
        user_id: uuid.UUID,
    ) -> list[Role]:

        return self.session.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        ).scalars().all()
        
    def remove_roles_from_user(
        self,
        user_id: uuid.UUID,
    ) -> None:

        self.session.execute(
            UserRole.__table__.delete().where(
                UserRole.user_id == user_id
            )
        )

        self.session.flush()