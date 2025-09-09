"""
Logging middleware and configuration.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import logging.config
import time
from typing import Callable
import json
from datetime import datetime

from ..config import settings


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("api.access")
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for health checks
        if request.url.path in ["/", "/api/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Get request ID
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log request
        self.logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate process time
        process_time = time.time() - start_time
        
        # Add process time header
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        self.logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s",
            }
        )
        
        return response


def setup_logging() -> None:
    """
    Configure logging for the application.
    """
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            } if settings.environment == "production" else None,
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if settings.environment == "production" else "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json" if settings.environment == "production" else "default",
                "filename": "/app/logs/app.log" if settings.environment != "development" else "app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            } if settings.environment != "development" else None,
        },
        "loggers": {
            "": {
                "level": settings.log_level,
                "handlers": ["console"] + (["file"] if settings.environment != "development" else []),
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING" if not settings.database_echo else "INFO",
                "propagate": False,
            },
            "api.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    
    # Remove None values from config
    log_config = _remove_none_values(log_config)
    
    logging.config.dictConfig(log_config)
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {settings.environment} environment")


def _remove_none_values(d: dict) -> dict:
    """
    Recursively remove None values from dictionary.
    """
    if not isinstance(d, dict):
        return d
    return {
        k: _remove_none_values(v)
        for k, v in d.items()
        if v is not None
    }