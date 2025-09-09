"""Tests for transaction management endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta

from src.database.models import User, Account, Transaction, PlaidItem, Institution


class TestTransactionEndpoints:
    """Test suite for transaction management endpoints."""
    
    def test_list_transactions_empty(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test listing transactions when none exist."""
        response = client.get("/api/v1/transactions/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 0
        assert data["transactions"] == []
        assert data["page"] == 1
        assert data["per_page"] == 20
    
    def test_list_transactions_with_data(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session
    ):
        """Test listing transactions with sample data."""
        # Create sample transaction
        transaction = Transaction(
            user_id=test_user.id,
            account_id=sample_account.id,
            plaid_transaction_id="txn_test_123",
            amount_cents=-1250,  # -$12.50
            iso_currency_code="USD",
            date=date.today(),
            name="Test Purchase",
            merchant_name="Test Store",
            primary_category="Food and Drink",
            detailed_category="Restaurants",
            payment_channel="in store",
            pending=False
        )
        db_session.add(transaction)
        db_session.commit()
        
        response = client.get("/api/v1/transactions/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 1
        assert len(data["transactions"]) == 1
        
        txn = data["transactions"][0]
        assert txn["id"] == str(transaction.id)
        assert txn["name"] == "Test Purchase"
        assert txn["amount"] == -12.5
        assert txn["merchant_name"] == "Test Store"
    
    def test_list_transactions_pagination(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session
    ):
        """Test transaction pagination."""
        # Create multiple transactions
        base_date = date.today()
        for i in range(25):
            transaction = Transaction(
                user_id=test_user.id,
                account_id=sample_account.id,
                plaid_transaction_id=f"txn_test_{i}",
                amount_cents=-(100 + i),
                iso_currency_code="USD",
                date=base_date - timedelta(days=i),
                name=f"Test Transaction {i}",
                primary_category="Shopping",
                payment_channel="online",
                pending=False
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
        assert len(data["transactions"]) == 10
        assert data["page"] == 2
    
    def test_list_transactions_filtering(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session
    ):
        """Test transaction filtering."""
        base_date = date.today()
        
        # Create transactions with different categories and dates
        transactions_data = [
            {"category": "Food and Drink", "amount": -1500, "days_ago": 5, "pending": False},
            {"category": "Shopping", "amount": -3000, "days_ago": 10, "pending": False},
            {"category": "Food and Drink", "amount": -800, "days_ago": 15, "pending": True},
            {"category": "Transfer", "amount": 50000, "days_ago": 2, "pending": False},
        ]
        
        for i, txn_data in enumerate(transactions_data):
            transaction = Transaction(
                user_id=test_user.id,
                account_id=sample_account.id,
                plaid_transaction_id=f"txn_filter_{i}",
                amount_cents=txn_data["amount"],
                iso_currency_code="USD",
                date=base_date - timedelta(days=txn_data["days_ago"]),
                name=f"Test Transaction {i}",
                primary_category=txn_data["category"],
                payment_channel="online",
                pending=txn_data["pending"]
            )
            db_session.add(transaction)
        
        db_session.commit()
        
        # Test category filtering
        response = client.get(
            "/api/v1/transactions/?category=Food and Drink",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Two food transactions
        
        # Test date range filtering
        start_date = (base_date - timedelta(days=7)).isoformat()
        end_date = base_date.isoformat()
        
        response = client.get(
            f"/api/v1/transactions/?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Transactions within 7 days
        
        # Test pending filter
        response = client.get(
            "/api/v1/transactions/?include_pending=false",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3  # Non-pending transactions
    
    def test_get_transaction(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session
    ):
        """Test getting a specific transaction."""
        transaction = Transaction(
            user_id=test_user.id,
            account_id=sample_account.id,
            plaid_transaction_id="txn_get_test",
            amount_cents=-2500,
            iso_currency_code="USD",
            date=date.today(),
            name="Get Test Transaction",
            merchant_name="Test Merchant",
            primary_category="Shopping",
            payment_channel="online",
            pending=False
        )
        db_session.add(transaction)
        db_session.commit()
        
        response = client.get(f"/api/v1/transactions/{transaction.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == str(transaction.id)
        assert data["name"] == "Get Test Transaction"
        assert data["amount"] == -25.0
        assert data["merchant_name"] == "Test Merchant"
    
    def test_get_transaction_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test getting non-existent transaction."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/transactions/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_update_transaction_category(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session
    ):
        """Test updating transaction category."""
        transaction = Transaction(
            user_id=test_user.id,
            account_id=sample_account.id,
            plaid_transaction_id="txn_update_test",
            amount_cents=-1500,
            iso_currency_code="USD",
            date=date.today(),
            name="Update Test Transaction",
            primary_category="Shopping",
            payment_channel="online",
            pending=False
        )
        db_session.add(transaction)
        db_session.commit()
        
        update_data = {
            "user_category": "Business Expense",
            "notes": "Updated for business purposes"
        }
        
        response = client.put(
            f"/api/v1/transactions/{transaction.id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_category"] == "Business Expense"
        assert data["notes"] == "Updated for business purposes"
        
        # Verify changes in database
        db_session.refresh(transaction)
        assert transaction.user_category == "Business Expense"
        assert transaction.notes == "Updated for business purposes"
    
    def test_bulk_categorize_transactions(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session
    ):
        """Test bulk categorization of transactions."""
        # Create multiple transactions
        transactions = []
        for i in range(3):
            transaction = Transaction(
                user_id=test_user.id,
                account_id=sample_account.id,
                plaid_transaction_id=f"txn_bulk_{i}",
                amount_cents=-(1000 + i * 100),
                iso_currency_code="USD",
                date=date.today(),
                name=f"Bulk Test {i}",
                primary_category="Uncategorized",
                payment_channel="online",
                pending=False
            )
            db_session.add(transaction)
            transactions.append(transaction)
        
        db_session.commit()
        
        # Bulk update categories
        bulk_data = {
            "transaction_ids": [str(txn.id) for txn in transactions],
            "category": "Business Expense",
            "notes": "Bulk categorized"
        }
        
        response = client.put(
            "/api/v1/transactions/bulk/categorize",
            json=bulk_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["updated_count"] == 3
        
        # Verify all transactions were updated
        for transaction in transactions:
            db_session.refresh(transaction)
            assert transaction.user_category == "Business Expense"
            assert transaction.notes == "Bulk categorized"
    
    def test_export_transactions(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session
    ):
        """Test exporting transactions to CSV."""
        # Create sample transactions
        for i in range(5):
            transaction = Transaction(
                user_id=test_user.id,
                account_id=sample_account.id,
                plaid_transaction_id=f"txn_export_{i}",
                amount_cents=-(1000 + i * 100),
                iso_currency_code="USD",
                date=date.today() - timedelta(days=i),
                name=f"Export Test {i}",
                merchant_name=f"Merchant {i}",
                primary_category="Shopping",
                payment_channel="online",
                pending=False
            )
            db_session.add(transaction)
        
        db_session.commit()
        
        response = client.get(
            "/api/v1/transactions/export?format=csv",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment; filename=" in response.headers["content-disposition"]
        
        # Check CSV content
        csv_content = response.content.decode("utf-8")
        assert "Date" in csv_content
        assert "Amount" in csv_content
        assert "Merchant" in csv_content
        assert "Export Test" in csv_content
    
    def test_transaction_search(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session
    ):
        """Test transaction search functionality."""
        # Create transactions with different names and merchants
        search_data = [
            {"name": "Starbucks Coffee", "merchant": "Starbucks"},
            {"name": "Amazon Purchase", "merchant": "Amazon.com"},
            {"name": "Grocery Store", "merchant": "Whole Foods"},
            {"name": "Gas Station", "merchant": "Shell"},
        ]
        
        for i, data in enumerate(search_data):
            transaction = Transaction(
                user_id=test_user.id,
                account_id=sample_account.id,
                plaid_transaction_id=f"txn_search_{i}",
                amount_cents=-1500,
                iso_currency_code="USD",
                date=date.today(),
                name=data["name"],
                merchant_name=data["merchant"],
                primary_category="Shopping",
                payment_channel="online",
                pending=False
            )
            db_session.add(transaction)
        
        db_session.commit()
        
        # Search by name
        response = client.get(
            "/api/v1/transactions/search?q=Amazon",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["transactions"]) == 1
        assert "Amazon" in data["transactions"][0]["name"]
        
        # Search by merchant
        response = client.get(
            "/api/v1/transactions/search?q=Starbucks",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["transactions"]) == 1
        assert "Starbucks" in data["transactions"][0]["merchant_name"]


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
    
    def test_invalid_date_format(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test invalid date format in filters."""
        response = client.get(
            "/api/v1/transactions/?start_date=invalid-date",
            headers=auth_headers
        )
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
        response = client.get("/api/v1/transactions/?per_page=1000", headers=auth_headers)
        assert response.status_code == 422


class TestTransactionSecurity:
    """Test transaction endpoint security."""
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication."""
        endpoints = [
            "/api/v1/transactions/",
            f"/api/v1/transactions/{uuid4()}",
            "/api/v1/transactions/search",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
    
    def test_transaction_isolation(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        sample_account: Account,
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
        
        other_transaction = Transaction(
            user_id=other_user.id,
            account_id=sample_account.id,
            plaid_transaction_id="other_txn",
            amount_cents=-1000,
            iso_currency_code="USD",
            date=date.today(),
            name="Other User Transaction",
            primary_category="Shopping",
            payment_channel="online",
            pending=False
        )
        db_session.add(other_transaction)
        db_session.commit()
        
        # Try to access other user's transaction
        response = client.get(f"/api/v1/transactions/{other_transaction.id}", headers=auth_headers)
        assert response.status_code == 404
        
        # List transactions should only return current user's transactions
        response = client.get("/api/v1/transactions/", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        for transaction in data["transactions"]:
            # Should only see transactions belonging to current user's accounts
            assert transaction["account_id"] != str(other_transaction.account_id)


class TestTransactionML:
    """Test ML integration for transactions."""
    
    def test_auto_categorization(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session,
        mock_ml_service
    ):
        """Test automatic transaction categorization."""
        # Create uncategorized transaction
        transaction = Transaction(
            user_id=test_user.id,
            account_id=sample_account.id,
            plaid_transaction_id="txn_ml_test",
            amount_cents=-1250,
            iso_currency_code="USD",
            date=date.today(),
            name="Starbucks Store",
            merchant_name="Starbucks",
            payment_channel="in store",
            pending=False
        )
        db_session.add(transaction)
        db_session.commit()
        
        # Mock ML categorization
        mock_ml_service.categorize_transaction.return_value = {
            "category": "Food and Drink",
            "subcategory": "Coffee Shops",
            "confidence": 0.95
        }
        
        response = client.post(
            f"/api/v1/transactions/{transaction.id}/categorize",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["primary_category"] == "Food and Drink"
        assert data["detailed_category"] == "Coffee Shops"
        assert data["confidence_level"] == 0.95
