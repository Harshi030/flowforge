import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.core.db import get_db_session
from app.modules.users.schemas import (
    UserResponse,
    AcceptInvitationRequest,
    AcceptInvitationResponse, 
    CreateUserRequest, 
    CreateUserResponse,
    PaginatedUsersResponse,
    UpdateUserRequest,
    UpdateUserResponse
)
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.users import service as user_service
from app.modules.rbac.dependencies import requires_permission, AuthContext

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/me", response_model=UserResponse, status_code=200)
def me(
    user:User = Depends(get_current_user)
): 
    return user

@router.post("/invitation/accept", response_model=AcceptInvitationResponse,status_code=200)
def accept_invitation(
    data:AcceptInvitationRequest,
    session: Session = Depends(get_db_session)
):  
    try:
        user_service.accept_invitation(session,data.token,data.password)
    except user_service.InvalidInvitationError:
        raise HTTPException(status_code=400, detail="Invalid or expired invitation")
    return AcceptInvitationResponse(message="Invitation accepted successfully")

@router.post("/",response_model=CreateUserResponse, status_code=201)
def create_user(
    data: CreateUserRequest,
    auth: AuthContext = Depends(
        requires_permission("user:create")
    ),
):
    current_user = auth.user
    session = auth.session

    try:
        user, invitation, token = user_service.create_user(
            session=session,
            tenant_id=current_user.tenant_id,
            created_by=current_user.id,
            data=data,
        )
    except user_service.UserAlreadyExistsError:
        raise HTTPException(status_code=409, detail="User already exists")
    except user_service.RoleNotFoundError:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return CreateUserResponse(
        user_id=user.id,
        message="User invitation created successfully",
        invitation_token=token,
    )

@router.get("/",response_model=PaginatedUsersResponse,status_code=200)
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(requires_permission("user:manage"))
):
    return user_service.get_users(
        session=auth.session,
        tenant_id=auth.user.tenant_id,
        page=page,
        page_size=page_size,
    )


@router.patch("/{user_id}",response_model=UpdateUserResponse,status_code=200)
def update_user(
    user_id: uuid.UUID,
    data: UpdateUserRequest,
    auth: AuthContext = Depends(requires_permission("user:manage"))
):
    try:
        user = user_service.update_user(
            session=auth.session,
            data=data,
            user_id=user_id,
            tenant_id=auth.user.tenant_id,
            updated_by=auth.user.id
        )
    except user_service.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except user_service.InvalidRoleAssignmentError:
        raise HTTPException(status_code=400, detail="Invalid role assignment")
    
    return UpdateUserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
    )