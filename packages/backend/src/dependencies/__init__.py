"""
FastAPI dependencies for request validation and authentication.
"""

from .auth import (
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    get_optional_current_user,
    require_admin,
    require_staff,
    require_user,
    RoleChecker,
)

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_current_verified_user",
    "get_optional_current_user",
    "require_admin",
    "require_staff",
    "require_user",
    "RoleChecker",
]