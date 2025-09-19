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
from .core.database import init_database, check_db_health
from .core.secrets import validate_production_setup
from .core.encryption import is_encryption_initialized
from .middleware import (
    setup_cors,
    ErrorHandlerMiddleware,
    setup_exception_handlers,
    LoggingMiddleware,
    setup_logging,
    RequestIdMiddleware,
)
from .middleware.security_headers import SecurityHeadersMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .routers import (
    auth_router,
    users_router,
    accounts_router,
    transactions_router,
    plaid_router,
    ml_router,
    bookkeeping_router,
)
from .routers.categories import router as categories_router
from .routers.reports import router as reports_router
from .routers.dashboard import router as dashboard_router
from .routers.tax_categorization import router as tax_router
from .schemas.common import HealthCheck
from .utils.redis import check_redis_connection
from .core.audit import log_audit_event, AuditEventType, AuditSeverity

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

    # Validate production setup
    try:
        if settings.environment == "production":
            validate_production_setup()
            logger.info("Production security validation passed")
    except Exception as e:
        logger.error(f"Production security validation failed: {e}")
        raise

    # Check encryption initialization
    if not is_encryption_initialized():
        logger.warning("Field encryption not initialized")
        if settings.field_encryption_enabled:
            logger.error("Encryption enabled but not initialized")
            if settings.environment == "production":
                raise RuntimeError("Encryption required but not available")

    # Initialize database with security
    try:
        init_database()
        logger.info("Secure database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Don't fail startup in development
        if settings.environment == "production":
            raise

    # Log application startup
    log_audit_event(
        AuditEventType.SYSTEM_START,
        f"Manna API started in {settings.environment} environment",
        severity=AuditSeverity.MEDIUM,
        metadata={
            "version": settings.app_version,
            "environment": settings.environment,
            "encryption_enabled": is_encryption_initialized()
        }
    )
    
    # Check connections with enhanced health checks
    db_health = check_db_health()
    redis_status = await check_redis_connection()

    db_status = db_health.get("status") == "healthy"
    logger.info(f"Database connection: {'OK' if db_status else 'FAILED'}")
    logger.info(f"Redis connection: {'OK' if redis_status else 'FAILED'}")

    if not db_status and settings.environment == "production":
        logger.error("Database health check failed in production")
        raise RuntimeError("Database not available")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Manna Financial Platform API...")

    # Log application shutdown
    log_audit_event(
        AuditEventType.SYSTEM_STOP,
        "Manna API shutting down",
        severity=AuditSeverity.MEDIUM
    )


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

# Add security middleware first
if settings.security_headers_enabled:
    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=settings.environment == "production"
    )

if settings.rate_limiting_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        requests_per_hour=1000
    )

# Add standard middleware
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
app.include_router(reports_router, prefix=f"{settings.api_prefix}/reports", tags=["Reports"])
app.include_router(dashboard_router, prefix=f"{settings.api_prefix}/dashboard", tags=["Dashboard"])
app.include_router(bookkeeping_router, prefix=f"{settings.api_prefix}/bookkeeping", tags=["Bookkeeping"])
app.include_router(tax_router, tags=["Tax Categorization"])


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
    # Enhanced health check with security status
    db_health = check_db_health()
    redis_status = await check_redis_connection()

    # Overall status based on critical components
    overall_status = "healthy"
    if db_health.get("status") != "healthy":
        overall_status = "unhealthy"
    elif not redis_status:
        overall_status = "degraded"

    return HealthCheck(
        status=overall_status,
        timestamp=datetime.utcnow(),
        environment=settings.environment,
        version=settings.app_version,
        database=db_health.get("status") == "healthy",
        redis=redis_status,
        # Add security status
        security={
            "encryption_enabled": is_encryption_initialized(),
            "security_headers": settings.security_headers_enabled,
            "rate_limiting": settings.rate_limiting_enabled,
            "audit_logging": settings.audit_logging_enabled
        },
        database_details=db_health if settings.environment != "production" else None
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