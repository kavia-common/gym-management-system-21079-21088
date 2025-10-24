from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database.connection import get_db
from src.database.models import Booking, BookingStatus, User, ClassSchedule, UserRole
from src.schemas.booking import BookingCreate, BookingResponse, AttendanceCreate, AttendanceResponse
from src.auth.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])

# PUBLIC_INTERFACE
@router.get("/", response_model=List[BookingResponse],
            summary="List bookings",
            description="List all bookings (admin) or current user's bookings")
async def list_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get bookings. Admins see all, members see their own.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List[BookingResponse]: List of bookings
    """
    if current_user.role == UserRole.admin:
        bookings = db.query(Booking).all()
    else:
        bookings = db.query(Booking).filter(
            Booking.member_id == current_user.id
        ).all()
    
    return bookings

# PUBLIC_INTERFACE
@router.get("/{booking_id}", response_model=BookingResponse,
            summary="Get booking details",
            description="Retrieve details of a specific booking")
async def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific booking's details.
    
    Args:
        booking_id: Booking ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        BookingResponse: Booking details
        
    Raises:
        HTTPException: If booking not found or permission denied
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.admin and booking.member_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return booking

# PUBLIC_INTERFACE
@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED,
             summary="Create booking",
             description="Book a class for the current user")
async def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new booking for a class. Checks capacity before confirming.
    
    Args:
        booking_data: Booking data with class_id
        db: Database session
        current_user: Authenticated user
        
    Returns:
        BookingResponse: Created booking
        
    Raises:
        HTTPException: If class not found, already booked, or at capacity
    """
    # Verify class exists
    class_schedule = db.query(ClassSchedule).filter(
        ClassSchedule.id == booking_data.class_id
    ).first()
    
    if not class_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Check if user already has a booking for this class
    existing_booking = db.query(Booking).filter(
        Booking.member_id == current_user.id,
        Booking.class_id == booking_data.class_id,
        Booking.status != BookingStatus.cancelled
    ).first()
    
    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a booking for this class"
        )
    
    # Check capacity
    confirmed_bookings = db.query(Booking).filter(
        Booking.class_id == booking_data.class_id,
        Booking.status == BookingStatus.confirmed
    ).count()
    
    if confirmed_bookings >= class_schedule.capacity:
        # Class is full, add to waitlist
        booking_status = BookingStatus.waitlisted
    else:
        booking_status = BookingStatus.confirmed
    
    new_booking = Booking(
        member_id=current_user.id,
        class_id=booking_data.class_id,
        status=booking_status
    )
    
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    
    return new_booking

# PUBLIC_INTERFACE
@router.patch("/{booking_id}/cancel", response_model=BookingResponse,
              summary="Cancel booking",
              description="Cancel a booking")
async def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a booking. Members can cancel their own, admins can cancel any.
    
    Args:
        booking_id: Booking ID to cancel
        db: Database session
        current_user: Authenticated user
        
    Returns:
        BookingResponse: Updated booking
        
    Raises:
        HTTPException: If booking not found or permission denied
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.admin and booking.member_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if booking.status == BookingStatus.cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled"
        )
    
    booking.status = BookingStatus.cancelled
    db.commit()
    db.refresh(booking)
    
    # Check if there are waitlisted bookings for this class
    waitlisted = db.query(Booking).filter(
        Booking.class_id == booking.class_id,
        Booking.status == BookingStatus.waitlisted
    ).order_by(Booking.created_at).first()
    
    if waitlisted:
        # Promote first waitlisted booking to confirmed
        waitlisted.status = BookingStatus.confirmed
        db.commit()
    
    return booking

# Attendance Management

# PUBLIC_INTERFACE
@router.post("/attendance", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED,
             summary="Mark attendance",
             description="Mark attendance for a booking (admin only)")
async def mark_attendance(
    attendance_data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Mark attendance for a booking. Requires admin role.
    
    Args:
        attendance_data: Attendance data
        db: Database session
        current_user: Authenticated admin user
        
    Returns:
        AttendanceResponse: Created attendance record
        
    Raises:
        HTTPException: If booking not found or attendance already recorded
    """
    from src.database.models import Attendance
    
    # Verify booking exists
    booking = db.query(Booking).filter(Booking.id == attendance_data.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check if attendance already recorded
    existing = db.query(Attendance).filter(
        Attendance.booking_id == attendance_data.booking_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already recorded for this booking"
        )
    
    attendance = Attendance(**attendance_data.dict())
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    
    return attendance
