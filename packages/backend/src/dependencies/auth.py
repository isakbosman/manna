"""
Authentication dependencies for FastAPI routes.
DISABLED FOR LOCAL DEVELOPMENT - Always returns a default user.
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from ..database import get_db
from ..database.models import User
from ..schemas.user import TokenData

# OAuth2 scheme for token authentication (disabled)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user_token(token: Optional[str] = Depends(oauth2_scheme)) -> TokenData:
    """
    DISABLED - Always returns a default token data for local development.
    """
    # Always return a default user token
    return TokenData(
        user_id="default-user-id",
        email="local@manna.finance",
        scopes=["read", "write", "admin"]
    )


async def get_current_user(
    token_data: Annotated[TokenData, Depends(get_current_user_token)],
    db: Session = Depends(get_db)
) -> User:
    """
    DISABLED - Always returns or creates the first user for local development.
    """
    # Get the first user from the database
    user = db.query(User).first()

    if user is None:
        # Create a default user with a random UUID
        user = User(
            id=uuid.uuid4(),
            email="local@manna.finance",
            username="localuser",
            full_name="Local User",
            is_active=True,
            is_superuser=True,
            is_verified=True,
            hashed_password="dummy_hash"
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except:
            db.rollback()
            # Try to get the first user again in case of race condition
            user = db.query(User).first()
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not create or find user"
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
    DISABLED - Always returns the current user for local development.
    """
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
        DISABLED - Always returns user for local development.
        """
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
    DISABLED - Always returns the default user for local development.
    """
    return await get_current_user(
        await get_current_user_token(token),
        db
    )