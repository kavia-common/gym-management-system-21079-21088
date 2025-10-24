from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from src.database.connection import get_db
from src.database.models import MembershipPlan, Membership, User, MembershipStatus
from src.schemas.membership import (
    MembershipPlanCreate, MembershipPlanUpdate, MembershipPlanResponse,
    MembershipCreate, MembershipResponse
)
from src.auth.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/api/memberships", tags=["Memberships"])

# Membership Plans

# PUBLIC_INTERFACE
@router.get("/plans", response_model=List[MembershipPlanResponse],
            summary="List all membership plans",
            description="Retrieve all available membership plans")
async def list_plans(db: Session = Depends(get_db)):
    """
    Get all available membership plans.
    
    Args:
        db: Database session
        
    Returns:
        List[MembershipPlanResponse]: List of membership plans
    """
    plans = db.query(MembershipPlan).all()
    return plans

# PUBLIC_INTERFACE
@router.post("/plans", response_model=MembershipPlanResponse, status_code=status.HTTP_201_CREATED,
             summary="Create membership plan",
             description="Create a new membership plan (admin only)")
async def create_plan(
    plan_data: MembershipPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new membership plan. Requires admin role.
    
    Args:
        plan_data: Membership plan data
        db: Database session
        current_user: Authenticated admin user
        
    Returns:
        MembershipPlanResponse: Created membership plan
        
    Raises:
        HTTPException: If plan name already exists
    """
    # Check if plan with same name exists
    existing_plan = db.query(MembershipPlan).filter(
        MembershipPlan.name == plan_data.name
    ).first()
    
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan with this name already exists"
        )
    
    new_plan = MembershipPlan(**plan_data.dict())
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    
    return new_plan

# PUBLIC_INTERFACE
@router.put("/plans/{plan_id}", response_model=MembershipPlanResponse,
            summary="Update membership plan",
            description="Update an existing membership plan (admin only)")
async def update_plan(
    plan_id: int,
    plan_data: MembershipPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update a membership plan. Requires admin role.
    
    Args:
        plan_id: Plan ID to update
        plan_data: Updated plan data
        db: Database session
        current_user: Authenticated admin user
        
    Returns:
        MembershipPlanResponse: Updated membership plan
        
    Raises:
        HTTPException: If plan not found
    """
    plan = db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found"
        )
    
    # Update only provided fields
    update_data = plan_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)
    
    db.commit()
    db.refresh(plan)
    
    return plan

# PUBLIC_INTERFACE
@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete membership plan",
               description="Delete a membership plan (admin only)")
async def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete a membership plan. Requires admin role.
    
    Args:
        plan_id: Plan ID to delete
        db: Database session
        current_user: Authenticated admin user
        
    Raises:
        HTTPException: If plan not found
    """
    plan = db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found"
        )
    
    db.delete(plan)
    db.commit()

# Member Memberships

# PUBLIC_INTERFACE
@router.get("/", response_model=List[MembershipResponse],
            summary="List memberships",
            description="List all memberships (admin) or current user's memberships")
async def list_memberships(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get memberships. Admins see all, members see their own.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List[MembershipResponse]: List of memberships
    """
    if current_user.role == "admin":
        memberships = db.query(Membership).all()
    else:
        memberships = db.query(Membership).filter(
            Membership.member_id == current_user.id
        ).all()
    
    return memberships

# PUBLIC_INTERFACE
@router.post("/", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED,
             summary="Create membership",
             description="Create a new membership for a member (admin only)")
async def create_membership(
    membership_data: MembershipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new membership for a member. Requires admin role.
    
    Args:
        membership_data: Membership data with member_id and plan_id
        db: Database session
        current_user: Authenticated admin user
        
    Returns:
        MembershipResponse: Created membership
        
    Raises:
        HTTPException: If member or plan not found
    """
    # Verify member exists
    member = db.query(User).filter(User.id == membership_data.member_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Verify plan exists
    plan = db.query(MembershipPlan).filter(
        MembershipPlan.id == membership_data.plan_id
    ).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership plan not found"
        )
    
    # Calculate dates
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=plan.duration_days)
    
    new_membership = Membership(
        member_id=membership_data.member_id,
        plan_id=membership_data.plan_id,
        start_date=start_date,
        end_date=end_date,
        status=MembershipStatus.active
    )
    
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    
    return new_membership

# PUBLIC_INTERFACE
@router.patch("/{membership_id}/cancel", response_model=MembershipResponse,
              summary="Cancel membership",
              description="Cancel a membership (admin only)")
async def cancel_membership(
    membership_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Cancel a membership. Requires admin role.
    
    Args:
        membership_id: Membership ID to cancel
        db: Database session
        current_user: Authenticated admin user
        
    Returns:
        MembershipResponse: Updated membership
        
    Raises:
        HTTPException: If membership not found
    """
    membership = db.query(Membership).filter(Membership.id == membership_id).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
    
    membership.status = MembershipStatus.cancelled
    db.commit()
    db.refresh(membership)
    
    return membership
