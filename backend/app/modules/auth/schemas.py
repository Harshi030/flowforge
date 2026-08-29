import uuid

from pydantic import BaseModel, EmailStr, Field

class RegisterTenantRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    
class RegisterTenantResponse(BaseModel):
  message: str
  
class LoginRequest(BaseModel):
    slug: str
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class RegistrationApprovalResponse(BaseModel):
    message: str
