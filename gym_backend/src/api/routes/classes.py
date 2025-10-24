from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from src.database.connection import get_db
from src.database.models import ClassSchedule, Trainer, User, Booking, BookingStatus
from src.schemas.class_schedule import (
    ClassScheduleCreate, ClassScheduleUpdate, ClassScheduleResponse
)
from src.auth.dependencies import get_current_admin

router = APIRouter(prefix="/api/classes", tags=["Classes"])

# PUBLIC_INTERFACE
@router.get("/", response_model=List[ClassScheduleResponse],
            summary="List all classes",
            description="Retrieve all scheduled classes with optional date filtering")
async def list_classes(
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db)
):
    """
    Get all scheduled classes with optional date filtering.
    
    Args:
        start_date: Optional filter for classes starting after this date
        end_date: Optional filter for classes starting before this date
        db: Database session
        
    Returns:
        List[ClassScheduleResponse]: List of class schedules with booking counts
    """
    query = db.query(ClassSchedule)
    
    if start_date:
        query = query.filter(ClassSchedule.start_time >= start_date)
    if end_date:
        query = query.filter(ClassSchedule.start_time <= end_date)
    
    classes = query.order_by(ClassSchedule.start_time).all()
    
    # Add booked count to each class
    result = []
    for cls in classes:
        booked_count = db.query(Booking).filter(
            Booking.class_id == cls.id,
            Booking.status == BookingStatus.confirmed
        ).count()
        
        class_dict = ClassScheduleResponse.from_orm(cls).dict()
        class_dict['booked_count'] = booked_count
        result.append(ClassScheduleResponse(**class_dict))
    
    return result

# PUBLIC_INTERFACE
@router.get("/{class_id}", response_model=ClassScheduleResponse,
            summary="Get class details",
            description="Retrieve details of a specific class")
async def get_class(class_id: int, db: Session = Depends(get_db)):
    """
    Get details of a specific class.
    
    Args:
        class_id: Class ID
        db: Database session
        
    Returns:
        ClassScheduleResponse: Class details with booking count
        
    Raises:
        HTTPException: If class not found
    """
    cls = db.query(ClassSchedule).filter(ClassSchedule.id == class_id).first()
    
    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    booked_count = db.query(Booking).filter(
        Booking.class_id == cls.id,
        Booking.status == BookingStatus.confirmed
    ).count()
    
    class_dict = ClassScheduleResponse.from_orm(cls).dict()
    class_dict['booked_count'] = booked_count
    
    return ClassScheduleResponse(**class_dict)

# PUBLIC_INTERFACE
@router.post("/", response_model=ClassScheduleResponse, status_code=status.HTTP_201_CREATED,
             summary="Create class",
             description="Create a new class schedule (admin only)")
async def create_class(
    class_data: ClassScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new class schedule. Requires admin role.
    
    Args:
        class_data: Class schedule data
        db: Database session
        current_user: Authenticated admin user
        
    Returns:
        ClassScheduleResponse: Created class schedule
        
    Raises:
        HTTPException: If trainer not found or time validation fails
    """
    # Verify trainer exists
    trainer = db.query(Trainer).filter(Trainer.id == class_data.trainer_id).first()
    if not trainer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer not found"
        )
    
    # Validate end_time > start_time
    if class_data.end_time <= class_data.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    new_class = ClassSchedule(**class_data.dict())
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    
    class_dict = ClassScheduleResponse.from_orm(new_class).dict()
    class_dict['booked_count'] = 0
    
    return ClassScheduleResponse(**class_dict)

# PUBLIC_INTERFACE
@router.put("/{class_id}", response_model=ClassScheduleResponse,
            summary="Update class",
            description="Update an existing class schedule (admin only)")
async def update_class(
    class_id: int,
    class_data: ClassScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update a class schedule. Requires admin role.
    
    Args:
        class_id: Class ID to update
        class_data: Updated class data
        db: Database session
        current_user: Authenticated admin user
        
    Returns:
        ClassScheduleResponse: Updated class schedule
        
    Raises:
        HTTPException: If class not found or validation fails
    """
    cls = db.query(ClassSchedule).filter(ClassSchedule.id == class_id).first()
    
    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Update only provided fields
    update_data = class_data.dict(exclude_unset=True)
    
    # Verify trainer if being updated
    if 'trainer_id' in update_data:
        trainer = db.query(Trainer).filter(
            Trainer.id == update_data['trainer_id']
        ).first()
        if not trainer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trainer not found"
            )
    
    for key, value in update_data.items():
        setattr(cls, key, value)
    
    # Validate times if both are present
    if cls.end_time <= cls.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    db.commit()
    db.refresh(cls)
    
    booked_count = db.query(Booking).filter(
        Booking.class_id == cls.id,
        Booking.status == BookingStatus.confirmed
    ).count()
    
    class_dict = ClassScheduleResponse.from_orm(cls).dict()
    class_dict['booked_count'] = booked_count
    
    return ClassScheduleResponse(**class_dict)

# PUBLIC_INTERFACE
@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete class",
               description="Delete a class schedule (admin only)")
async def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a class schedule. Requires admin role.
    
    Args:
        class_id: Class ID to delete
        db: Database session
        current_user: Authenticated admin user
        
    Raises:
        HTTPException: If class not found
    """
    cls = db.query(ClassSchedule).filter(ClassSchedule.id == class_id).first()
    
    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    db.delete(cls)
    db.commit()
