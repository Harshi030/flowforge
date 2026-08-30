import uuid
import json
from app.modules.rbac.constants import ROLE_PERMISSIONS
from sqlalchemy.orm import Session
from app.modules.rbac.repository import RBACRepository
from app.core.redis import redis_client
from app.core.config import Settings

settings = Settings()

def provision_default_roles(
    session: Session,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:

    rbac_repository = RBACRepository(session)

    admin_role = None

    for name, codes in ROLE_PERMISSIONS.items():

        role = rbac_repository.create_role(
            tenant_id=tenant_id,
            name=name,
            is_system=True,
        )

        permissions = rbac_repository.get_permissions_by_codes(codes)

        if len(permissions) != len(codes):
            raise RuntimeError(
                f"Missing permissions for role: {name}"
            )

        rbac_repository.add_permissions_to_role(
            role=role,
            permissions=permissions,
        )

        if name == "ADMIN":
            admin_role = role

    if admin_role is None:
        raise RuntimeError("ADMIN role was not created")

    rbac_repository.assign_role_to_user(
        user_id=user_id,
        role_id=admin_role.id,
    )
    
def get_permission_codes_for_user(
    session: Session,
    user_id: uuid.UUID
):
    rbac_repository = RBACRepository(session)

    key = f"rbac:permissions:user:{user_id}"
    
    cached = redis_client.get(key)
    
    if cached is not None:
        return set(json.loads(cached))
    
    permissions = rbac_repository.get_permission_codes_for_user(
        user_id=user_id
    )
    
    redis_client.set(
        key,
        json.dumps(list(permissions)),
        ex=settings.rbac_permission_cache_ttl
    )
    
    return permissions
    
    