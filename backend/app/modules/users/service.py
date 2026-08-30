import hashlib
import secrets
import uuid
import math
from sqlalchemy.orm import Session
from app.modules.users.repository import UserRepository, UserInvitationRepository 
from app.modules.rbac.repository import RBACRepository
from datetime import datetime,timezone,timedelta
from app.core.config import Settings
from app.modules.users.models import UserInvitation
from app.core import security
from app.modules.users.schemas import CreateUserRequest, UpdateUserRequest
from app.modules.audit import service as audit_service

settings = Settings()

class InvalidInvitationError(Exception):
  pass

class UserAlreadyExistsError(Exception):
  pass

class RoleNotFoundError(Exception):
  pass

class UserNotFoundError(Exception):
  pass

class InvalidRoleAssignmentError(Exception):
  pass

  
def create_invitation(
  session: Session,
  user_id: uuid.UUID,
  created_by: uuid.UUID
) -> tuple[UserInvitation, str] :
  user_invitation_repository = UserInvitationRepository(session)
  token = security.generate_token()
  token_hash = security.hash_token(token) 
  expires_at = (
    datetime.now(timezone.utc)
    + timedelta(days=settings.invitation_expire_days)
  )
  
  user_invitation = user_invitation_repository.create(
    user_id=user_id,
    token_hash=token_hash,
    expires_at=expires_at,
    created_by=created_by
  )
  
  
  return user_invitation, token

def accept_invitation(
  session: Session,
  token: str,
  password: str
) -> None:
  try:
    token_hash = security.hash_token(token)
    
    invitation_repository = UserInvitationRepository(session)
    
    invitation = invitation_repository.get_by_token_hash(token_hash)
    
    if not invitation:
      raise InvalidInvitationError()
    
    if invitation.used_at is not None:
      raise InvalidInvitationError()
    
    if invitation.expires_at <= datetime.now(timezone.utc):
      raise InvalidInvitationError()
    
    user_repository = UserRepository(session)
    
    user = user_repository.get_by_id(invitation.user_id)
    
    if user is None:
      raise InvalidInvitationError()
    
    user.password_hash = security.hash_password(password)
    user.is_active=True
    invitation_repository.mark_as_used(invitation)
    
    audit_service.create_audit_log(
      session=session,
      tenant_id=user.tenant_id,
      user_id=user.id,
      action="USER_INVITATION_ACCEPTED",
      entity_type="user",
      entity_id=user.id
    )
    
    session.commit()
  except Exception:
    session.rollback()
    raise
  
def create_user(
  session: Session,
  tenant_id: uuid.UUID,
  created_by: uuid.UUID,
  data: CreateUserRequest
):
  try:
    user_repository = UserRepository(session)
    
    existing_user = user_repository.get_by_email_and_tenant(
        email=data.email,
        tenant_id=tenant_id,
    )

    if existing_user is not None:
      raise UserAlreadyExistsError()
    
    user = user_repository.create(
      tenant_id=tenant_id,
      email=data.email,
      full_name=data.full_name,
      password_hash=None,
      is_active=False,
      created_by=created_by
    )
    
    rbac_repository = RBACRepository(session)
    role = rbac_repository.get_role_by_tenant_id_and_role_id(tenant_id, data.role_id)
    
    if role is None:
      raise RoleNotFoundError()
    
    rbac_repository.assign_role_to_user(user.id,role.id)
    invitation,token = create_invitation(session, user.id, created_by)
    
    
    audit_service.create_audit_log(
      session=session,
      tenant_id=tenant_id,
      user_id=created_by,
      action="USER_CREATED",
      entity_type="user",
      entity_id=user.id,
    )
    
    session.commit()
    
    return user, invitation, token
  except Exception:
    session.rollback()
    raise
    
  
def get_users(session:Session, tenant_id: uuid.UUID, page: int, page_size: int):
  user_repository = UserRepository(session)
  
  rows, total = user_repository.get_users(
    tenant_id=tenant_id,
    page=page,
    page_size=page_size
  )
  users = {}
  
  for user, role in rows:
    if user.id not in users:
      users[user.id] = {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "is_active": user.is_active,
        "roles": [],
      }
      
    users[user.id]["roles"].append(role.name)
    
  total_pages = math.ceil(total / page_size) if total else 0
  
  return {
    "items": list(users.values()),
    "page": page,
    "page_size": page_size,
    "total": total,
    "total_pages": total_pages,
  }
  
def update_user(
  session: Session, 
  data: UpdateUserRequest,
  user_id: uuid.UUID,
  tenant_id: uuid.UUID,
  updated_by: uuid.UUID
):
  try:
    user_repository = UserRepository(session)
    
    user = user_repository.get_by_id_and_tenant(user_id, tenant_id)
    
    if user is None:
      raise UserNotFoundError()
    
    details = {
      "changed_fields":[]
    }
    
    if data.full_name is not None:
      details["old_full_name"] = user.full_name
      details["new_full_name"] = data.full_name
      user.full_name = data.full_name
      details["changed_fields"].append("full_name")
      
    if data.is_active is not None:
      details["old_is_active"] = user.is_active
      details["new_is_active"] = data.is_active
      user.is_active = data.is_active
      details["changed_fields"].append("is_active")
      
    if data.role_ids is not None:
      
      if len(data.role_ids) == 0:
        raise InvalidRoleAssignmentError()
      
      rbac_repository = RBACRepository(session)
      
      old_roles = rbac_repository.get_roles_by_user_id(
        user_id=user_id
      )
      
      roles = rbac_repository.get_roles_by_ids_and_tenant(
        role_ids=data.role_ids,
        tenant_id=tenant_id
      )
      
      if len(roles) != len(data.role_ids):
        raise InvalidRoleAssignmentError()
      
      details["changed_fields"].append("role_ids")
      
      details["old_roles"] = [
        role.name for role in old_roles
      ]
      
      details["new_roles"] = [
        role.name for role in roles
      ]
      rbac_repository.remove_roles_from_user(
        user_id=user_id
      )
      
      for role in roles:
        rbac_repository.assign_role_to_user(
          user_id=user_id,
          role_id=role.id
        )
    
        
    user.updated_at = datetime.now(timezone.utc)
    user.updated_by = updated_by
    
    
    audit_service.create_audit_log(
      session=session,
      tenant_id=tenant_id,
      user_id=updated_by,
      action="USER_UPDATED",
      entity_type="user",
      entity_id=user.id,
      details=details
    )
    
    session.commit()
    
    return user
  except Exception:
    session.rollback()
    raise