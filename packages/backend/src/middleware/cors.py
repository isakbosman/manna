"""
CORS middleware configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging

from ..config import settings

logger = logging.getLogger(__name__)


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    origins = settings.allowed_origins
    
    # Add localhost variations in development
    if settings.environment == "development":
        origins.extend([
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ])
    
    # Remove duplicates
    origins = list(set(origins))
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    logger.info(f"CORS configured with origins: {origins}")