"""
Comprehensive tests for transaction endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, date, timedelta
from unittest.mock import patch, Mock

from src.database.models import User, Account, Transaction, Category


class TestTransactionEndpoints:
    """Comprehensive test suite for transaction endpoints."""

    def test_list_transactions_empty(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test listing transactions when user has none."""
        response = client.get("/api/v1/transactions/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 0
        assert data["transactions"] == []
        assert data["page"] == 1
        assert data["per_page"] == 50

    def test_list_transactions_with_data(
        self, 
        client: TestClient, 
        test_user: User, 
        auth_headers: dict,
        test_account: Account,
        test_category: Category,
        db_session: Session
    ):
        """Test listing transactions with sample data."""
        # Create test transactions
        transactions = []
        for i in range(5):
            transaction = Transaction(
                account_id=test_account.id,
                plaid_transaction_id=f"test_txn_{i}",
                amount_cents=-(1000 + i * 100),  # -$10.00, -$11.00, etc.
                date=date.today() - timedelta(days=i),
                name=f"Test Transaction {i}",
                merchant_name=f"Test Merchant {i}",
                category_id=test_category.id if i % 2 == 0 else None,
                pending=False,
            )
            db_session.add(transaction)
            transactions.append(transaction)
        
        db_session.commit()
        
        response = client.get("/api/v1/transactions/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 5
        assert len(data["transactions"]) == 5
        
        # Verify transaction data structure
        transaction = data["transactions"][0]
        assert "id" in transaction
        assert "amount" in transaction
        assert "date" in transaction
        assert "name" in transaction

    def test_list_transactions_pagination(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_account: Account,
        db_session: Session
    ):
        """Test transaction pagination."""
        # Create 25 test transactions
        for i in range(25):
            transaction = Transaction(
                account_id=test_account.id,
                plaid_transaction_id=f"page_txn_{i}",
                amount_cents=-(100 + i),
                date=date.today() - timedelta(days=i),
                name=f"Page Test Transaction {i}",
                pending=False,
            )
            db_session.add(transaction)
        
        db_session.commit()
        
        # Test first page
        response = client.get("/api/v1/transactions/?per_page=10", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 25
        assert len(data["transactions"]) == 10
        assert data["page"] == 1
        assert data["per_page"] == 10
        
        # Test second page
        response = client.get("/api/v1/transactions/?page=2&per_page=10", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 25
        assert len(data["transactions"]) == 10
        assert data["page"] == 2

    def test_list_transactions_filtering(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_account: Account,
        test_category: Category,
        db_session: Session
    ):
        """Test transaction filtering by various criteria."""
        # Create transactions with different categories and amounts
        transactions = [
            Transaction(
                account_id=test_account.id,
                plaid_transaction_id="filter_txn_1",
                amount_cents=-500,  # $5.00 debit
                date=date.today(),
                name="Coffee Purchase",
                category_id=test_category.id,
                pending=False,
            ),
            Transaction(
                account_id=test_account.id,
                plaid_transaction_id="filter_txn_2",
                amount_cents=2500,  # $25.00 credit
                date=date.today(),
                name="Refund",
                category_id=None,
                pending=False,
            ),
            Transaction(
                account_id=test_account.id,
                plaid_transaction_id="filter_txn_3",
                amount_cents=-1500,  # $15.00 debit
                date=date.today() - timedelta(days=1),
                name="Gas Station",
                category_id=None,
                pending=True,
            )
        ]
        
        for txn in transactions:
            db_session.add(txn)
        db_session.commit()
        
        # Test filtering by category
        response = client.get(
            f"/api/v1/transactions/?category_id={test_category.id}", 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["transactions"][0]["name"] == "Coffee Purchase"
        
        # Test filtering by amount range
        response = client.get(
            "/api/v1/transactions/?min_amount=-10.00&max_amount=-1.00", 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["transactions"][0]["name"] == "Coffee Purchase"
        
        # Test including pending transactions
        response = client.get(
            "/api/v1/transactions/?include_pending=true", 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3

    def test_list_transactions_date_filtering(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        test_account: Account,
        db_session: Session
    ):
        """Test transaction filtering by date range."""
        # Create transactions across different dates
        today = date.today()
        transactions = [
            Transaction(
                account_id=test_account.id,
                plaid_transaction_id="date_txn_1",
                amount_cents=-1000,
                date=today,
                name="Today Transaction",
                pending=False,
            ),
            Transaction(
                account_id=test_account.id,
                plaid_transaction_id="date_txn_2",
                amount_cents=-1000,
                date=today - timedelta(days=7),
                name="Last Week Transaction",
                pending=False,
            ),
            Transaction(
                account_id=test_account.id,
                plaid_transaction_id="date_txn_3",
                amount_cents=-1000,
                date=today - timedelta(days=30),
                name="Last Month Transaction",
                pending=False,
            )
        ]
        
        for txn in transactions:
            db_session.add(txn)
        db_session.commit()
        
        # Test filtering by start date
        start_date = today - timedelta(days=7)
        response = client.get(
            f"/api/v1/transactions/?start_date={start_date.isoformat()}", 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Today and last week
        
        # Test filtering by date range
        end_date = today - timedelta(days=1)
        response = client.get(
            f"/api/v1/transactions/?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}", 
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1  # Only last week

    def test_get_transaction(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        test_account: Account,
        test_category: Category,
        db_session: Session
    ):
        """Test getting a specific transaction."""
        transaction = Transaction(
            account_id=test_account.id,
            plaid_transaction_id="get_test_txn",
            amount_cents=-2500,
            date=date.today(),
            name="Get Test Transaction",
            merchant_name="Test Merchant",
            category_id=test_category.id,
            pending=False,
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        
        response = client.get(f"/api/v1/transactions/{transaction.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(transaction.id)
        assert data["name"] == "Get Test Transaction"
        assert data["amount"] == -25.00
        assert data["merchant_name"] == "Test Merchant"

    def test_get_transaction_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent transaction."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/transactions/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_update_transaction_category(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        test_account: Account,
        test_category: Category,
        db_session: Session
    ):
        """Test updating transaction category."""
        transaction = Transaction(
            account_id=test_account.id,
            plaid_transaction_id="update_test_txn",
            amount_cents=-1500,
            date=date.today(),
            name="Update Test Transaction",
            pending=False,
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        
        update_data = {
            "category_id": str(test_category.id),
            "notes": "Updated via API"
        }
        
        response = client.put(
            f"/api/v1/transactions/{transaction.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["category_id"] == str(test_category.id)
        assert data["notes"] == "Updated via API"
        
        # Verify changes in database
        db_session.refresh(transaction)
        assert transaction.category_id == test_category.id
        assert transaction.notes == "Updated via API"

    def test_update_transaction_validation(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        test_account: Account,
        db_session: Session
    ):
        """Test transaction update validation."""
        transaction = Transaction(
            account_id=test_account.id,
            plaid_transaction_id="validate_test_txn",
            amount_cents=-1000,
            date=date.today(),
            name="Validation Test Transaction",
            pending=False,
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        
        # Test invalid category ID
        update_data = {"category_id": "invalid-uuid"}
        
        response = client.put(
            f"/api/v1/transactions/{transaction.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_categorize_transaction_ml(
        self, 
        client: TestClient, 
        auth_headers: dict, 
        test_account: Account,
        db_session: Session
    ):
        """Test ML-based transaction categorization."""
        transaction = Transaction(
            account_id=test_account.id,
            plaid_transaction_id="ml_test_txn",
            amount_cents=-1200,
            date=date.today(),
            name="STARBUCKS STORE #1234",
            merchant_name="Starbucks",
            pending=False,
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        
        # Mock ML service response
        with patch('src.routers.transactions.ml_categorization_service') as mock_ml:
            mock_ml.categorize_transaction.return_value = {
                'category': 'Food and Drink',
                'confidence': 0.85,
                'method': 'ml_prediction'
            }
            
            response = client.post(
                f"/api/v1/transactions/{transaction.id}/categorize",
                headers=auth_headers
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["category"] == "Food and Drink"
            assert data["confidence"] == 0.85
            assert data["method"] == "ml_prediction"

    def test_bulk_categorize_transactions(
        self,
        client: TestClient,
        auth_headers: dict,
        test_account: Account,
        test_category: Category,
        db_session: Session
    ):
        """Test bulk transaction categorization."""
        # Create multiple transactions
        transactions = []
        for i in range(3):
            transaction = Transaction(
                account_id=test_account.id,
                plaid_transaction_id=f"bulk_txn_{i}",
                amount_cents=-(1000 + i * 100),
                date=date.today(),
                name=f"Bulk Transaction {i}",
                pending=False,
            )
            db_session.add(transaction)
            transactions.append(transaction)
        
        db_session.commit()
        
        # Refresh to get IDs
        for txn in transactions:
            db_session.refresh(txn)
        
        bulk_data = {
            "transaction_ids": [str(txn.id) for txn in transactions],
            "category_id": str(test_category.id)
        }
        
        response = client.post(
            "/api/v1/transactions/bulk-categorize",
            json=bulk_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["updated_count"] == 3

    def test_get_transaction_statistics(
        self,
        client: TestClient,
        auth_headers: dict,
        test_account: Account,
        test_category: Category,
        db_session: Session
    ):
        """Test getting transaction statistics."""
        # Create transactions for statistics
        transactions = [
            Transaction(
                account_id=test_account.id,
                plaid_transaction_id="stat_txn_1",
                amount_cents=-2500,  # $25.00 debit
                date=date.today(),
                name="Expense Transaction",
                category_id=test_category.id,
                pending=False,
            ),
            Transaction(
                account_id=test_account.id,
                plaid_transaction_id="stat_txn_2",
                amount_cents=5000,  # $50.00 credit
                date=date.today(),
                name="Income Transaction",
                category_id=None,
                pending=False,
            )
        ]
        
        for txn in transactions:
            db_session.add(txn)
        db_session.commit()
        
        response = client.get("/api/v1/transactions/statistics", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_transactions" in data
        assert "total_income" in data
        assert "total_expenses" in data
        assert "net_flow" in data
        assert data["total_transactions"] == 2
        assert data["total_income"] == 50.00
        assert data["total_expenses"] == 25.00
        assert data["net_flow"] == 25.00

    def test_export_transactions(
        self,
        client: TestClient,
        auth_headers: dict,
        test_account: Account,
        db_session: Session
    ):
        """Test exporting transactions to CSV."""
        # Create test transaction
        transaction = Transaction(
            account_id=test_account.id,
            plaid_transaction_id="export_test_txn",
            amount_cents=-1000,
            date=date.today(),
            name="Export Test Transaction",
            pending=False,
        )
        db_session.add(transaction)
        db_session.commit()
        
        response = client.get("/api/v1/transactions/export", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert "Export Test Transaction" in response.text

    def test_search_transactions(
        self,
        client: TestClient,
        auth_headers: dict,
        test_account: Account,
        db_session: Session
    ):
        """Test searching transactions by text."""
        # Create transactions with different names
        transactions = [
            Transaction(
                account_id=test_account.id,
                plaid_transaction_id="search_txn_1",
                amount_cents=-1000,
                date=date.today(),
                name="STARBUCKS COFFEE",
                merchant_name="Starbucks",
                pending=False,
            ),
            Transaction(
                account_id=test_account.id,
                plaid_transaction_id="search_txn_2",
                amount_cents=-1500,
                date=date.today(),
                name="SHELL GAS STATION",
                merchant_name="Shell",
                pending=False,
            )
        ]
        
        for txn in transactions:
            db_session.add(txn)
        db_session.commit()
        
        # Search for coffee-related transactions
        response = client.get("/api/v1/transactions/search?q=coffee", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 1
        assert "STARBUCKS" in data["transactions"][0]["name"]


class TestTransactionValidation:
    """Test transaction data validation."""
    
    def test_invalid_transaction_id_format(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test invalid UUID format for transaction ID."""
        response = client.get("/api/v1/transactions/invalid-uuid", headers=auth_headers)
        assert response.status_code == 422
    
    def test_pagination_limits(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test pagination parameter validation."""
        # Test invalid page number
        response = client.get("/api/v1/transactions/?page=0", headers=auth_headers)
        assert response.status_code == 422
        
        # Test per_page limit
        response = client.get("/api/v1/transactions/?per_page=500", headers=auth_headers)
        assert response.status_code == 422
    
    def test_date_range_validation(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test date range parameter validation."""
        # Test invalid date format
        response = client.get("/api/v1/transactions/?start_date=invalid-date", headers=auth_headers)
        assert response.status_code == 422
        
        # Test start date after end date
        start_date = "2024-12-31"
        end_date = "2024-01-01"
        response = client.get(
            f"/api/v1/transactions/?start_date={start_date}&end_date={end_date}", 
            headers=auth_headers
        )
        assert response.status_code == 422


class TestTransactionSecurity:
    """Test transaction endpoint security."""
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        endpoints = [
            "/api/v1/transactions/",
            f"/api/v1/transactions/{uuid4()}",
            "/api/v1/transactions/statistics",
            "/api/v1/transactions/export",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_transaction_isolation(
        self,
        client: TestClient,
        auth_headers: dict,
        test_account: Account,
        db_session: Session
    ):
        """Test that users can only access their own transactions."""
        # Create another user's transaction
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
            plaid_account_id="other_account",
            name="Other Account",
            type="depository",
            subtype="checking"
        )
        db_session.add(other_account)
        db_session.flush()
        
        other_transaction = Transaction(
            account_id=other_account.id,
            plaid_transaction_id="other_txn",
            amount_cents=-1000,
            date=date.today(),
            name="Other User Transaction",
            pending=False,
        )
        db_session.add(other_transaction)
        db_session.commit()
        
        # List transactions should only return current user's transactions
        response = client.get("/api/v1/transactions/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        for transaction in data["transactions"]:
            # Should not see other user's transactions
            assert transaction["name"] != "Other User Transaction"
            
        # Direct access to other user's transaction should fail
        response = client.get(f"/api/v1/transactions/{other_transaction.id}", headers=auth_headers)
        assert response.status_code == 404