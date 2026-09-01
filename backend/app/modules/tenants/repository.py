from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.tenants.models import Tenant, TenantRegistrationRequest


class TenantRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_slug(self, slug: str):
        return self.session.execute(
            select(Tenant).where(Tenant.slug == slug)
        ).scalar_one_or_none()

    def create(self, name: str, slug: str):
        tenant = Tenant(name=name, slug=slug)

        self.session.add(tenant)
        self.session.flush()

        return tenant


class TenantRegistrationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        company_name: str,
        slug: str,
        email: str,
        full_name: str,
        password_hash: str,
        approval_token_hash: str,
        expires_at: datetime,
    ) -> TenantRegistrationRequest:
        register_request = TenantRegistrationRequest(
            company_name=company_name,
            slug=slug,
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            approval_token_hash=approval_token_hash,
            expires_at=expires_at,
        )

        self.session.add(register_request)
        self.session.flush()

        return register_request

    def get_pending_by_email(self, email: str):
        return self.session.execute(
            select(TenantRegistrationRequest).where(
                TenantRegistrationRequest.email == email
            )
        ).scalar_one_or_none()

    def get_pending_by_slug(self, slug: str):
        return self.session.execute(
            select(TenantRegistrationRequest).where(
                TenantRegistrationRequest.slug == slug
            )
        ).scalar_one_or_none()

    def get_by_approval_token_hash(
        self, token_hash: str
    ) -> TenantRegistrationRequest | None:
        return self.session.execute(
            select(TenantRegistrationRequest).where(
                TenantRegistrationRequest.approval_token_hash == token_hash
            )
        ).scalar_one_or_none()

    def mark_as_approved(self, registration: TenantRegistrationRequest) -> None:
        registration.status = "approved"
        registration.approved_at = datetime.now(UTC)

        self.session.flush()
