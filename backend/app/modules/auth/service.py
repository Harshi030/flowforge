import re
import uuid
import jwt
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.modules.auth.schemas import (
    RegisterTenantRequest,
    LoginRequest,
)

from app.modules.tenants.models import Tenant
from app.modules.users.models import User

from app.modules.tenants.repository import TenantRepository, TenantRegistrationRepository
from app.modules.users.repository import UserRepository
from app.modules.auth.repository import RefreshTokenRepository
from app.modules.auth.rate_limiter import LoginRateLimiter
from app.core.redis import redis_client
from app.modules.rbac import service as rbac_service
from app.core.config import Settings
from app.infrastructure.tasks.email_tasks import (
    send_registration_approval_email,
)

from app.core import security 

settings = Settings()

class SlugAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass

class RateLimitExceededError(Exception):
    pass

class RegistrationAlreadyPendingError(Exception):
    pass

class InvalidRegistrationApprovalError(Exception):
    pass


def _make_slug(company_name: str) -> str:
    slug = company_name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")

def submit_registration(session: Session, data: RegisterTenantRequest):
    try:
        slug = _make_slug(data.company_name)
        tenant_repository = TenantRepository(session)
        
        register_request_repository = TenantRegistrationRepository(session)
        
        existing_tenant = tenant_repository.get_by_slug(slug)
        
        if existing_tenant:
            raise SlugAlreadyExistsError()
        
        pending_registartion_by_email = register_request_repository.get_pending_by_email(data.email)
        
        if pending_registartion_by_email:
            raise RegistrationAlreadyPendingError()
        
        pending_registration_by_slug = register_request_repository.get_pending_by_slug(slug)
        
        if pending_registration_by_slug:
            raise RegistrationAlreadyPendingError()
        
        token = security.generate_token()
        token_hash = security.hash_token(token)
        
        password_hash = security.hash_password(data.password)
        
        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(days=settings.registration_approval_expire_days)
        )
        
        registration = register_request_repository.create(
            company_name=data.company_name,
            slug=slug,
            email=data.email,
            full_name=data.full_name,
            password_hash=password_hash,
            approval_token_hash=token_hash,
            expires_at=expires_at
        )
        
        session.commit()
        
        send_registration_approval_email.delay(
            to=settings.admin_email,
            company_name=registration.company_name,
            email=registration.email,
            full_name=registration.full_name,
            approval_token=token
        )
        return registration, token
    except Exception:
        session.rollback()
        raise
    
def approval_registration(
    session: Session,
    token: str
): 
    try:
    
        token_hash = security.hash_token(token)

        register_repository = TenantRegistrationRepository(session)
        registration = register_repository.get_by_approval_token_hash(
            token_hash=token_hash
        )

        if registration is None:
            raise InvalidRegistrationApprovalError()

        if registration.status != "pending":
            raise InvalidRegistrationApprovalError()

        if registration.expires_at <= datetime.now(timezone.utc):
            raise InvalidRegistrationApprovalError()
        
        register_repository.mark_as_approved(registration)

        tenant_repository = TenantRepository(session)

        tenant = tenant_repository.create(
            name=registration.company_name,
            slug=registration.slug,
        )

        user_repository = UserRepository(session)

        user = user_repository.create(
            tenant_id=tenant.id,
            email=registration.email,
            full_name=registration.full_name,
            password_hash=registration.password_hash,
        )

        rbac_service.provision_default_roles(
            session,
            tenant.id,
            user.id,
        )

        session.commit()

        return tenant, user
    except Exception:
        session.rollback()
        raise
  
def login(
    session: Session,
    data: LoginRequest,
    key: str
) -> tuple[str, str]:
    rate_limiter = LoginRateLimiter(redis_client)
    
    if not rate_limiter.is_allowed(key):
        raise RateLimitExceededError()
    
    tenant_repository = TenantRepository(session)
    user_repository = UserRepository(session)

    tenant = tenant_repository.get_by_slug(data.slug)

    if not tenant:
        rate_limiter.record_failure(key)
        raise InvalidCredentialsError()

    user = user_repository.get_by_email_and_tenant(
        email=data.email,
        tenant_id=tenant.id,
    )

    if not user or not security.verify_password(
        data.password,
        user.password_hash
    ):
        rate_limiter.record_failure(key)
        raise InvalidCredentialsError()

    if not user.is_active:
        rate_limiter.record_failure(key)
        raise InvalidCredentialsError()

    access_token,refresh_token = security.create_token(
        user.id,
        tenant.id,
    )
    rate_limiter.reset(key)
    refresh_token_repository = RefreshTokenRepository(session)
    
    try:
        payload = security.decode_token(refresh_token)
    except jwt.InvalidTokenError:
        raise InvalidCredentialsError()
    
    jti = payload.get("jti")
    expiry_at = payload.get("exp")
    
    if not jti or not expiry_at:
        raise InvalidCredentialsError()
    
    expiry_at = datetime.fromtimestamp(
        expiry_at,timezone.utc
    )
    refresh_token_repository.create(
        jti=jti,
        user_id=user.id,
        tenant_id=tenant.id,
        expires_at=expiry_at,
    )
    session.commit()
    return access_token,refresh_token

def refresh_access_token(session: Session, refresh_token: str | None) -> str:
    if refresh_token is None:
        raise InvalidCredentialsError()
    
    try:
        payload = security.decode_token(refresh_token)
    except jwt.InvalidTokenError:
        raise InvalidCredentialsError()
    
    if payload.get("type") != "refresh":
        raise InvalidCredentialsError()
    
    user_id = payload.get("sub")
    jti = payload.get("jti")
    
    if not user_id or not jti:
        raise InvalidCredentialsError()
    
    try:
        user_id = uuid.UUID(user_id)
    except(ValueError,AttributeError):
        raise InvalidCredentialsError()
    
    refresh_token_repository = RefreshTokenRepository(session)

    stored_token = refresh_token_repository.get_by_jti(jti)
    
    if (
        stored_token is None
        or stored_token.revoked_at is not None
        or stored_token.expires_at <= datetime.now(timezone.utc)
    ):
        raise InvalidCredentialsError()
    
    user_repository = UserRepository(session)
    
    user = user_repository.get_by_id(user_id)
    
    if user is None or not user.is_active:
        raise InvalidCredentialsError()
    
    return security.create_access_token(
        user.id,
        user.tenant_id
    )
    
def logout(session: Session, refresh_token: str | None) -> None:
    if refresh_token is None:
        raise InvalidCredentialsError()
        
    try:
        payload = security.decode_token(refresh_token)
    except jwt.InvalidTokenError:
        raise InvalidCredentialsError()
    
    jti = payload.get("jti")
    
    if not jti:
        raise InvalidCredentialsError()
    
    jti = uuid.UUID(jti)
    
    refresh_token_repository = RefreshTokenRepository(session)
    
    refresh_token_repository.revoke(jti)
    
    session.commit()
    
    
    
    