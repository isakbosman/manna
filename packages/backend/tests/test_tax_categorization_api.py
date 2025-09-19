"""Integration tests for tax categorization API endpoints."""

import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import json

# Test fixtures and models
from models.tax_categorization import (
    TaxCategory, ChartOfAccount, BusinessExpenseTracking,
    CategoryMapping, CategorizationAudit
)
from models.transaction import Transaction
from models.user import User
from models.category import Category


class TestTaxCategorizationAPI:
    """Integration tests for tax categorization API endpoints."""

    def test_categorize_transaction_for_tax_success(self, client, auth_headers, db_session):
        """Test successful transaction tax categorization."""
        # Create test data
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        transaction = Transaction(
            account_id="acc-123",
            plaid_transaction_id="txn-123",
            amount=Decimal("100.00"),
            name="Office supplies",
            merchant_name="Staples",
            is_tax_deductible=False
        )
        db_session.add(transaction)
        db_session.flush()

        tax_category = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            tax_line="Line 18",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.flush()

        chart_account = ChartOfAccount(
            user_id=user.id,
            account_code="5100",
            account_name="Office Expense",
            account_type="expense",
            normal_balance="debit",
            is_active=True
        )
        db_session.add(chart_account)
        db_session.commit()

        # Make API request
        request_data = {
            "tax_category_id": str(tax_category.id),
            "chart_account_id": str(chart_account.id),
            "business_percentage": 100.0,
            "business_purpose": "Office supplies for business",
            "override_automated": True
        }

        response = client.post(
            f"/api/tax/categorize/{transaction.id}",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["transaction_id"] == str(transaction.id)
        assert data["tax_category"] == "Office expense"
        assert data["chart_account"] == "Office Expense"

    def test_categorize_transaction_for_tax_invalid_transaction(self, client, auth_headers):
        """Test categorization with invalid transaction ID."""
        request_data = {
            "tax_category_id": "tax-123",
            "chart_account_id": "chart-123",
            "business_percentage": 100.0
        }

        response = client.post(
            "/api/tax/categorize/invalid-transaction-id",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_categorize_transaction_for_tax_unauthorized(self, client, db_session):
        """Test categorization without authentication."""
        request_data = {
            "tax_category_id": "tax-123",
            "chart_account_id": "chart-123",
            "business_percentage": 100.0
        }

        response = client.post(
            "/api/tax/categorize/trans-123",
            json=request_data
        )

        assert response.status_code == 401

    def test_bulk_categorize_transactions_for_tax(self, client, auth_headers, db_session):
        """Test bulk transaction tax categorization."""
        # Create test data
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Create multiple transactions
        transactions = []
        for i in range(3):
            transaction = Transaction(
                account_id="acc-123",
                plaid_transaction_id=f"txn-{i}",
                amount=Decimal("50.00"),
                name=f"Transaction {i}",
                merchant_name="Test Merchant"
            )
            db_session.add(transaction)
            db_session.flush()
            transactions.append(transaction)

        tax_category = TaxCategory(
            category_code="SCHED_C_27",
            category_name="Travel",
            tax_form="Schedule C",
            tax_line="Line 27a",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.flush()

        chart_account = ChartOfAccount(
            user_id=user.id,
            account_code="5200",
            account_name="Travel Expense",
            account_type="expense",
            normal_balance="debit",
            is_active=True
        )
        db_session.add(chart_account)
        db_session.commit()

        # Make API request
        request_data = {
            "transaction_ids": [str(t.id) for t in transactions],
            "tax_category_id": str(tax_category.id),
            "chart_account_id": str(chart_account.id),
            "business_percentage": 100.0
        }

        response = client.post(
            "/api/tax/categorize/bulk",
            json=request_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        assert data["error_count"] == 0
        assert len(data["results"]) == 3

    def test_get_tax_summary(self, client, auth_headers, db_session):
        """Test tax summary endpoint."""
        # Create test data
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        tax_category = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            tax_line="Line 18",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.flush()

        # Create transactions with tax categorization
        transaction = Transaction(
            account_id="acc-123",
            plaid_transaction_id="txn-123",
            amount=Decimal("100.00"),
            name="Office supplies",
            tax_category_id=tax_category.id,
            deductible_amount=Decimal("100.00"),
            is_tax_deductible=True,
            tax_year=2024
        )
        db_session.add(transaction)
        db_session.commit()

        response = client.get(
            "/api/tax/summary/2024",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tax_year"] == 2024
        assert data["total_deductions"] == 100.0
        assert "SCHED_C_18" in data["categories"]

    def test_export_schedule_c(self, client, auth_headers, db_session):
        """Test Schedule C export endpoint."""
        # Create test data similar to tax summary
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        tax_category = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            tax_line="Line 18",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.flush()

        transaction = Transaction(
            account_id="acc-123",
            plaid_transaction_id="txn-123",
            amount=Decimal("200.00"),
            name="Office supplies",
            tax_category_id=tax_category.id,
            deductible_amount=Decimal("200.00"),
            is_tax_deductible=True,
            tax_year=2024
        )
        db_session.add(transaction)
        db_session.commit()

        response = client.get(
            "/api/tax/export/schedule-c/2024",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tax_year"] == 2024
        assert "18" in data["schedule_c_lines"]
        assert data["total_expenses"] == 200.0

    def test_get_tax_categories(self, client, db_session):
        """Test getting available tax categories."""
        # Create test tax categories
        categories = [
            TaxCategory(
                category_code="SCHED_C_18",
                category_name="Office expense",
                tax_form="Schedule C",
                tax_line="Line 18",
                is_active=True,
                effective_date=date(2024, 1, 1)
            ),
            TaxCategory(
                category_code="SCHED_C_27",
                category_name="Travel",
                tax_form="Schedule C",
                tax_line="Line 27a",
                is_active=True,
                effective_date=date(2024, 1, 1)
            ),
            TaxCategory(
                category_code="SCHED_E_20",
                category_name="Rental expenses",
                tax_form="Schedule E",
                tax_line="Line 20",
                is_active=False,  # Inactive
                effective_date=date(2024, 1, 1)
            )
        ]

        for category in categories:
            db_session.add(category)
        db_session.commit()

        # Test getting all active categories
        response = client.get("/api/tax/categories")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Only active ones

        # Test filtering by tax form
        response = client.get("/api/tax/categories?tax_form=Schedule C")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(cat["tax_form"] == "Schedule C" for cat in data)

        # Test including inactive categories
        response = client.get("/api/tax/categories?is_active=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category_code"] == "SCHED_E_20"

    def test_create_tax_category(self, client, auth_headers, db_session):
        """Test creating a new tax category."""
        category_data = {
            "category_code": "SCHED_C_NEW",
            "category_name": "New Business Expense",
            "tax_form": "Schedule C",
            "tax_line": "Line 99",
            "description": "New type of business expense",
            "deduction_type": "ordinary",
            "is_business_expense": True,
            "is_active": True,
            "effective_date": "2024-01-01",
            "keywords": ["new", "expense"],
            "exclusions": ["personal"]
        }

        response = client.post(
            "/api/tax/categories",
            json=category_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category_code"] == "SCHED_C_NEW"
        assert data["category_name"] == "New Business Expense"

    def test_get_chart_of_accounts(self, client, auth_headers, db_session):
        """Test getting user's chart of accounts."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        accounts = [
            ChartOfAccount(
                user_id=user.id,
                account_code="1100",
                account_name="Cash",
                account_type="asset",
                normal_balance="debit",
                is_active=True
            ),
            ChartOfAccount(
                user_id=user.id,
                account_code="5100",
                account_name="Office Expense",
                account_type="expense",
                normal_balance="debit",
                is_active=True
            ),
            ChartOfAccount(
                user_id=user.id,
                account_code="5200",
                account_name="Archived Expense",
                account_type="expense",
                normal_balance="debit",
                is_active=False  # Inactive
            )
        ]

        for account in accounts:
            db_session.add(account)
        db_session.commit()

        # Test getting all active accounts
        response = client.get(
            "/api/tax/chart-of-accounts",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Only active ones

        # Test filtering by account type
        response = client.get(
            "/api/tax/chart-of-accounts?account_type=expense",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["account_type"] == "expense"
        assert data[0]["account_code"] == "5100"

        # Test including inactive accounts
        response = client.get(
            "/api/tax/chart-of-accounts?is_active=false",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["account_code"] == "5200"

    def test_create_chart_account(self, client, auth_headers, db_session):
        """Test creating a new chart of accounts entry."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        account_data = {
            "account_code": "5300",
            "account_name": "Marketing Expense",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Marketing and advertising expenses",
            "tax_category": "Advertising",
            "tax_line_mapping": "Line 8"
        }

        response = client.post(
            "/api/tax/chart-of-accounts",
            json=account_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["account_code"] == "5300"
        assert data["account_name"] == "Marketing Expense"
        assert data["account_type"] == "expense"
        assert data["normal_balance"] == "debit"

    def test_create_chart_account_duplicate_code(self, client, auth_headers, db_session):
        """Test creating chart account with duplicate code."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Create existing account
        existing_account = ChartOfAccount(
            user_id=user.id,
            account_code="5100",
            account_name="Office Expense",
            account_type="expense",
            normal_balance="debit",
            is_active=True
        )
        db_session.add(existing_account)
        db_session.commit()

        # Try to create account with same code
        account_data = {
            "account_code": "5100",  # Duplicate
            "account_name": "Another Office Expense",
            "account_type": "expense",
            "normal_balance": "debit"
        }

        response = client.post(
            "/api/tax/chart-of-accounts",
            json=account_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_chart_account(self, client, auth_headers, db_session):
        """Test updating a chart of accounts entry."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        account = ChartOfAccount(
            user_id=user.id,
            account_code="5100",
            account_name="Office Expense",
            account_type="expense",
            normal_balance="debit",
            is_active=True,
            description="Old description"
        )
        db_session.add(account)
        db_session.commit()

        update_data = {
            "account_name": "Updated Office Expense",
            "description": "Updated description",
            "tax_category": "Office supplies"
        }

        response = client.put(
            f"/api/tax/chart-of-accounts/{account.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["account_name"] == "Updated Office Expense"
        assert data["description"] == "Updated description"
        assert data["tax_category"] == "Office supplies"

    def test_update_chart_account_not_found(self, client, auth_headers):
        """Test updating non-existent chart account."""
        update_data = {
            "account_name": "Updated Name"
        }

        response = client.put(
            "/api/tax/chart-of-accounts/nonexistent-id",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_delete_chart_account(self, client, auth_headers, db_session):
        """Test deleting a chart of accounts entry."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        account = ChartOfAccount(
            user_id=user.id,
            account_code="5100",
            account_name="Office Expense",
            account_type="expense",
            normal_balance="debit",
            is_active=True,
            is_system_account=False
        )
        db_session.add(account)
        db_session.commit()

        response = client.delete(
            f"/api/tax/chart-of-accounts/{account.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Account deleted successfully"

    def test_delete_system_account(self, client, auth_headers, db_session):
        """Test that deleting system account fails."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        system_account = ChartOfAccount(
            user_id=user.id,
            account_code="1000",
            account_name="System Cash",
            account_type="asset",
            normal_balance="debit",
            is_active=True,
            is_system_account=True  # System account
        )
        db_session.add(system_account)
        db_session.commit()

        response = client.delete(
            f"/api/tax/chart-of-accounts/{system_account.id}",
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "Cannot delete system accounts" in response.json()["detail"]

    def test_get_trial_balance(self, client, auth_headers, db_session):
        """Test getting trial balance report."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Create some accounts
        accounts = [
            ChartOfAccount(
                user_id=user.id,
                account_code="1100",
                account_name="Cash",
                account_type="asset",
                normal_balance="debit",
                is_active=True,
                current_balance=Decimal("1000.00")
            ),
            ChartOfAccount(
                user_id=user.id,
                account_code="2100",
                account_name="Accounts Payable",
                account_type="liability",
                normal_balance="credit",
                is_active=True,
                current_balance=Decimal("500.00")
            )
        ]

        for account in accounts:
            db_session.add(account)
        db_session.commit()

        response = client.get(
            "/api/tax/trial-balance",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert "total_debits" in data
        assert "total_credits" in data
        assert len(data["accounts"]) == 2

        # Test with date filter
        response = client.get(
            "/api/tax/trial-balance?as_of_date=2024-12-31",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_get_financial_statements(self, client, auth_headers, db_session):
        """Test getting financial statements."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Create accounts for balance sheet and income statement
        accounts = [
            ChartOfAccount(
                user_id=user.id,
                account_code="1100",
                account_name="Cash",
                account_type="asset",
                normal_balance="debit",
                is_active=True,
                current_balance=Decimal("2000.00")
            ),
            ChartOfAccount(
                user_id=user.id,
                account_code="4000",
                account_name="Service Revenue",
                account_type="revenue",
                normal_balance="credit",
                is_active=True,
                current_balance=Decimal("1500.00")
            ),
            ChartOfAccount(
                user_id=user.id,
                account_code="5000",
                account_name="Office Expense",
                account_type="expense",
                normal_balance="debit",
                is_active=True,
                current_balance=Decimal("300.00")
            )
        ]

        for account in accounts:
            db_session.add(account)
        db_session.commit()

        response = client.get(
            "/api/tax/financial-statements",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "balance_sheet" in data
        assert "income_statement" in data
        assert "assets" in data["balance_sheet"]
        assert "liabilities" in data["balance_sheet"]
        assert "equity" in data["balance_sheet"]
        assert "revenue" in data["income_statement"]
        assert "expenses" in data["income_statement"]
        assert "net_income" in data["income_statement"]

    def test_create_business_expense_tracking(self, client, auth_headers, db_session):
        """Test creating business expense tracking record."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        transaction = Transaction(
            account_id="acc-123",
            plaid_transaction_id="txn-123",
            amount=Decimal("150.00"),
            name="Business dinner"
        )
        db_session.add(transaction)
        db_session.commit()

        tracking_data = {
            "transaction_id": str(transaction.id),
            "business_purpose": "Client meeting dinner",
            "business_percentage": 100.0,
            "receipt_required": True,
            "receipt_attached": False,
            "mileage_start_location": "Office",
            "mileage_end_location": "Restaurant",
            "miles_driven": 15.5
        }

        response = client.post(
            "/api/tax/business-expense",
            json=tracking_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == str(transaction.id)
        assert data["business_purpose"] == "Client meeting dinner"
        assert data["business_percentage"] == 100.0
        assert data["miles_driven"] == 15.5

    def test_get_business_expense_tracking(self, client, auth_headers, db_session):
        """Test getting business expense tracking for a transaction."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        transaction = Transaction(
            account_id="acc-123",
            plaid_transaction_id="txn-123",
            amount=Decimal("75.00"),
            name="Office supplies"
        )
        db_session.add(transaction)
        db_session.flush()

        tracking = BusinessExpenseTracking(
            transaction_id=transaction.id,
            user_id=user.id,
            business_purpose="Office supplies for business",
            business_percentage=Decimal("100.00"),
            receipt_required=True,
            receipt_attached=True
        )
        db_session.add(tracking)
        db_session.commit()

        response = client.get(
            f"/api/tax/business-expense/{transaction.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == str(transaction.id)
        assert data["business_purpose"] == "Office supplies for business"

    def test_get_business_expense_tracking_not_found(self, client, auth_headers):
        """Test getting business expense tracking for non-existent transaction."""
        response = client.get(
            "/api/tax/business-expense/nonexistent-transaction",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_category_mappings(self, client, auth_headers, db_session):
        """Test getting user's category mappings."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        category = Category(
            user_id=user.id,
            name="Office Supplies",
            type="expense"
        )
        db_session.add(category)
        db_session.flush()

        tax_category = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            tax_line="Line 18",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.flush()

        chart_account = ChartOfAccount(
            user_id=user.id,
            account_code="5100",
            account_name="Office Expense",
            account_type="expense",
            normal_balance="debit",
            is_active=True
        )
        db_session.add(chart_account)
        db_session.flush()

        mapping = CategoryMapping(
            user_id=user.id,
            source_category_id=category.id,
            chart_account_id=chart_account.id,
            tax_category_id=tax_category.id,
            confidence_score=Decimal("0.95"),
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(mapping)
        db_session.commit()

        response = client.get(
            "/api/tax/category-mappings",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["confidence_score"] == 0.95

    def test_create_category_mapping(self, client, auth_headers, db_session):
        """Test creating a new category mapping."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        category = Category(
            user_id=user.id,
            name="Travel",
            type="expense"
        )
        db_session.add(category)
        db_session.flush()

        tax_category = TaxCategory(
            category_code="SCHED_C_27",
            category_name="Travel",
            tax_form="Schedule C",
            tax_line="Line 27a",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.flush()

        chart_account = ChartOfAccount(
            user_id=user.id,
            account_code="5200",
            account_name="Travel Expense",
            account_type="expense",
            normal_balance="debit",
            is_active=True
        )
        db_session.add(chart_account)
        db_session.commit()

        mapping_data = {
            "source_category_id": str(category.id),
            "chart_account_id": str(chart_account.id),
            "tax_category_id": str(tax_category.id),
            "confidence_score": 0.9,
            "is_user_defined": True,
            "effective_date": "2024-01-01",
            "business_percentage_default": 100.0
        }

        response = client.post(
            "/api/tax/category-mappings",
            json=mapping_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["source_category_id"] == str(category.id)
        assert data["confidence_score"] == 0.9


class TestTaxCategorizationAPIErrorHandling:
    """Test error handling in tax categorization API endpoints."""

    def test_internal_server_error_handling(self, client, auth_headers):
        """Test that internal server errors are handled properly."""
        with patch('src.services.tax_categorization_service.TaxCategorizationService') as mock_service:
            mock_service.return_value.categorize_for_tax.side_effect = Exception("Database connection error")

            request_data = {
                "tax_category_id": "tax-123",
                "chart_account_id": "chart-123",
                "business_percentage": 100.0
            }

            response = client.post(
                "/api/tax/categorize/trans-123",
                json=request_data,
                headers=auth_headers
            )

            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_validation_errors(self, client, auth_headers):
        """Test request validation errors."""
        # Invalid business percentage
        request_data = {
            "tax_category_id": "tax-123",
            "chart_account_id": "chart-123",
            "business_percentage": 150.0  # Invalid - over 100%
        }

        response = client.post(
            "/api/tax/categorize/trans-123",
            json=request_data,
            headers=auth_headers
        )

        # Should be handled by Pydantic validation
        assert response.status_code in [400, 422]

    def test_missing_required_fields(self, client, auth_headers):
        """Test requests with missing required fields."""
        # Empty request body
        response = client.post(
            "/api/tax/categorize/trans-123",
            json={},
            headers=auth_headers
        )

        # Should be handled by Pydantic validation
        assert response.status_code in [400, 422]

    def test_invalid_uuid_format(self, client, auth_headers):
        """Test requests with invalid UUID format."""
        request_data = {
            "tax_category_id": "not-a-uuid",
            "chart_account_id": "also-not-a-uuid",
            "business_percentage": 100.0
        }

        response = client.post(
            "/api/tax/categorize/invalid-transaction-id",
            json=request_data,
            headers=auth_headers
        )

        # Should fail with validation or not found error
        assert response.status_code in [400, 422]


class TestTaxCategorizationAPIPerformance:
    """Performance tests for tax categorization API endpoints."""

    def test_bulk_categorization_performance(self, client, auth_headers, db_session, performance_timer):
        """Test performance of bulk categorization."""
        # Create test data
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Create many transactions
        transaction_ids = []
        for i in range(50):  # 50 transactions
            transaction = Transaction(
                account_id="acc-123",
                plaid_transaction_id=f"perf-txn-{i}",
                amount=Decimal("25.00"),
                name=f"Performance test transaction {i}"
            )
            db_session.add(transaction)
            db_session.flush()
            transaction_ids.append(str(transaction.id))

        tax_category = TaxCategory(
            category_code="PERF_TEST",
            category_name="Performance Test Category",
            tax_form="Schedule C",
            tax_line="Line 99",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.flush()

        chart_account = ChartOfAccount(
            user_id=user.id,
            account_code="9999",
            account_name="Performance Test Account",
            account_type="expense",
            normal_balance="debit",
            is_active=True
        )
        db_session.add(chart_account)
        db_session.commit()

        request_data = {
            "transaction_ids": transaction_ids,
            "tax_category_id": str(tax_category.id),
            "chart_account_id": str(chart_account.id),
            "business_percentage": 100.0
        }

        performance_timer.start()
        response = client.post(
            "/api/tax/categorize/bulk",
            json=request_data,
            headers=auth_headers
        )
        performance_timer.stop()

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 50
        assert data["error_count"] == 0

        # Performance assertion - should complete within reasonable time
        assert performance_timer.elapsed_ms < 10000  # Less than 10 seconds

    def test_tax_summary_with_large_dataset(self, client, auth_headers, db_session, large_dataset):
        """Test tax summary performance with large dataset."""
        # Use the large_dataset fixture from conftest.py
        # This creates 1000 transactions

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        tax_category = TaxCategory(
            category_code="LARGE_TEST",
            category_name="Large Dataset Test",
            tax_form="Schedule C",
            tax_line="Line 18",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.commit()

        # Update some transactions to have tax categorization
        transactions = db_session.query(Transaction).limit(100).all()
        for transaction in transactions:
            transaction.tax_category_id = tax_category.id
            transaction.deductible_amount = Decimal("50.00")
            transaction.is_tax_deductible = True
            transaction.tax_year = 2024

        db_session.commit()

        response = client.get(
            "/api/tax/summary/2024",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tax_year"] == 2024
        assert data["transaction_count"] == 100
        assert data["total_deductions"] == 5000.0  # 100 * 50.00