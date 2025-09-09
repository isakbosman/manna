"""
Users router - placeholder for Task 2.2.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, List

router = APIRouter()


@router.get("/me")
async def get_current_user() -> Dict[str, str]:
    """
    Get current user profile - to be implemented in Task 2.2.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User endpoints will be implemented in Task 2.2"
    )


@router.put("/me")
async def update_current_user() -> Dict[str, str]:
    """
    Update current user profile - to be implemented in Task 2.2.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User endpoints will be implemented in Task 2.2"
    )


@router.delete("/me")
async def delete_current_user() -> Dict[str, str]:
    """
    Delete current user account - to be implemented in Task 2.2.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User endpoints will be implemented in Task 2.2"
    )


@router.post("/me/change-password")
async def change_password() -> Dict[str, str]:
    """
    Change user password - to be implemented in Task 2.2.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User endpoints will be implemented in Task 2.2"
    )