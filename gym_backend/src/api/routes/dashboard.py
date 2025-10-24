from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from src.database.connection import get_db
from src.database.models import (
    User, UserRole, Membership, MembershipStatus, ClassSchedule, 
    Booking, BookingStatus, Trainer
)
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# PUBLIC_INTERFACE
@router.get("/admin", summary="Admin dashboard",
            description="Get dashboard metrics for admin users")
async def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get admin dashboard with system-wide metrics.
    
    Args:
        db: Database session
        current_user: Authenticated user (must be admin)
        
    Returns:
        dict: Dashboard metrics including member counts, revenue, bookings, etc.
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Total members
    total_members = db.query(User).filter(User.role == UserRole.member).count()
    
    # Active memberships
    active_memberships = db.query(Membership).filter(
        Membership.status == MembershipStatus.active
    ).count()
    
    # Total trainers
    total_trainers = db.query(Trainer).count()
    
    # Upcoming classes (next 7 days)
    now = datetime.utcnow()
    week_later = now + timedelta(days=7)
    upcoming_classes = db.query(ClassSchedule).filter(
        ClassSchedule.start_time >= now,
        ClassSchedule.start_time <= week_later
    ).count()
    
    # Total bookings this month
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_bookings = db.query(Booking).filter(
        Booking.created_at >= month_start,
        Booking.status == BookingStatus.confirmed
    ).count()
    
    # Revenue this month (from active memberships created this month)
    from src.database.models import MembershipPlan
    monthly_revenue = db.query(func.sum(MembershipPlan.price)).join(
        Membership, Membership.plan_id == MembershipPlan.id
    ).filter(
        Membership.created_at >= month_start
    ).scalar() or 0
    
    # Recent bookings
    recent_bookings = db.query(Booking).order_by(
        Booking.created_at.desc()
    ).limit(10).all()
    
    return {
        "total_members": total_members,
        "active_memberships": active_memberships,
        "total_trainers": total_trainers,
        "upcoming_classes": upcoming_classes,
        "monthly_bookings": monthly_bookings,
        "monthly_revenue": monthly_revenue / 100,  # Convert cents to dollars
        "recent_bookings_count": len(recent_bookings)
    }

# PUBLIC_INTERFACE
@router.get("/member", summary="Member dashboard",
            description="Get dashboard for member users")
async def member_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get member dashboard with personalized information.
    
    Args:
        db: Database session
        current_user: Authenticated member user
        
    Returns:
        dict: Dashboard with member's membership status, bookings, and upcoming classes
    """
    # User's active membership
    active_membership = db.query(Membership).filter(
        Membership.member_id == current_user.id,
        Membership.status == MembershipStatus.active
    ).first()
    
    membership_info = None
    if active_membership:
        from src.database.models import MembershipPlan
        plan = db.query(MembershipPlan).filter(
            MembershipPlan.id == active_membership.plan_id
        ).first()
        
        membership_info = {
            "plan_name": plan.name if plan else "Unknown",
            "start_date": active_membership.start_date.isoformat(),
            "end_date": active_membership.end_date.isoformat(),
            "status": active_membership.status.value,
            "days_remaining": (active_membership.end_date - datetime.utcnow()).days
        }
    
    # User's upcoming bookings
    now = datetime.utcnow()
    upcoming_bookings = db.query(Booking).join(
        ClassSchedule, Booking.class_id == ClassSchedule.id
    ).filter(
        Booking.member_id == current_user.id,
        Booking.status == BookingStatus.confirmed,
        ClassSchedule.start_time >= now
    ).order_by(ClassSchedule.start_time).limit(5).all()
    
    upcoming_classes = []
    for booking in upcoming_bookings:
        class_schedule = db.query(ClassSchedule).filter(
            ClassSchedule.id == booking.class_id
        ).first()
        if class_schedule:
            upcoming_classes.append({
                "booking_id": booking.id,
                "class_title": class_schedule.title,
                "start_time": class_schedule.start_time.isoformat(),
                "room": class_schedule.room
            })
    
    # Total bookings
    total_bookings = db.query(Booking).filter(
        Booking.member_id == current_user.id,
        Booking.status == BookingStatus.confirmed
    ).count()
    
    # Attended classes (with attendance records)
    from src.database.models import Attendance
    attended_count = db.query(Attendance).join(
        Booking, Attendance.booking_id == Booking.id
    ).filter(
        Booking.member_id == current_user.id,
        Attendance.attended == True
    ).count()
    
    return {
        "membership": membership_info,
        "upcoming_classes": upcoming_classes,
        "total_bookings": total_bookings,
        "attended_classes": attended_count
    }

# PUBLIC_INTERFACE
@router.get("/trainer", summary="Trainer dashboard",
            description="Get dashboard for trainer users")
async def trainer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get trainer dashboard with schedule and class metrics.
    
    Args:
        db: Database session
        current_user: Authenticated trainer user
        
    Returns:
        dict: Dashboard with trainer's classes, bookings, and attendance
        
    Raises:
        HTTPException: If user is not a trainer or has no trainer profile
    """
    if current_user.role != UserRole.trainer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trainer access required"
        )
    
    # Get trainer profile
    trainer = db.query(Trainer).filter(Trainer.user_id == current_user.id).first()
    if not trainer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer profile not found"
        )
    
    # Upcoming classes
    now = datetime.utcnow()
    upcoming_classes = db.query(ClassSchedule).filter(
        ClassSchedule.trainer_id == trainer.id,
        ClassSchedule.start_time >= now
    ).order_by(ClassSchedule.start_time).limit(10).all()
    
    classes_info = []
    for cls in upcoming_classes:
        booked = db.query(Booking).filter(
            Booking.class_id == cls.id,
            Booking.status == BookingStatus.confirmed
        ).count()
        
        classes_info.append({
            "class_id": cls.id,
            "title": cls.title,
            "start_time": cls.start_time.isoformat(),
            "end_time": cls.end_time.isoformat(),
            "room": cls.room,
            "booked": booked,
            "capacity": cls.capacity
        })
    
    # Total classes assigned
    total_classes = db.query(ClassSchedule).filter(
        ClassSchedule.trainer_id == trainer.id
    ).count()
    
    # Total bookings for trainer's classes
    total_bookings = db.query(Booking).join(
        ClassSchedule, Booking.class_id == ClassSchedule.id
    ).filter(
        ClassSchedule.trainer_id == trainer.id,
        Booking.status == BookingStatus.confirmed
    ).count()
    
    return {
        "trainer_name": current_user.full_name,
        "specialties": trainer.specialties,
        "upcoming_classes": classes_info,
        "total_classes": total_classes,
        "total_bookings": total_bookings
    }
