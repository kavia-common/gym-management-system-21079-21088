from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BookingBase(BaseModel):
    """Base booking schema"""
    class_id: int = Field(..., description="Class schedule ID")

class BookingCreate(BookingBase):
    """Schema for creating a booking"""
    pass

class BookingResponse(BaseModel):
    """Schema for booking response"""
    id: int = Field(..., description="Booking ID")
    member_id: int = Field(..., description="Member user ID")
    class_id: int = Field(..., description="Class schedule ID")
    status: str = Field(..., description="Booking status: confirmed, cancelled, waitlisted")
    created_at: datetime = Field(..., description="Booking creation timestamp")
    
    class Config:
        from_attributes = True

class AttendanceCreate(BaseModel):
    """Schema for marking attendance"""
    booking_id: int = Field(..., description="Booking ID")
    attended: bool = Field(..., description="Whether the member attended")
    notes: Optional[str] = Field(None, description="Attendance notes")

class AttendanceResponse(BaseModel):
    """Schema for attendance response"""
    id: int = Field(..., description="Attendance ID")
    booking_id: int = Field(..., description="Booking ID")
    attended: bool = Field(..., description="Attendance status")
    notes: Optional[str] = Field(None, description="Attendance notes")
    created_at: datetime = Field(..., description="Attendance record timestamp")
    
    class Config:
        from_attributes = True
