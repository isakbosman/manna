"""
Manna Financial Platform - Backend API
FastAPI application for financial data processing and management.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from typing import Dict, Any

app = FastAPI(
    title="Manna Financial Platform API",
    description="Backend API for financial data processing and management",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint returning API information."""
    return {
        "name": "Manna Financial Platform API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@app.get("/api/accounts")
async def get_accounts() -> Dict[str, Any]:
    """Get all connected accounts."""
    # Placeholder implementation
    return {
        "accounts": [],
        "total": 0
    }


@app.get("/api/transactions")
async def get_transactions() -> Dict[str, Any]:
    """Get transactions for connected accounts."""
    # Placeholder implementation
    return {
        "transactions": [],
        "total": 0,
        "page": 1,
        "per_page": 50
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )