"""
Authentication dependencies for FastAPI routes.
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from ..database import get_db
from ..database.models import User
from ..utils.security import decode_token
from ..schemas.user import TokenData

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user_token(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    """
    Extract and validate user information from JWT token.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        TokenData with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        
        # Verify this is an access token
        if payload.get("type") != "access":
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        token_data = TokenData(
            user_id=user_id,
            email=payload.get("email"),
            scopes=payload.get("scopes", [])
        )
        
    except JWTError:
        raise credentials_exception
    
    return token_data


async def get_current_user(
    token_data: Annotated[TokenData, Depends(get_current_user_token)],
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the database.
    
    Args:
        token_data: Validated token data
        db: Database session
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If user not found or inactive
    """
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Ensure the current user is active.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user


async def get_current_verified_user(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Ensure the current user has verified their email.
    
    Args:
        current_user: Current active user
        
    Returns:
        Verified user object
        
    Raises:
        HTTPException: If user email is not verified
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email to continue."
        )
    
    return current_user


class RoleChecker:
    """
    Dependency class for checking user roles.
    """
    
    def __init__(self, allowed_roles: list[str]):
        """
        Initialize role checker with allowed roles.
        
        Args:
            allowed_roles: List of roles that are allowed access
        """
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        """
        Check if user has required role.
        
        Args:
            user: Current authenticated user
            
        Returns:
            User if they have required role
            
        Raises:
            HTTPException: If user lacks required role
        """
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user.role}' not authorized for this operation"
            )
        
        return user


# Convenience dependencies for common role checks
require_admin = RoleChecker(["admin"])
require_staff = RoleChecker(["admin", "staff"])
require_user = RoleChecker(["admin", "staff", "user"])


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that have optional authentication.
    
    Args:
        token: Optional JWT token
        db: Database session
        
    Returns:
        User object or None
    """
    if not token:
        return None
    
    try:
        token_data = await get_current_user_token(token)
        user = await get_current_user(token_data, db)
        return user
    except HTTPException:
        return None