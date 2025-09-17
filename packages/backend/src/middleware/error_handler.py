"""
Global error handling middleware and exception handlers.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback
from typing import Any, Dict, Callable
from datetime import datetime
import uuid

from ..schemas.common import ErrorResponse, ErrorDetail
from ..config import settings

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling uncaught exceptions.
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            logger.error(
                f"Unhandled exception for request {request_id}: {str(e)}",
                exc_info=True,
                extra={"request_id": request_id, "path": request.url.path}
            )
            
            # Don't expose internal errors in production
            if settings.environment == "production":
                message = "An internal error occurred. Please try again later."
                details = None
            else:
                message = str(e)
                details = [{"message": traceback.format_exc()}]
            
            error_response = ErrorResponse(
                error="InternalServerError",
                message=message,
                details=details,
                request_id=request_id,
                timestamp=datetime.utcnow()
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(mode='json')
            )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    error_response = ErrorResponse(
        error=exc.__class__.__name__,
        message=exc.detail,
        request_id=request_id,
        timestamp=datetime.utcnow()
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation errors.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Parse validation errors
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body' prefix
        details.append(ErrorDetail(
            field=field,
            message=error["msg"],
            code=error["type"]
        ))
    
    error_response = ErrorResponse(
        error="ValidationError",
        message="Request validation failed",
        details=details,
        request_id=request_id,
        timestamp=datetime.utcnow()
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode='json')
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle database exceptions.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    logger.error(
        f"Database error for request {request_id}: {str(exc)}",
        exc_info=True,
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    # Don't expose database errors in production
    if settings.environment == "production":
        message = "A database error occurred. Please try again later."
        details = None
    else:
        message = f"Database error: {str(exc)}"
        details = [{"message": str(exc.__class__.__name__)}]
    
    error_response = ErrorResponse(
        error="DatabaseError",
        message=message,
        details=details,
        request_id=request_id,
        timestamp=datetime.utcnow()
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Setup all exception handlers for the application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    
    logger.info("Exception handlers configured")