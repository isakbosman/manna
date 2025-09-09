"""Tests for Plaid integration endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta

from src.database.models import User, PlaidItem, Institution, Account, Transaction


class TestPlaidLinkEndpoints:
    """Test suite for Plaid Link endpoints."""
    
    def test_create_link_token(
        self,
        client: TestClient,
        auth_headers: dict,
        mock_plaid_service
    ):
        """Test creating a Plaid Link token."""
        # Mock successful token creation
        mock_plaid_service.create_link_token.return_value = {
            "link_token": "link-sandbox-12345",
            "expiration": datetime.utcnow() + timedelta(minutes=30),
            "request_id": "req-123"
        }
        
        response = client.post("/api/v1/plaid/create-link-token", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "link_token" in data
        assert "expiration" in data
        assert data["link_token"] == "link-sandbox-12345"
    
    def test_create_link_token_with_access_token(
        self,
        client: TestClient,
        auth_headers: dict,
        mock_plaid_service
    ):
        """Test creating Link token for update mode."""
        mock_plaid_service.create_link_token.return_value = {
            "link_token": "link-update-12345",
            "expiration": datetime.utcnow() + timedelta(minutes=30)
        }
        
        response = client.post(
            "/api/v1/plaid/create-link-token?access_token=access-token-123",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify update mode was used
        mock_plaid_service.create_link_token.assert_called_with(
            user_id=str(response.json().get("user_id", "")),
            user_name=pytest.any(str),
            access_token="access-token-123"
        )
    
    def test_create_link_token_failure(
        self,
        client: TestClient,
        auth_headers: dict,
        mock_plaid_service
    ):
        """Test Link token creation failure."""
        mock_plaid_service.create_link_token.side_effect = Exception("Plaid API error")
        
        response = client.post("/api/v1/plaid/create-link-token", headers=auth_headers)
        assert response.status_code == 500
    
    def test_exchange_public_token(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session,
        mock_plaid_service
    ):
        """Test exchanging public token for access token."""
        # Mock Plaid service responses
        mock_plaid_service.exchange_public_token.return_value = "access-sandbox-12345"
        mock_plaid_service.get_item.return_value = {
            "item_id": "item-123",
            "institution_id": "ins_1",
            "webhook": "https://example.com/webhook",
            "available_products": ["transactions"],
            "billed_products": ["transactions"],
            "consent_expiration_time": None
        }
        mock_plaid_service.get_institution.return_value = {
            "institution_id": "ins_1",
            "name": "Test Bank",
            "url": "https://testbank.com",
            "primary_color": "#1f77b4",
            "logo": "https://testbank.com/logo.png"
        }
        mock_plaid_service.get_accounts.return_value = [
            {
                "account_id": "acc_1",
                "name": "Test Checking",
                "official_name": "Test Checking Account",
                "type": "depository",
                "subtype": "checking",
                "mask": "1234",
                "current_balance": 1500.00,
                "available_balance": 1450.00,
                "limit": None,
                "iso_currency_code": "USD"
            }
        ]
        
        exchange_data = {
            "public_token": "public-sandbox-12345",
            "metadata": {"institution": {"name": "Test Bank"}}
        }
        
        response = client.post(
            "/api/v1/plaid/exchange-public-token",
            json=exchange_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "item_id" in data
        assert "institution" in data
        assert "accounts_connected" in data
        assert data["accounts_connected"] == 1
        
        # Verify database records were created
        plaid_item = db_session.query(PlaidItem).filter(
            PlaidItem.user_id == test_user.id
        ).first()
        assert plaid_item is not None
        assert plaid_item.plaid_item_id == "item-123"
        assert plaid_item.access_token == "access-sandbox-12345"
        
        account = db_session.query(Account).filter(
            Account.user_id == test_user.id
        ).first()
        assert account is not None
        assert account.plaid_account_id == "acc_1"
        assert account.name == "Test Checking"
    
    def test_exchange_public_token_existing_item(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session,
        mock_plaid_service
    ):
        """Test updating existing Plaid item."""
        # Create existing institution and item
        institution = Institution(
            plaid_institution_id="ins_1",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        existing_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="item-123",
            access_token="old-token",
            is_active=False  # Item was previously deactivated
        )
        db_session.add(existing_item)
        db_session.commit()
        
        # Mock Plaid responses for update
        mock_plaid_service.exchange_public_token.return_value = "new-access-token"
        mock_plaid_service.get_item.return_value = {
            "item_id": "item-123",  # Same item ID
            "institution_id": "ins_1",
            "webhook": "https://example.com/webhook"
        }
        mock_plaid_service.get_institution.return_value = {
            "institution_id": "ins_1",
            "name": "Test Bank"
        }
        mock_plaid_service.get_accounts.return_value = []
        
        exchange_data = {"public_token": "public-update-12345"}
        
        response = client.post(
            "/api/v1/plaid/exchange-public-token",
            json=exchange_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify item was updated, not duplicated
        db_session.refresh(existing_item)
        assert existing_item.access_token == "new-access-token"
        assert existing_item.is_active == True
        assert existing_item.error is None
    
    def test_exchange_public_token_failure(
        self,
        client: TestClient,
        auth_headers: dict,
        mock_plaid_service
    ):
        """Test public token exchange failure."""
        mock_plaid_service.exchange_public_token.side_effect = Exception("Invalid token")
        
        exchange_data = {"public_token": "invalid-token"}
        
        response = client.post(
            "/api/v1/plaid/exchange-public-token",
            json=exchange_data,
            headers=auth_headers
        )
        assert response.status_code == 500


class TestPlaidItemManagement:
    """Test Plaid item management endpoints."""
    
    def test_get_linked_items_empty(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test getting linked items when none exist."""
        response = client.get("/api/v1/plaid/items", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data == []
    
    def test_get_linked_items_with_data(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session
    ):
        """Test getting linked items with sample data."""
        # Create test data
        institution = Institution(
            plaid_institution_id="ins_1",
            name="Test Bank",
            logo_url="https://testbank.com/logo.png",
            primary_color="#1f77b4"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="item-123",
            access_token="access-token",
            last_successful_sync=datetime.utcnow()
        )
        db_session.add(plaid_item)
        db_session.flush()
        
        # Create account for item
        account = Account(
            user_id=test_user.id,
            plaid_item_id=plaid_item.id,
            institution_id=institution.id,
            plaid_account_id="acc_1",
            name="Test Account",
            type="depository",
            subtype="checking"
        )
        db_session.add(account)
        db_session.commit()
        
        response = client.get("/api/v1/plaid/items", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        
        item = data[0]
        assert item["item_id"] == str(plaid_item.id)
        assert item["is_active"] == True
        assert item["account_count"] == 1
        assert item["institution"]["name"] == "Test Bank"
    
    def test_remove_linked_item(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session,
        mock_plaid_service
    ):
        """Test removing a linked Plaid item."""
        # Create test item
        institution = Institution(
            plaid_institution_id="ins_1",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="item-123",
            access_token="access-token"
        )
        db_session.add(plaid_item)
        db_session.flush()
        
        account = Account(
            user_id=test_user.id,
            plaid_item_id=plaid_item.id,
            institution_id=institution.id,
            plaid_account_id="acc_1",
            name="Test Account",
            type="depository",
            subtype="checking"
        )
        db_session.add(account)
        db_session.commit()
        
        # Mock successful removal
        mock_plaid_service.remove_item.return_value = True
        
        response = client.delete(f"/api/v1/plaid/items/{plaid_item.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "unlinked successfully" in data["message"]
        
        # Verify item and accounts were deactivated
        db_session.refresh(plaid_item)
        db_session.refresh(account)
        assert plaid_item.is_active == False
        assert plaid_item.access_token is None
        assert account.is_active == False
    
    def test_remove_linked_item_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test removing non-existent item."""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/plaid/items/{fake_id}", headers=auth_headers)
        assert response.status_code == 404


class TestPlaidTransactionSync:
    """Test Plaid transaction synchronization."""
    
    def test_sync_transactions(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session,
        mock_plaid_service
    ):
        """Test manual transaction sync."""
        # Create test item
        institution = Institution(
            plaid_institution_id="ins_1",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="item-123",
            access_token="access-token",
            cursor=None
        )
        db_session.add(plaid_item)
        db_session.commit()
        
        response = client.post(
            f"/api/v1/plaid/transactions/sync/{plaid_item.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "started"
        assert data["item_id"] == str(plaid_item.id)
    
    def test_sync_transactions_in_progress(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session,
        mock_redis_client
    ):
        """Test sync when already in progress."""
        # Create test item
        institution = Institution(
            plaid_institution_id="ins_1",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="item-123",
            access_token="access-token"
        )
        db_session.add(plaid_item)
        db_session.commit()
        
        # Mock Redis lock exists
        mock_redis_client.exists.return_value = True
        
        response = client.post(
            f"/api/v1/plaid/transactions/sync/{plaid_item.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "in_progress"
    
    def test_sync_transactions_item_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test sync for non-existent item."""
        fake_id = uuid4()
        response = client.post(
            f"/api/v1/plaid/transactions/sync/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestPlaidWebhooks:
    """Test Plaid webhook handling."""
    
    def test_webhook_transactions_available(
        self,
        client: TestClient,
        test_user: User,
        db_session: Session,
        mock_plaid_service
    ):
        """Test webhook for new transactions available."""
        # Create test item
        institution = Institution(
            plaid_institution_id="ins_1",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="item-123",
            access_token="access-token"
        )
        db_session.add(plaid_item)
        db_session.commit()
        
        # Mock webhook handling
        mock_plaid_service.handle_webhook.return_value = {
            "action": "fetch_transactions"
        }
        
        webhook_data = {
            "webhook_type": "TRANSACTIONS",
            "webhook_code": "SYNC_UPDATES_AVAILABLE",
            "item_id": "item-123",
            "error": None
        }
        
        response = client.post("/api/v1/plaid/webhook", json=webhook_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "processed"
        assert data["action"] == "fetch_transactions"
    
    def test_webhook_item_error(
        self,
        client: TestClient,
        test_user: User,
        db_session: Session,
        mock_plaid_service
    ):
        """Test webhook for item error."""
        # Create test item
        institution = Institution(
            plaid_institution_id="ins_1",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="item-123",
            access_token="access-token"
        )
        db_session.add(plaid_item)
        db_session.commit()
        
        mock_plaid_service.handle_webhook.return_value = {
            "action": "notify_user"
        }
        
        error_data = {
            "error_type": "ITEM_ERROR",
            "error_code": "ITEM_LOGIN_REQUIRED",
            "error_message": "Login required"
        }
        
        webhook_data = {
            "webhook_type": "ITEM",
            "webhook_code": "ERROR",
            "item_id": "item-123",
            "error": error_data
        }
        
        response = client.post("/api/v1/plaid/webhook", json=webhook_data)
        assert response.status_code == 200
        
        # Verify error was stored
        db_session.refresh(plaid_item)
        assert plaid_item.error is not None
    
    def test_webhook_unknown_item(
        self,
        client: TestClient,
        mock_plaid_service
    ):
        """Test webhook for unknown item."""
        mock_plaid_service.handle_webhook.return_value = {
            "action": "ignore"
        }
        
        webhook_data = {
            "webhook_type": "TRANSACTIONS",
            "webhook_code": "SYNC_UPDATES_AVAILABLE",
            "item_id": "unknown-item",
            "error": None
        }
        
        response = client.post("/api/v1/plaid/webhook", json=webhook_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ignored"
        assert data["reason"] == "item_not_found"


class TestPlaidSecurity:
    """Test Plaid endpoint security."""
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        endpoints = [
            ("/api/v1/plaid/create-link-token", "POST"),
            ("/api/v1/plaid/exchange-public-token", "POST"),
            ("/api/v1/plaid/items", "GET"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            assert response.status_code == 401
    
    def test_item_isolation(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db_session: Session
    ):
        """Test that users can only access their own items."""
        # Create another user's item
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_verified=True
        )
        db_session.add(other_user)
        db_session.flush()
        
        institution = Institution(
            plaid_institution_id="ins_1",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        other_item = PlaidItem(
            user_id=other_user.id,
            institution_id=institution.id,
            plaid_item_id="other-item",
            access_token="other-token"
        )
        db_session.add(other_item)
        db_session.commit()
        
        # Try to access other user's item
        response = client.delete(f"/api/v1/plaid/items/{other_item.id}", headers=auth_headers)
        assert response.status_code == 404
        
        # Try to sync other user's item
        response = client.post(
            f"/api/v1/plaid/transactions/sync/{other_item.id}",
            headers=auth_headers
        )
        assert response.status_code == 404
