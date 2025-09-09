"""
Service layer for business logic and external integrations.
"""

from .plaid_service import plaid_service

__all__ = [
    "plaid_service",
]