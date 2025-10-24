from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User
from src.schemas.user import UserCreate, UserResponse, TokenResponse
from src.auth.password import get_password_hash, verify_password
from src.auth.jwt_handler import create_access_token
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# PUBLIC_INTERFACE
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED,
             summary="Register a new user",
             description="Create a new user account and return authentication token")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user in the system.
    
    Args:
        user_data: User registration data including email, password, full_name, and role
        db: Database session
        
    Returns:
        TokenResponse: Authentication token and user information
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": new_user.id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(new_user)
    )

# PUBLIC_INTERFACE
@router.post("/login", response_model=TokenResponse,
             summary="Login user",
             description="Authenticate user and return access token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return access token.
    
    Args:
        form_data: OAuth2 password form with username (email) and password
        db: Database session
        
    Returns:
        TokenResponse: Authentication token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email (username field contains email)
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

# PUBLIC_INTERFACE
@router.get("/me", response_model=UserResponse,
            summary="Get current user",
            description="Retrieve the currently authenticated user's information")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    
    Args:
        current_user: The authenticated user from JWT token
        
    Returns:
        UserResponse: Current user information
    """
    return UserResponse.from_orm(current_user)
