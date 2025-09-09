"""
API routers for the Manna Financial Platform.
"""

from .auth import router as auth_router
from .users import router as users_router
from .accounts import router as accounts_router
from .transactions import router as transactions_router
from .plaid import router as plaid_router
from .ml import router as ml_router

__all__ = [
    "auth_router",
    "users_router",
    "accounts_router",
    "transactions_router",
    "plaid_router",
    "ml_router",
]