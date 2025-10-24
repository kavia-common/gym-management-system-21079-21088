from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database.connection import get_db
from src.database.models import Trainer, User, ClassSchedule, UserRole
from src.schemas.trainer import TrainerCreate, TrainerUpdate, TrainerResponse
from src.schemas.class_schedule import ClassScheduleResponse
from src.auth.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/api/trainers", tags=["Trainers"])

# PUBLIC_INTERFACE
@router.get("/", response_model=List[TrainerResponse],
            summary="List all trainers",
            description="Retrieve all trainer profiles")
async def list_trainers(db: Session = Depends(get_db)):
    """
    Get all trainer profiles.
    
    Args:
        db: Database session
        
    Returns:
        List[TrainerResponse]: List of trainer profiles
    """
    trainers = db.query(Trainer).all()
    return trainers

# PUBLIC_INTERFACE
@router.get("/{trainer_id}", response_model=TrainerResponse,
            summary="Get trainer profile",
            description="Retrieve a specific trainer's profile")
async def get_trainer(trainer_id: int, db: Session = Depends(get_db)):
    """
    Get a specific trainer's profile.
    
    Args:
        trainer_id: Trainer ID
        db: Database session
        
    Returns:
        TrainerResponse: Trainer profile
        
    Raises:
        HTTPException: If trainer not found
    """
    trainer = db.query(Trainer).filter(Trainer.id == trainer_id).first()
    
    if not trainer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer not found"
        )
    
    return trainer

# PUBLIC_INTERFACE
@router.get("/{trainer_id}/classes", response_model=List[ClassScheduleResponse],
            summary="Get trainer's classes",
            description="Retrieve all classes assigned to a trainer")
async def get_trainer_classes(trainer_id: int, db: Session = Depends(get_db)):
    """
    Get all classes assigned to a specific trainer.
    
    Args:
        trainer_id: Trainer ID
        db: Database session
        
    Returns:
        List[ClassScheduleResponse]: List of classes
        
    Raises:
        HTTPException: If trainer not found
    """
    trainer = db.query(Trainer).filter(Trainer.id == trainer_id).first()
    
    if not trainer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer not found"
        )
    
    classes = db.query(ClassSchedule).filter(
        ClassSchedule.trainer_id == trainer_id
    ).order_by(ClassSchedule.start_time).all()
    
    # Add booked_count to response
    from src.database.models import Booking, BookingStatus
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
@router.post("/", response_model=TrainerResponse, status_code=status.HTTP_201_CREATED,
             summary="Create trainer profile",
             description="Create a new trainer profile (admin only)")
async def create_trainer(
    trainer_data: TrainerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new trainer profile. Requires admin role.
    
    Args:
        trainer_data: Trainer profile data
        db: Database session
        current_user: Authenticated admin user
        
    Returns:
        TrainerResponse: Created trainer profile
        
    Raises:
        HTTPException: If user not found, not a trainer, or profile already exists
    """
    # Verify user exists and is a trainer
    user = db.query(User).filter(User.id == trainer_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.role != UserRole.trainer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must have trainer role"
        )
    
    # Check if trainer profile already exists
    existing_trainer = db.query(Trainer).filter(
        Trainer.user_id == trainer_data.user_id
    ).first()
    if existing_trainer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trainer profile already exists for this user"
        )
    
    new_trainer = Trainer(**trainer_data.dict())
    db.add(new_trainer)
    db.commit()
    db.refresh(new_trainer)
    
    return new_trainer

# PUBLIC_INTERFACE
@router.put("/{trainer_id}", response_model=TrainerResponse,
            summary="Update trainer profile",
            description="Update a trainer's profile (admin or own profile)")
async def update_trainer(
    trainer_id: int,
    trainer_data: TrainerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a trainer profile. Admin can update any, trainers can update their own.
    
    Args:
        trainer_id: Trainer ID to update
        trainer_data: Updated trainer data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        TrainerResponse: Updated trainer profile
        
    Raises:
        HTTPException: If trainer not found or permission denied
    """
    trainer = db.query(Trainer).filter(Trainer.id == trainer_id).first()
    
    if not trainer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer not found"
        )
    
    # Check permissions - admin or own profile
    if current_user.role != UserRole.admin and trainer.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update only provided fields
    update_data = trainer_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(trainer, key, value)
    
    db.commit()
    db.refresh(trainer)
    
    return trainer

# PUBLIC_INTERFACE
@router.delete("/{trainer_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete trainer profile",
               description="Delete a trainer profile (admin only)")
async def delete_trainer(
    trainer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a trainer profile. Requires admin role.
    
    Args:
        trainer_id: Trainer ID to delete
        db: Database session
        current_user: Authenticated admin user
        
    Raises:
        HTTPException: If trainer not found
    """
    trainer = db.query(Trainer).filter(Trainer.id == trainer_id).first()
    
    if not trainer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer not found"
        )
    
    db.delete(trainer)
    db.commit()
