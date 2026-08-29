from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Request
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.modules.auth import service
from app.modules.auth.schemas import RegisterTenantRequest, RegisterTenantResponse, LoginRequest, LoginResponse,RegistrationApprovalResponse
from app.core.config import Settings
from app.infrastructure.email.service import EmailService
from app.infrastructure.email.provider import ConsoleEmailProvider

settings = Settings()

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", response_model=RegisterTenantResponse, status_code=201,)
def register_tenant(
    data: RegisterTenantRequest,
    session: Session = Depends(get_db_session),
):
    try:
        registration,token = service.submit_registration(session, data)
        email_service = EmailService(ConsoleEmailProvider())
        email_service.send_registration_approval(
            to=settings.admin_email,
            company_name=registration.company_name,
            email=registration.email,
            full_name=registration.full_name,
            approval_token=token
        )
    except service.SlugAlreadyExistsError:
      raise HTTPException(status_code=409, detail="Company name already taken")
    except service.RegistrationAlreadyPendingError:
        raise HTTPException(
            status_code=409,
            detail="Registration is already pending approval",
        )
    return RegisterTenantResponse(message="Registration submitted for approval")

@router.post("/approval", response_model=RegistrationApprovalResponse, status_code=200)
def approve_registration(
    token: str,
    session: Session = Depends(get_db_session)
):
    try:
        tenant, user = service.approval_registration(
            session,
            token
        )
    except service.InvalidCredentialsError:
        raise HTTPException(
            status_code=400,
            detail= "Invalid or expired approval link"
        )
    
    return RegistrationApprovalResponse(
        message="Registration approved successfully"
    )
@router.post("/login", response_model=LoginResponse, status_code=200)
def login(
    data: LoginRequest,
    response: Response,
    request: Request,
    session: Session = Depends(get_db_session)
):
    key = f"login_rate:{request.client.host}:{data.slug}:{data.email.lower()}"
    try:
        access_token,refresh_token = service.login(session, data, key)
    except service.RateLimitExceededError:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later.",
        )
    except service.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,      # True in production with HTTPS
        samesite="lax",
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        path="/"
    )
    return LoginResponse(access_token=access_token)

@router.post("/refresh", response_model=LoginResponse, status_code=200)
def refresh(
    refresh_token: str | None = Cookie(default=None),
    session:Session = Depends(get_db_session)
):
    try:
        access_token = service.refresh_access_token(session, refresh_token)
    except service.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return LoginResponse(access_token=access_token)

@router.post("/logout", status_code=204)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    session:Session = Depends(get_db_session)
):
    try:
        service.logout(session, refresh_token)
    except service.InvalidCredentialsError:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    response.delete_cookie(
        key="refresh_token",
        path="/",
    )