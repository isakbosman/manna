"""Tests for account management endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime

from src.database.models import User, Account, PlaidItem, Institution
from src.schemas.account import AccountUpdate


class TestAccountEndpoints:
    """Test suite for account management endpoints."""
    
    def test_list_accounts_empty(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test listing accounts when user has none."""
        response = client.get("/api/v1/accounts/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 0
        assert data["accounts"] == []
        assert data["page"] == 1
        assert data["per_page"] == 20
    
    def test_list_accounts_with_data(
        self, 
        client: TestClient, 
        test_user: User, 
        auth_headers: dict,
        sample_account: Account,
        db_session: Session
    ):
        """Test listing accounts with sample data."""
        response = client.get("/api/v1/accounts/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 1
        assert len(data["accounts"]) == 1
        
        account = data["accounts"][0]
        assert account["id"] == str(sample_account.id)
        assert account["name"] == sample_account.name
        assert account["type"] == sample_account.type
        assert account["current_balance"] == (sample_account.current_balance_cents or 0) / 100
    
    def test_list_accounts_pagination(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test account pagination."""
        # Create multiple accounts
        institution = Institution(
            plaid_institution_id="test_inst_1",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="test_item_1",
            access_token="test_token"
        )
        db_session.add(plaid_item)
        db_session.flush()
        
        for i in range(5):
            account = Account(
                user_id=test_user.id,
                plaid_item_id=plaid_item.id,
                institution_id=institution.id,
                plaid_account_id=f"test_account_{i}",
                name=f"Test Account {i}",
                type="depository",
                subtype="checking",
                current_balance_cents=1000 * (i + 1)
            )
            db_session.add(account)
        
        db_session.commit()
        
        # Test first page
        response = client.get("/api/v1/accounts/?per_page=3", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 5
        assert len(data["accounts"]) == 3
        assert data["page"] == 1
        assert data["per_page"] == 3
        
        # Test second page
        response = client.get("/api/v1/accounts/?page=2&per_page=3", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 5
        assert len(data["accounts"]) == 2
        assert data["page"] == 2
    
    def test_list_accounts_filtering(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test account filtering by type and hidden status."""
        institution = Institution(
            plaid_institution_id="test_inst_1",
            name="Test Bank"
        )
        db_session.add(institution)
        db_session.flush()
        
        plaid_item = PlaidItem(
            user_id=test_user.id,
            institution_id=institution.id,
            plaid_item_id="test_item_1",
            access_token="test_token"
        )
        db_session.add(plaid_item)
        db_session.flush()
        
        # Create accounts of different types
        accounts_data = [
            {"type": "depository", "subtype": "checking", "is_hidden": False},
            {"type": "depository", "subtype": "savings", "is_hidden": True},
            {"type": "credit", "subtype": "credit_card", "is_hidden": False},
        ]
        
        for i, data in enumerate(accounts_data):
            account = Account(
                user_id=test_user.id,
                plaid_item_id=plaid_item.id,
                institution_id=institution.id,
                plaid_account_id=f"test_account_{i}",
                name=f"Test Account {i}",
                **data
            )
            db_session.add(account)
        
        db_session.commit()
        
        # Test filtering by type
        response = client.get("/api/v1/accounts/?account_type=depository", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1  # Only non-hidden depository account
        
        # Test including hidden accounts
        response = client.get(
            "/api/v1/accounts/?account_type=depository&include_hidden=true", 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Both depository accounts
    
    def test_get_account(self, client: TestClient, auth_headers: dict, sample_account: Account):
        """Test getting a specific account."""
        response = client.get(f"/api/v1/accounts/{sample_account.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(sample_account.id)
        assert data["name"] == sample_account.name
        assert data["type"] == sample_account.type
        assert data["subtype"] == sample_account.subtype
    
    def test_get_account_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent account."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/accounts/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_account_different_user(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        sample_account: Account,
        db_session: Session
    ):
        """Test that users can't access other users' accounts."""
        # Create another user's account
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_verified=True
        )
        db_session.add(other_user)
        db_session.flush()
        
        other_account = Account(
            user_id=other_user.id,
            plaid_item_id=sample_account.plaid_item_id,
            institution_id=sample_account.institution_id,
            plaid_account_id="other_account",
            name="Other Account",
            type="depository",
            subtype="checking"
        )
        db_session.add(other_account)
        db_session.commit()
        
        response = client.get(f"/api/v1/accounts/{other_account.id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_account(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        sample_account: Account,
        db_session: Session
    ):
        """Test updating account information."""
        update_data = {
            "name": "Updated Account Name",
            "is_hidden": True
        }
        
        response = client.put(
            f"/api/v1/accounts/{sample_account.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Account Name"
        assert data["is_hidden"] == True
        
        # Verify changes in database
        db_session.refresh(sample_account)
        assert sample_account.name == "Updated Account Name"
        assert sample_account.is_hidden == True
    
    def test_update_account_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent account."""
        fake_id = uuid4()
        update_data = {"name": "New Name"}
        
        response = client.put(
            f"/api/v1/accounts/{fake_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_delete_account(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        sample_account: Account,
        db_session: Session
    ):
        """Test soft deleting an account."""
        response = client.delete(f"/api/v1/accounts/{sample_account.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "successfully disconnected" in data["message"]
        
        # Verify account is deactivated, not deleted
        db_session.refresh(sample_account)
        assert sample_account.is_active == False
    
    def test_delete_account_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent account."""
        fake_id = uuid4()
        response = client.delete(f"/api/v1/accounts/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_account_balance(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        sample_account: Account
    ):
        """Test getting account balance."""
        response = client.get(f"/api/v1/accounts/{sample_account.id}/balance", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "account_id" in data
        assert "current_balance" in data
        assert "currency" in data
        assert "as_of" in data
        assert data["account_id"] == str(sample_account.id)
    
    def test_sync_accounts(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_account: Account,
        mock_plaid_service
    ):
        """Test syncing account data."""
        # Mock successful account sync
        mock_plaid_service.get_accounts.return_value = [
            {
                "account_id": sample_account.plaid_account_id,
                "current_balance": 1250.50,
                "available_balance": 1200.00,
                "limit": None
            }
        ]
        
        response = client.post("/api/v1/accounts/sync", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["account_id"] == str(sample_account.id)
        assert data[0]["status"] in ["started", "in_progress"]
    
    def test_sync_specific_accounts(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_account: Account,
        mock_plaid_service
    ):
        """Test syncing specific accounts."""
        mock_plaid_service.get_accounts.return_value = []
        
        response = client.post(
            f"/api/v1/accounts/sync?account_ids={sample_account.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_sync_no_active_accounts(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test syncing when no active accounts exist."""
        response = client.post("/api/v1/accounts/sync", headers=auth_headers)
        assert response.status_code == 404
        
        data = response.json()
        assert "No active accounts" in data["detail"]


class TestAccountValidation:
    """Test account data validation."""
    
    def test_invalid_account_id_format(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test invalid UUID format for account ID."""
        response = client.get("/api/v1/accounts/invalid-uuid", headers=auth_headers)
        assert response.status_code == 422
    
    def test_pagination_limits(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test pagination parameter validation."""
        # Test invalid page number
        response = client.get("/api/v1/accounts/?page=0", headers=auth_headers)
        assert response.status_code == 422
        
        # Test per_page limit
        response = client.get("/api/v1/accounts/?per_page=200", headers=auth_headers)
        assert response.status_code == 422
    
    def test_account_update_validation(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_account: Account
    ):
        """Test account update data validation."""
        # Test empty update
        response = client.put(
            f"/api/v1/accounts/{sample_account.id}",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 200  # Empty updates should be allowed
        
        # Test partial update
        response = client.put(
            f"/api/v1/accounts/{sample_account.id}",
            json={"name": "Partial Update"},
            headers=auth_headers
        )
        assert response.status_code == 200


class TestAccountSecurity:
    """Test account endpoint security."""
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        endpoints = [
            "/api/v1/accounts/",
            f"/api/v1/accounts/{uuid4()}",
            "/api/v1/accounts/sync",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_account_isolation(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session
    ):
        """Test that users can only access their own accounts."""
        # Create another user
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed",
            is_verified=True
        )
        db_session.add(other_user)
        db_session.commit()
        
        # List accounts should only return current user's accounts
        response = client.get("/api/v1/accounts/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        for account in data["accounts"]:
            # Should only see accounts belonging to current user
            assert account["user_id"] != str(other_user.id)
