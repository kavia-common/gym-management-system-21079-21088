from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ClassScheduleBase(BaseModel):
    """Base class schedule schema"""
    title: str = Field(..., description="Class title")
    description: Optional[str] = Field(None, description="Class description")
    room: Optional[str] = Field(None, description="Room/location")
    capacity: int = Field(default=20, gt=0, description="Maximum capacity")
    start_time: datetime = Field(..., description="Class start time")
    end_time: datetime = Field(..., description="Class end time")

class ClassScheduleCreate(ClassScheduleBase):
    """Schema for creating a class schedule"""
    trainer_id: int = Field(..., description="Trainer ID")

class ClassScheduleUpdate(BaseModel):
    """Schema for updating a class schedule"""
    title: Optional[str] = Field(None, description="Class title")
    description: Optional[str] = Field(None, description="Class description")
    trainer_id: Optional[int] = Field(None, description="Trainer ID")
    room: Optional[str] = Field(None, description="Room/location")
    capacity: Optional[int] = Field(None, gt=0, description="Maximum capacity")
    start_time: Optional[datetime] = Field(None, description="Class start time")
    end_time: Optional[datetime] = Field(None, description="Class end time")

class ClassScheduleResponse(ClassScheduleBase):
    """Schema for class schedule response"""
    id: int = Field(..., description="Class ID")
    trainer_id: int = Field(..., description="Trainer ID")
    created_at: datetime = Field(..., description="Class creation timestamp")
    booked_count: int = Field(default=0, description="Number of confirmed bookings")
    
    class Config:
        from_attributes = True
