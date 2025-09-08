"""FastAPI main application for Manna Financial Management."""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from ..utils.database import init_database, get_session
from .plaid_client import PlaidClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    logger.info("Starting Manna API...")
    try:
        # Initialize database
        init_database()
        logger.info("Database initialized")
        
        # Initialize Plaid client
        app.state.plaid_client = PlaidClient()
        logger.info("Plaid client initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Manna API...")


# Create FastAPI application
app = FastAPI(
    title="Manna Financial Management API",
    description="API for financial transaction management and reporting",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "manna-api",
        "version": "1.0.0"
    }


@app.get("/api/status")
async def api_status() -> Dict[str, Any]:
    """API status endpoint with more detailed information."""
    try:
        # Check database connection
        session = get_session()
        session.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        db_status = "disconnected"
    
    return {
        "api": "online",
        "database": db_status,
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }


@app.get("/api/accounts")
async def get_accounts() -> Dict[str, Any]:
    """Get all accounts."""
    try:
        session = get_session()
        # This would typically query the accounts table
        # For now, return a placeholder response
        return {
            "accounts": [],
            "total": 0
        }
    except Exception as e:
        logger.error(f"Failed to fetch accounts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch accounts")


@app.get("/api/transactions")
async def get_transactions(
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """Get transactions with pagination."""
    try:
        session = get_session()
        # This would typically query the transactions table
        # For now, return a placeholder response
        return {
            "transactions": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Failed to fetch transactions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")


@app.post("/api/plaid/link_token")
async def create_link_token() -> Dict[str, Any]:
    """Create Plaid Link token."""
    try:
        plaid_client = app.state.plaid_client
        link_token = plaid_client.create_link_token("manna-user")
        return {"link_token": link_token}
    except Exception as e:
        logger.error(f"Failed to create link token: {e}")
        raise HTTPException(status_code=500, detail="Failed to create link token")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
