"""
Manna Financial Platform - Backend API
FastAPI application for financial data processing and management.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any
from datetime import datetime

from .config import settings
from .database import init_db, check_db_connection
from .middleware import (
    setup_cors,
    ErrorHandlerMiddleware,
    setup_exception_handlers,
    LoggingMiddleware,
    setup_logging,
    RequestIdMiddleware,
)
from .routers import (
    auth_router,
    users_router,
    accounts_router,
    transactions_router,
    plaid_router,
    ml_router,
)
from .routers.categories import router as categories_router
from .schemas.common import HealthCheck
from .utils.redis import check_redis_connection

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events.
    """
    # Startup
    logger.info("Starting Manna Financial Platform API...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Don't fail startup in development
        if settings.environment == "production":
            raise
    
    # Check connections
    db_status = check_db_connection()
    redis_status = await check_redis_connection()
    logger.info(f"Database connection: {'OK' if db_status else 'FAILED'}")
    logger.info(f"Redis connection: {'OK' if redis_status else 'FAILED'}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Manna Financial Platform API...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Backend API for financial data processing and management",
    version=settings.app_version,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add trusted host middleware in production
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.manna.finance", "manna.finance"]
    )

# Setup CORS
setup_cors(app)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(auth_router, prefix=f"{settings.api_prefix}/auth", tags=["Authentication"])
app.include_router(users_router, prefix=f"{settings.api_prefix}/users", tags=["Users"])
app.include_router(accounts_router, prefix=f"{settings.api_prefix}/accounts", tags=["Accounts"])
app.include_router(transactions_router, prefix=f"{settings.api_prefix}/transactions", tags=["Transactions"])
app.include_router(categories_router, prefix=f"{settings.api_prefix}/categories", tags=["Categories"])
app.include_router(plaid_router, prefix=f"{settings.api_prefix}/plaid", tags=["Plaid"])
app.include_router(ml_router, prefix=f"{settings.api_prefix}/ml", tags=["Machine Learning"])


@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """
    Root endpoint returning API information.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs" if settings.environment != "production" else "disabled",
    }


@app.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """
    Health check endpoint for monitoring.
    """
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        environment=settings.environment,
        version=settings.app_version,
        database=check_db_connection(),
        redis=await check_redis_connection(),
    )


@app.get(f"{settings.api_prefix}/health", response_model=HealthCheck)
async def api_health_check() -> HealthCheck:
    """
    API health check endpoint.
    """
    return await health_check()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )