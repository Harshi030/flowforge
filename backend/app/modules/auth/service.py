import re
import uuid
import jwt
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.security import (
    hash_password,
    verify_password,
    create_token,
)

from app.modules.auth.schemas import (
    RegisterTenantRequest,
    LoginRequest,
)

from app.modules.tenants.models import Tenant
from app.modules.users.models import User

from app.modules.tenants.repository import TenantRepository
from app.modules.users.repository import UserRepository
from app.modules.auth.repository import RefreshTokenRepository
from app.modules.auth.rate_limiter import LoginRateLimiter
from app.core.redis import redis_client
from app.modules.rbac import service as rbac_service

from app.core.security import decode_token,create_access_token

class SlugAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass

class RateLimitExceededError(Exception):
    pass


def _make_slug(company_name: str) -> str:
    slug = company_name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def register_tenant(
    session: Session,
    data: RegisterTenantRequest
) -> tuple[Tenant, User]:
    try:
        tenant_repository = TenantRepository(session)
        user_repository = UserRepository(session)

        slug = _make_slug(data.company_name)

        existing_tenant = tenant_repository.get_by_slug(slug)

        if existing_tenant:
            raise SlugAlreadyExistsError(
                f"Slug {slug} already exists."
            )

        tenant = tenant_repository.create(
            name=data.company_name,
            slug=slug,
        )

        password_hash = hash_password(data.password)

        user = user_repository.create(
            tenant_id=tenant.id,
            email=data.email,
            full_name=data.full_name,
            password_hash=password_hash,
        )
        
        rbac_service.provision_default_roles(
            session,
            tenant.id,
            user.id
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

    if not user or not verify_password(
        data.password,
        user.password_hash
    ):
        rate_limiter.record_failure(key)
        raise InvalidCredentialsError()

    if not user.is_active:
        rate_limiter.record_failure(key)
        raise InvalidCredentialsError()

    access_token,refresh_token = create_token(
        user.id,
        tenant.id,
    )
    rate_limiter.reset(key)
    refresh_token_repository = RefreshTokenRepository(session)
    
    try:
        payload = decode_token(refresh_token)
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
        payload = decode_token(refresh_token)
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
    
    return create_access_token(
        user.id,
        user.tenant_id
    )
    
def logout(session: Session, refresh_token: str | None) -> None:
    if refresh_token is None:
        raise InvalidCredentialsError()
        
    try:
        payload = decode_token(refresh_token)
    except jwt.InvalidTokenError:
        raise InvalidCredentialsError()
    
    jti = payload.get("jti")
    
    if not jti:
        raise InvalidCredentialsError()
    
    jti = uuid.UUID(jti)
    
    refresh_token_repository = RefreshTokenRepository(session)
    
    refresh_token_repository.revoke(jti)
    
    session.commit()
    
    
    
    