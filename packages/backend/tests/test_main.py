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
    assert data["name"] == "Manna Financial Platform API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"


def test_health_check() -> None:
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "environment" in data


def test_accounts_endpoint() -> None:
    """Test the accounts endpoint returns empty list initially."""
    response = client.get("/api/accounts")
    assert response.status_code == 200
    data = response.json()
    assert data["accounts"] == []
    assert data["total"] == 0


def test_transactions_endpoint() -> None:
    """Test the transactions endpoint returns empty list initially."""
    response = client.get("/api/transactions")
    assert response.status_code == 200
    data = response.json()
    assert data["transactions"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["per_page"] == 50