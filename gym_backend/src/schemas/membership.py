from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MembershipPlanBase(BaseModel):
    """Base membership plan schema"""
    name: str = Field(..., description="Plan name")
    description: Optional[str] = Field(None, description="Plan description")
    duration_days: int = Field(..., gt=0, description="Plan duration in days")
    price: int = Field(..., ge=0, description="Plan price in cents")
    features: Optional[str] = Field(None, description="Plan features (JSON string)")

class MembershipPlanCreate(MembershipPlanBase):
    """Schema for creating a membership plan"""
    pass

class MembershipPlanUpdate(BaseModel):
    """Schema for updating a membership plan"""
    name: Optional[str] = Field(None, description="Plan name")
    description: Optional[str] = Field(None, description="Plan description")
    duration_days: Optional[int] = Field(None, gt=0, description="Plan duration in days")
    price: Optional[int] = Field(None, ge=0, description="Plan price in cents")
    features: Optional[str] = Field(None, description="Plan features (JSON string)")

class MembershipPlanResponse(MembershipPlanBase):
    """Schema for membership plan response"""
    id: int = Field(..., description="Plan ID")
    created_at: datetime = Field(..., description="Plan creation timestamp")
    
    class Config:
        from_attributes = True

class MembershipBase(BaseModel):
    """Base membership schema"""
    plan_id: int = Field(..., description="Membership plan ID")
    start_date: datetime = Field(..., description="Membership start date")
    end_date: datetime = Field(..., description="Membership end date")

class MembershipCreate(BaseModel):
    """Schema for creating a membership"""
    member_id: int = Field(..., description="Member user ID")
    plan_id: int = Field(..., description="Membership plan ID")

class MembershipResponse(BaseModel):
    """Schema for membership response"""
    id: int = Field(..., description="Membership ID")
    member_id: int = Field(..., description="Member user ID")
    plan_id: int = Field(..., description="Membership plan ID")
    start_date: datetime = Field(..., description="Membership start date")
    end_date: datetime = Field(..., description="Membership end date")
    status: str = Field(..., description="Membership status: active, expired, cancelled")
    created_at: datetime = Field(..., description="Membership creation timestamp")
    
    class Config:
        from_attributes = True
