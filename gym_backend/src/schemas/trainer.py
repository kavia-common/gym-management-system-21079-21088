from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TrainerBase(BaseModel):
    """Base trainer schema"""
    bio: Optional[str] = Field(None, description="Trainer biography")
    specialties: Optional[str] = Field(None, description="Trainer specialties")
    certifications: Optional[str] = Field(None, description="Trainer certifications")

class TrainerCreate(TrainerBase):
    """Schema for creating a trainer profile"""
    user_id: int = Field(..., description="User ID for the trainer")

class TrainerUpdate(TrainerBase):
    """Schema for updating a trainer profile"""
    pass

class TrainerResponse(TrainerBase):
    """Schema for trainer response"""
    id: int = Field(..., description="Trainer ID")
    user_id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    
    class Config:
        from_attributes = True
