from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User, UserRole
from src.auth.jwt_handler import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# PUBLIC_INTERFACE
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

# PUBLIC_INTERFACE
async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify that the current user has admin role.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        User: The authenticated admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# PUBLIC_INTERFACE
async def get_current_trainer(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify that the current user has trainer role.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        User: The authenticated trainer user
        
    Raises:
        HTTPException: If user is not a trainer
    """
    if current_user.role != UserRole.trainer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions - trainer role required"
        )
    return current_user

# PUBLIC_INTERFACE
async def get_current_member(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify that the current user has member role.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        User: The authenticated member user
        
    Raises:
        HTTPException: If user is not a member
    """
    if current_user.role != UserRole.member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions - member role required"
        )
    return current_user
