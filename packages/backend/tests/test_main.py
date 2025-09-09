"""
Tests for the main FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Test the root endpoint returns correct information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Manna Financial Platform"
    assert data["version"] == "1.0.0"
    assert data["environment"] == "development"


def test_health_check() -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "environment" in data
    assert "version" in data


def test_accounts_endpoint_unauthorized() -> None:
    """Test the accounts endpoint requires authentication."""
    response = client.get("/api/v1/accounts/")
    assert response.status_code == 401


def test_transactions_endpoint_unauthorized() -> None:
    """Test the transactions endpoint requires authentication."""
    response = client.get("/api/v1/transactions/")
    assert response.status_code == 401


def test_api_health_check() -> None:
    """Test the API health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "environment" in data