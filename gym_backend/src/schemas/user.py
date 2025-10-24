from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name")

class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")
    role: str = Field(default="member", description="User role: admin, member, or trainer")

class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., description="User email (username)")
    password: str = Field(..., description="User password")

class UserResponse(UserBase):
    """Schema for user response"""
    id: int = Field(..., description="User ID")
    role: str = Field(..., description="User role")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="Authenticated user information")
