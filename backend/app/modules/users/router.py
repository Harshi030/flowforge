from fastapi import APIRouter, HTTPException, Depends
from app.modules.users.schemas import UserResponse
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/me", response_model=UserResponse, status_code=200)
def me(
    user:User = Depends(get_current_user)
): 
    return user
