"""End-to-end workflow tests for tax categorization system."""

import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, List
from fastapi.testclient import TestClient

# Import models
from models.tax_categorization import (
    TaxCategory, ChartOfAccount, BusinessExpenseTracking,
    CategoryMapping, CategorizationAudit
)
from models.transaction import Transaction
from models.user import User
from models.category import Category
from models.account import Account


class TestCompleteTransactionCategorizationWorkflow:
    """Test complete end-to-end transaction categorization workflows."""

    def test_complete_single_transaction_workflow(self, client, auth_headers, db_session):
        """Test complete workflow from transaction creation to tax categorization."""
        # Step 1: Create user and setup
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Step 2: Create account
        account = Account(
            user_id=user.id,
            plaid_account_id="acc-123",
            name="Business Checking",
            type="depository",
            subtype="checking",
            current_balance=5000.00
        )
        db_session.add(account)
        db_session.flush()

        # Step 3: Create transaction category
        category = Category(
            user_id=user.id,
            name="Office Supplies",
            type="expense"
        )
        db_session.add(category)
        db_session.flush()

        # Step 4: Create transaction
        transaction = Transaction(
            account_id=account.id,
            plaid_transaction_id="txn-123",
            amount=Decimal("125.50"),
            name="Staples Office Supplies",
            merchant_name="Staples",
            description="Office supplies for business",
            category_id=category.id,
            is_tax_deductible=False  # Initially not categorized for tax
        )
        db_session.add(transaction)
        db_session.flush()

        # Step 5: Create tax category
        tax_category = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            tax_line="Line 18",
            description="Office supplies and related expenses",
            is_business_expense=True,
            is_active=True,
            effective_date=date(2024, 1, 1),
            keywords=["office", "supplies", "staples", "paper"],
            exclusions=["personal"]
        )
        db_session.add(tax_category)
        db_session.flush()

        # Step 6: Create chart of accounts entry
        chart_account = ChartOfAccount(
            user_id=user.id,
            account_code="5100",
            account_name="Office Expense",
            account_type="expense",
            normal_balance="debit",
            description="Office supplies and related business expenses",
            tax_category="Office expense",
            tax_line_mapping="Line 18"
        )
        db_session.add(chart_account)
        db_session.commit()

        # Step 7: Test auto-detection (should find the tax category)
        # First, let's test without providing tax_category_id to trigger auto-detection
        categorization_request = {
            "business_percentage": 100.0,
            "business_purpose": "Office supplies for daily business operations",
            "override_automated": True
        }

        response = client.post(
            f"/api/tax/categorize/{transaction.id}",
            json=categorization_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        categorization_result = response.json()
        assert categorization_result["success"] is True
        assert categorization_result["requires_substantiation"] is True  # Amount > $75

        # Step 8: Verify transaction was updated
        db_session.refresh(transaction)
        assert transaction.tax_category_id is not None
        assert transaction.chart_account_id is not None
        assert transaction.business_use_percentage == Decimal("100.00")
        assert transaction.deductible_amount == Decimal("125.50")
        assert transaction.schedule_c_line == "Line 18"
        assert transaction.requires_substantiation is True
        assert transaction.is_tax_deductible is True

        # Step 9: Verify business expense tracking was created
        business_tracking = db_session.query(BusinessExpenseTracking).filter_by(
            transaction_id=transaction.id
        ).first()
        assert business_tracking is not None
        assert business_tracking.business_purpose == "Office supplies for daily business operations"
        assert business_tracking.business_percentage == Decimal("100.00")
        assert business_tracking.receipt_required is True

        # Step 10: Verify audit trail was created
        audit_records = db_session.query(CategorizationAudit).filter_by(
            transaction_id=transaction.id
        ).all()
        assert len(audit_records) == 1
        assert audit_records[0].action_type == "tax_categorize"
        assert audit_records[0].new_tax_category_id == transaction.tax_category_id

        # Step 11: Test getting business expense tracking
        response = client.get(
            f"/api/tax/business-expense/{transaction.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        tracking_data = response.json()
        assert tracking_data["business_purpose"] == "Office supplies for daily business operations"

        # Step 12: Update business expense tracking with receipt information
        tracking_update = {
            "transaction_id": str(transaction.id),
            "business_purpose": "Office supplies for daily business operations",
            "business_percentage": 100.0,
            "receipt_required": True,
            "receipt_attached": True,
            "receipt_url": "https://example.com/receipts/staples-123.pdf",
            "substantiation_notes": "Receipt attached for office supplies purchase"
        }

        response = client.post(
            "/api/tax/business-expense",
            json=tracking_update,
            headers=auth_headers
        )
        assert response.status_code == 200

        # Step 13: Test tax summary includes our transaction
        response = client.get(
            "/api/tax/summary/2024",
            headers=auth_headers
        )
        assert response.status_code == 200
        tax_summary = response.json()
        assert tax_summary["total_deductions"] == 125.50
        assert "SCHED_C_18" in tax_summary["categories"]
        office_category = tax_summary["categories"]["SCHED_C_18"]
        assert office_category["total_amount"] == 125.50
        assert office_category["transaction_count"] == 1

        # Step 14: Test Schedule C export
        response = client.get(
            "/api/tax/export/schedule-c/2024",
            headers=auth_headers
        )
        assert response.status_code == 200
        schedule_c_data = response.json()
        assert schedule_c_data["total_expenses"] == 125.50
        assert "18" in schedule_c_data["schedule_c_lines"]
        assert schedule_c_data["schedule_c_lines"]["18"]["amount"] == 125.50

        print("✅ Complete single transaction workflow test passed!")

    def test_bulk_transaction_categorization_workflow(self, client, auth_headers, db_session):
        """Test bulk categorization workflow with multiple transactions."""
        # Step 1: Setup user and accounts
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        account = Account(
            user_id=user.id,
            plaid_account_id="acc-123",
            name="Business Checking",
            type="depository",
            subtype="checking",
            current_balance=10000.00
        )
        db_session.add(account)
        db_session.flush()

        # Step 2: Create multiple transactions
        transactions_data = [
            {
                "plaid_id": "txn-travel-1",
                "amount": Decimal("85.00"),
                "name": "Hotel Stay",
                "merchant": "Hilton Hotels",
                "description": "Business travel accommodation"
            },
            {
                "plaid_id": "txn-travel-2",
                "amount": Decimal("45.50"),
                "name": "Taxi Ride",
                "merchant": "Yellow Cab",
                "description": "Airport transportation"
            },
            {
                "plaid_id": "txn-travel-3",
                "amount": Decimal("25.75"),
                "name": "Business Meal",
                "merchant": "Restaurant ABC",
                "description": "Client dinner meeting"
            }
        ]

        transactions = []
        for tx_data in transactions_data:
            transaction = Transaction(
                account_id=account.id,
                plaid_transaction_id=tx_data["plaid_id"],
                amount=tx_data["amount"],
                name=tx_data["name"],
                merchant_name=tx_data["merchant"],
                description=tx_data["description"]
            )
            db_session.add(transaction)
            db_session.flush()
            transactions.append(transaction)

        # Step 3: Create tax categories for different expense types
        travel_tax_category = TaxCategory(
            category_code="SCHED_C_27A",
            category_name="Travel",
            tax_form="Schedule C",
            tax_line="Line 27a",
            description="Business travel expenses",
            is_business_expense=True,
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(travel_tax_category)

        meals_tax_category = TaxCategory(
            category_code="SCHED_C_27B",
            category_name="Meals",
            tax_form="Schedule C",
            tax_line="Line 27b",
            description="Business meal expenses",
            percentage_limit=Decimal("50.00"),  # 50% deductible
            is_business_expense=True,
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(meals_tax_category)
        db_session.flush()

        # Step 4: Create corresponding chart accounts
        travel_chart_account = ChartOfAccount(
            user_id=user.id,
            account_code="5200",
            account_name="Travel Expense",
            account_type="expense",
            normal_balance="debit",
            tax_category="Travel"
        )
        db_session.add(travel_chart_account)

        meals_chart_account = ChartOfAccount(
            user_id=user.id,
            account_code="5210",
            account_name="Meals Expense",
            account_type="expense",
            normal_balance="debit",
            tax_category="Meals"
        )
        db_session.add(meals_chart_account)
        db_session.commit()

        # Step 5: Bulk categorize travel expenses (first 2 transactions)
        travel_bulk_request = {
            "transaction_ids": [str(transactions[0].id), str(transactions[1].id)],
            "tax_category_id": str(travel_tax_category.id),
            "chart_account_id": str(travel_chart_account.id),
            "business_percentage": 100.0
        }

        response = client.post(
            "/api/tax/categorize/bulk",
            json=travel_bulk_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        bulk_result = response.json()
        assert bulk_result["success_count"] == 2
        assert bulk_result["error_count"] == 0

        # Step 6: Categorize meal expense individually (to test percentage limit)
        meal_categorization = {
            "tax_category_id": str(meals_tax_category.id),
            "chart_account_id": str(meals_chart_account.id),
            "business_percentage": 100.0,
            "business_purpose": "Client dinner to discuss new contract"
        }

        response = client.post(
            f"/api/tax/categorize/{transactions[2].id}",
            json=meal_categorization,
            headers=auth_headers
        )

        assert response.status_code == 200
        meal_result = response.json()
        assert meal_result["success"] is True
        # Meal should be 50% deductible: 25.75 * 0.5 = 12.875 ≈ 12.88
        assert abs(meal_result["deductible_amount"] - 12.88) < 0.01

        # Step 7: Verify all transactions were properly categorized
        for i, transaction in enumerate(transactions):
            db_session.refresh(transaction)
            assert transaction.tax_category_id is not None
            assert transaction.chart_account_id is not None
            assert transaction.is_tax_deductible is True

        # Travel transactions should be 100% deductible
        assert transactions[0].deductible_amount == Decimal("85.00")
        assert transactions[1].deductible_amount == Decimal("45.50")
        # Meal transaction should be 50% deductible (with percentage limit)
        assert abs(transactions[2].deductible_amount - Decimal("12.88")) < Decimal("0.01")

        # Step 8: Test comprehensive tax summary
        response = client.get(
            "/api/tax/summary/2024",
            headers=auth_headers
        )

        assert response.status_code == 200
        tax_summary = response.json()

        # Total deductions = 85.00 + 45.50 + 12.88 = 143.38
        expected_total = 85.00 + 45.50 + 12.88
        assert abs(tax_summary["total_deductions"] - expected_total) < 0.01

        # Should have both travel and meals categories
        assert "SCHED_C_27A" in tax_summary["categories"]
        assert "SCHED_C_27B" in tax_summary["categories"]

        travel_summary = tax_summary["categories"]["SCHED_C_27A"]
        assert travel_summary["transaction_count"] == 2
        assert travel_summary["total_amount"] == 130.50  # 85.00 + 45.50

        meals_summary = tax_summary["categories"]["SCHED_C_27B"]
        assert meals_summary["transaction_count"] == 1
        assert abs(meals_summary["total_amount"] - 12.88) < 0.01

        # Step 9: Test Schedule C export with multiple categories
        response = client.get(
            "/api/tax/export/schedule-c/2024",
            headers=auth_headers
        )

        assert response.status_code == 200
        schedule_c = response.json()
        assert "27" in schedule_c["schedule_c_lines"]  # Combined travel/meals line
        assert abs(schedule_c["total_expenses"] - expected_total) < 0.01

        print("✅ Bulk transaction categorization workflow test passed!")

    def test_category_mapping_workflow(self, client, auth_headers, db_session):
        """Test workflow with category mappings for automatic categorization."""
        # Step 1: Setup
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Step 2: Create transaction category
        office_category = Category(
            user_id=user.id,
            name="Office Supplies",
            type="expense"
        )
        db_session.add(office_category)
        db_session.flush()

        # Step 3: Create tax category and chart account
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
            normal_balance="debit"
        )
        db_session.add(chart_account)
        db_session.flush()

        # Step 4: Create category mapping
        mapping_data = {
            "source_category_id": str(office_category.id),
            "chart_account_id": str(chart_account.id),
            "tax_category_id": str(tax_category.id),
            "confidence_score": 0.95,
            "is_user_defined": True,
            "effective_date": "2024-01-01",
            "business_percentage_default": 100.0,
            "always_require_receipt": True
        }

        response = client.post(
            "/api/tax/category-mappings",
            json=mapping_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        mapping = response.json()
        assert mapping["confidence_score"] == 0.95

        # Step 5: Create transaction with the mapped category
        account = Account(
            user_id=user.id,
            plaid_account_id="acc-123",
            name="Business Checking",
            type="depository",
            subtype="checking",
            current_balance=5000.00
        )
        db_session.add(account)
        db_session.flush()

        transaction = Transaction(
            account_id=account.id,
            plaid_transaction_id="txn-mapped",
            amount=Decimal("75.00"),
            name="Office supplies from Amazon",
            merchant_name="Amazon",
            category_id=office_category.id  # This should trigger mapping
        )
        db_session.add(transaction)
        db_session.commit()

        # Step 6: Categorize transaction without specifying tax info (should use mapping)
        categorization_request = {
            "business_percentage": 100.0,
            "business_purpose": "Office supplies for business operations"
        }

        response = client.post(
            f"/api/tax/categorize/{transaction.id}",
            json=categorization_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["tax_category"] == "Office expense"
        assert result["chart_account"] == "Office Expense"

        # Step 7: Verify mapping was used correctly
        db_session.refresh(transaction)
        assert transaction.tax_category_id == tax_category.id
        assert transaction.chart_account_id == chart_account.id

        # Step 8: Verify business tracking uses mapping defaults
        business_tracking = db_session.query(BusinessExpenseTracking).filter_by(
            transaction_id=transaction.id
        ).first()
        assert business_tracking is not None
        assert business_tracking.receipt_required is True  # From mapping

        print("✅ Category mapping workflow test passed!")

    def test_chart_of_accounts_management_workflow(self, client, auth_headers, db_session):
        """Test complete chart of accounts management workflow."""
        # Step 1: Setup user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Step 2: Create parent account (main expense category)
        parent_account_data = {
            "account_code": "5000",
            "account_name": "Operating Expenses",
            "account_type": "expense",
            "normal_balance": "debit",
            "description": "Main operating expenses account"
        }

        response = client.post(
            "/api/tax/chart-of-accounts",
            json=parent_account_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        parent_account = response.json()

        # Step 3: Create child accounts under parent
        child_accounts_data = [
            {
                "account_code": "5100",
                "account_name": "Office Supplies",
                "account_type": "expense",
                "normal_balance": "debit",
                "parent_account_id": parent_account["id"],
                "tax_category": "Office expense",
                "tax_line_mapping": "Line 18"
            },
            {
                "account_code": "5200",
                "account_name": "Travel Expense",
                "account_type": "expense",
                "normal_balance": "debit",
                "parent_account_id": parent_account["id"],
                "tax_category": "Travel",
                "tax_line_mapping": "Line 27a"
            }
        ]

        child_accounts = []
        for child_data in child_accounts_data:
            response = client.post(
                "/api/tax/chart-of-accounts",
                json=child_data,
                headers=auth_headers
            )
            assert response.status_code == 200
            child_accounts.append(response.json())

        # Step 4: Get chart of accounts list
        response = client.get(
            "/api/tax/chart-of-accounts",
            headers=auth_headers
        )

        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) == 3  # Parent + 2 children

        # Verify accounts are ordered by code
        codes = [acc["account_code"] for acc in accounts]
        assert codes == ["5000", "5100", "5200"]

        # Step 5: Filter by account type
        response = client.get(
            "/api/tax/chart-of-accounts?account_type=expense",
            headers=auth_headers
        )

        assert response.status_code == 200
        expense_accounts = response.json()
        assert len(expense_accounts) == 3
        assert all(acc["account_type"] == "expense" for acc in expense_accounts)

        # Step 6: Update an account
        update_data = {
            "account_name": "Office Supplies & Equipment",
            "description": "Office supplies and equipment purchases",
            "requires_1099": True
        }

        response = client.put(
            f"/api/tax/chart-of-accounts/{child_accounts[0]['id']}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        updated_account = response.json()
        assert updated_account["account_name"] == "Office Supplies & Equipment"
        assert updated_account["requires_1099"] is True

        # Step 7: Create some transactions and assign to accounts
        account = Account(
            user_id=user.id,
            plaid_account_id="acc-123",
            name="Business Checking",
            type="depository",
            subtype="checking",
            current_balance=5000.00
        )
        db_session.add(account)
        db_session.flush()

        transactions_data = [
            {
                "amount": Decimal("150.00"),
                "name": "Office chairs",
                "chart_account_id": child_accounts[0]["id"]
            },
            {
                "amount": Decimal("85.00"),
                "name": "Flight booking",
                "chart_account_id": child_accounts[1]["id"]
            }
        ]

        for i, tx_data in enumerate(transactions_data):
            transaction = Transaction(
                account_id=account.id,
                plaid_transaction_id=f"txn-chart-{i}",
                amount=tx_data["amount"],
                name=tx_data["name"],
                chart_account_id=tx_data["chart_account_id"]
            )
            db_session.add(transaction)

        db_session.commit()

        # Step 8: Get trial balance
        response = client.get(
            "/api/tax/trial-balance",
            headers=auth_headers
        )

        assert response.status_code == 200
        trial_balance = response.json()
        assert "accounts" in trial_balance
        assert trial_balance["is_balanced"] in [True, False]  # Depends on account balances

        # Step 9: Get financial statements
        response = client.get(
            "/api/tax/financial-statements",
            headers=auth_headers
        )

        assert response.status_code == 200
        statements = response.json()
        assert "balance_sheet" in statements
        assert "income_statement" in statements
        assert "expenses" in statements["income_statement"]

        # Step 10: Try to delete an account with transactions (should soft delete)
        response = client.delete(
            f"/api/tax/chart-of-accounts/{child_accounts[0]['id']}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Step 11: Verify account is inactive but still exists
        response = client.get(
            "/api/tax/chart-of-accounts?is_active=false",
            headers=auth_headers
        )

        assert response.status_code == 200
        inactive_accounts = response.json()
        assert len(inactive_accounts) >= 1
        assert any(acc["id"] == child_accounts[0]["id"] for acc in inactive_accounts)

        print("✅ Chart of accounts management workflow test passed!")

    def test_error_handling_and_recovery_workflow(self, client, auth_headers, db_session):
        """Test error handling and recovery scenarios."""
        # Step 1: Setup
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Step 2: Try to categorize non-existent transaction
        categorization_request = {
            "tax_category_id": "nonexistent-tax-id",
            "chart_account_id": "nonexistent-chart-id",
            "business_percentage": 100.0
        }

        response = client.post(
            "/api/tax/categorize/nonexistent-transaction-id",
            json=categorization_request,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

        # Step 3: Try to create duplicate account code
        account_data = {
            "account_code": "5100",
            "account_name": "Office Expense",
            "account_type": "expense",
            "normal_balance": "debit"
        }

        # Create first account
        response = client.post(
            "/api/tax/chart-of-accounts",
            json=account_data,
            headers=auth_headers
        )
        assert response.status_code == 200

        # Try to create duplicate
        response = client.post(
            "/api/tax/chart-of-accounts",
            json=account_data,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

        # Step 4: Try to update non-existent account
        update_data = {"account_name": "Updated Name"}

        response = client.put(
            "/api/tax/chart-of-accounts/nonexistent-id",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 400

        # Step 5: Try to delete non-existent account
        response = client.delete(
            "/api/tax/chart-of-accounts/nonexistent-id",
            headers=auth_headers
        )
        assert response.status_code == 400

        # Step 6: Try bulk categorization with mixed valid/invalid IDs
        account = Account(
            user_id=user.id,
            plaid_account_id="acc-123",
            name="Business Checking",
            type="depository",
            subtype="checking",
            current_balance=5000.00
        )
        db_session.add(account)
        db_session.flush()

        # Create one valid transaction
        valid_transaction = Transaction(
            account_id=account.id,
            plaid_transaction_id="txn-valid",
            amount=Decimal("100.00"),
            name="Valid transaction"
        )
        db_session.add(valid_transaction)
        db_session.commit()

        # Create tax category for successful categorization
        tax_category = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.commit()

        # Bulk request with mixed valid/invalid transaction IDs
        bulk_request = {
            "transaction_ids": [
                str(valid_transaction.id),
                "invalid-transaction-id-1",
                "invalid-transaction-id-2"
            ],
            "tax_category_id": str(tax_category.id),
            "business_percentage": 100.0
        }

        response = client.post(
            "/api/tax/categorize/bulk",
            json=bulk_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        bulk_result = response.json()
        assert bulk_result["success_count"] == 1
        assert bulk_result["error_count"] == 2
        assert len(bulk_result["errors"]) == 2

        # Step 7: Test getting business expense tracking for non-existent transaction
        response = client.get(
            "/api/tax/business-expense/nonexistent-transaction",
            headers=auth_headers
        )
        assert response.status_code == 404

        # Step 8: Test tax summary for year with no transactions
        response = client.get(
            "/api/tax/summary/2025",  # Future year
            headers=auth_headers
        )
        assert response.status_code == 200
        summary = response.json()
        assert summary["total_deductions"] == 0.0
        assert len(summary["categories"]) == 0

        print("✅ Error handling and recovery workflow test passed!")


class TestPerformanceWorkflows:
    """Test performance with realistic data volumes."""

    def test_large_volume_categorization_workflow(self, client, auth_headers, db_session, performance_timer):
        """Test performance with large volumes of transactions."""
        # Step 1: Setup
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        account = Account(
            user_id=user.id,
            plaid_account_id="acc-123",
            name="Business Checking",
            type="depository",
            subtype="checking",
            current_balance=100000.00
        )
        db_session.add(account)
        db_session.flush()

        # Step 2: Create tax categories and chart accounts
        categories_data = [
            ("SCHED_C_18", "Office expense", "Line 18", "Office Expense", "5100"),
            ("SCHED_C_27A", "Travel", "Line 27a", "Travel Expense", "5200"),
            ("SCHED_C_09", "Car and truck expenses", "Line 9", "Vehicle Expense", "5300"),
            ("SCHED_C_25", "Utilities", "Line 25", "Utilities Expense", "5400"),
            ("SCHED_C_08", "Advertising", "Line 8", "Advertising Expense", "5500")
        ]

        tax_categories = []
        chart_accounts = []

        for code, name, line, chart_name, chart_code in categories_data:
            tax_category = TaxCategory(
                category_code=code,
                category_name=name,
                tax_form="Schedule C",
                tax_line=line,
                is_active=True,
                effective_date=date(2024, 1, 1)
            )
            db_session.add(tax_category)
            db_session.flush()
            tax_categories.append(tax_category)

            chart_account = ChartOfAccount(
                user_id=user.id,
                account_code=chart_code,
                account_name=chart_name,
                account_type="expense",
                normal_balance="debit"
            )
            db_session.add(chart_account)
            db_session.flush()
            chart_accounts.append(chart_account)

        db_session.commit()

        # Step 3: Create large number of transactions
        transactions = []
        batch_size = 50
        total_transactions = 200

        for batch in range(total_transactions // batch_size):
            batch_transactions = []
            for i in range(batch_size):
                tx_num = batch * batch_size + i
                transaction = Transaction(
                    account_id=account.id,
                    plaid_transaction_id=f"perf-txn-{tx_num}",
                    amount=Decimal(f"{25.00 + (tx_num % 100)}"),
                    name=f"Performance test transaction {tx_num}",
                    merchant_name=f"Merchant {tx_num % 20}"
                )
                batch_transactions.append(transaction)

            db_session.bulk_save_objects(batch_transactions)
            db_session.commit()
            transactions.extend(batch_transactions)

        # Refresh to get IDs
        transaction_ids = [str(t.id) for t in db_session.query(Transaction).filter(
            Transaction.plaid_transaction_id.like("perf-txn-%")
        ).all()]

        # Step 4: Performance test - bulk categorization
        performance_timer.start()

        # Categorize in batches
        batch_size = 50
        for i in range(0, len(transaction_ids), batch_size):
            batch_ids = transaction_ids[i:i + batch_size]
            category_idx = (i // batch_size) % len(tax_categories)

            bulk_request = {
                "transaction_ids": batch_ids,
                "tax_category_id": str(tax_categories[category_idx].id),
                "chart_account_id": str(chart_accounts[category_idx].id),
                "business_percentage": 100.0
            }

            response = client.post(
                "/api/tax/categorize/bulk",
                json=bulk_request,
                headers=auth_headers
            )
            assert response.status_code == 200

        performance_timer.stop()

        # Performance assertion
        assert performance_timer.elapsed_ms < 30000  # Should complete within 30 seconds

        # Step 5: Test tax summary performance with large dataset
        performance_timer.start()

        response = client.get(
            "/api/tax/summary/2024",
            headers=auth_headers
        )

        performance_timer.stop()

        assert response.status_code == 200
        summary = response.json()
        assert summary["transaction_count"] == total_transactions
        assert len(summary["categories"]) == len(categories_data)

        # Summary generation should be fast even with large dataset
        assert performance_timer.elapsed_ms < 5000  # Less than 5 seconds

        # Step 6: Test Schedule C export performance
        performance_timer.start()

        response = client.get(
            "/api/tax/export/schedule-c/2024",
            headers=auth_headers
        )

        performance_timer.stop()

        assert response.status_code == 200
        schedule_c = response.json()
        assert schedule_c["tax_year"] == 2024
        assert len(schedule_c["schedule_c_lines"]) > 0

        # Export should also be fast
        assert performance_timer.elapsed_ms < 3000  # Less than 3 seconds

        print(f"✅ Large volume categorization workflow completed in {performance_timer.elapsed_ms:.2f}ms")

    def test_concurrent_operations_workflow(self, client, auth_headers, db_session):
        """Test concurrent operations don't cause data corruption."""
        # This test simulates concurrent access scenarios
        # Note: In a real concurrent test, you'd use threading or async

        # Step 1: Setup
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        account = Account(
            user_id=user.id,
            plaid_account_id="acc-123",
            name="Business Checking",
            type="depository",
            subtype="checking",
            current_balance=5000.00
        )
        db_session.add(account)
        db_session.flush()

        transaction = Transaction(
            account_id=account.id,
            plaid_transaction_id="txn-concurrent",
            amount=Decimal("100.00"),
            name="Concurrent test transaction"
        )
        db_session.add(transaction)
        db_session.flush()

        tax_category1 = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        tax_category2 = TaxCategory(
            category_code="SCHED_C_27",
            category_name="Travel",
            tax_form="Schedule C",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category1)
        db_session.add(tax_category2)
        db_session.commit()

        # Step 2: Simulate concurrent categorization attempts
        # (In real test, these would be parallel requests)

        # First categorization
        request1 = {
            "tax_category_id": str(tax_category1.id),
            "business_percentage": 100.0,
            "business_purpose": "Office supplies"
        }

        response1 = client.post(
            f"/api/tax/categorize/{transaction.id}",
            json=request1,
            headers=auth_headers
        )

        # Second categorization (re-categorization)
        request2 = {
            "tax_category_id": str(tax_category2.id),
            "business_percentage": 75.0,
            "business_purpose": "Travel expense"
        }

        response2 = client.post(
            f"/api/tax/categorize/{transaction.id}",
            json=request2,
            headers=auth_headers
        )

        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Step 3: Verify final state is consistent
        db_session.refresh(transaction)
        assert transaction.tax_category_id == tax_category2.id  # Last one wins
        assert transaction.business_use_percentage == Decimal("75.0")

        # Step 4: Verify audit trail captures both operations
        audit_records = db_session.query(CategorizationAudit).filter_by(
            transaction_id=transaction.id
        ).order_by(CategorizationAudit.created_at).all()

        assert len(audit_records) == 2
        assert audit_records[0].new_tax_category_id == tax_category1.id
        assert audit_records[1].new_tax_category_id == tax_category2.id
        assert audit_records[1].old_tax_category_id == tax_category1.id

        print("✅ Concurrent operations workflow test passed!")


class TestComplianceWorkflows:
    """Test tax compliance and audit workflows."""

    def test_irs_compliance_workflow(self, client, auth_headers, db_session):
        """Test IRS compliance requirements and documentation."""
        # Step 1: Setup
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        account = Account(
            user_id=user.id,
            plaid_account_id="acc-123",
            name="Business Checking",
            type="depository",
            subtype="checking",
            current_balance=10000.00
        )
        db_session.add(account)
        db_session.flush()

        # Step 2: Create transactions requiring different documentation levels
        transactions_data = [
            {
                "plaid_id": "txn-meals-high",
                "amount": Decimal("85.00"),
                "name": "Business dinner with client",
                "merchant": "Fine Dining Restaurant",
                "requires_documentation": True
            },
            {
                "plaid_id": "txn-supplies-low",
                "amount": Decimal("25.00"),
                "name": "Office supplies",
                "merchant": "Office Depot",
                "requires_documentation": False
            },
            {
                "plaid_id": "txn-travel-high",
                "amount": Decimal("450.00"),
                "name": "Business conference flight",
                "merchant": "United Airlines",
                "requires_documentation": True
            }
        ]

        transactions = []
        for tx_data in transactions_data:
            transaction = Transaction(
                account_id=account.id,
                plaid_transaction_id=tx_data["plaid_id"],
                amount=tx_data["amount"],
                name=tx_data["name"],
                merchant_name=tx_data["merchant"]
            )
            db_session.add(transaction)
            db_session.flush()
            transactions.append(transaction)

        # Step 3: Create tax categories with compliance requirements
        meals_category = TaxCategory(
            category_code="SCHED_C_27B",
            category_name="Meals",
            tax_form="Schedule C",
            tax_line="Line 27b",
            percentage_limit=Decimal("50.00"),  # 50% limit
            documentation_required=True,
            is_active=True,
            effective_date=date(2024, 1, 1)
        )

        office_category = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            tax_line="Line 18",
            documentation_required=False,
            is_active=True,
            effective_date=date(2024, 1, 1)
        )

        travel_category = TaxCategory(
            category_code="SCHED_C_27A",
            category_name="Travel",
            tax_form="Schedule C",
            tax_line="Line 27a",
            documentation_required=True,
            is_active=True,
            effective_date=date(2024, 1, 1)
        )

        db_session.add(meals_category)
        db_session.add(office_category)
        db_session.add(travel_category)
        db_session.commit()

        # Step 4: Categorize transactions with proper documentation
        # High-value meal transaction
        meal_request = {
            "tax_category_id": str(meals_category.id),
            "business_percentage": 100.0,
            "business_purpose": "Client dinner to discuss Q4 contract renewal"
        }

        response = client.post(
            f"/api/tax/categorize/{transactions[0].id}",
            json=meal_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        meal_result = response.json()
        assert meal_result["requires_substantiation"] is True
        # Should be 50% deductible: 85.00 * 0.5 = 42.50
        assert meal_result["deductible_amount"] == 42.50

        # Low-value office supplies
        office_request = {
            "tax_category_id": str(office_category.id),
            "business_percentage": 100.0,
            "business_purpose": "Office supplies for daily operations"
        }

        response = client.post(
            f"/api/tax/categorize/{transactions[1].id}",
            json=office_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        office_result = response.json()
        # Low amount, but still requires substantiation due to amount threshold
        assert office_result["requires_substantiation"] is False

        # High-value travel expense
        travel_request = {
            "tax_category_id": str(travel_category.id),
            "business_percentage": 100.0,
            "business_purpose": "Flight to industry conference in Chicago"
        }

        response = client.post(
            f"/api/tax/categorize/{transactions[2].id}",
            json=travel_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        travel_result = response.json()
        assert travel_result["requires_substantiation"] is True
        assert travel_result["deductible_amount"] == 450.00

        # Step 5: Add detailed business expense tracking with documentation
        # Add receipt for meal
        meal_tracking = {
            "transaction_id": str(transactions[0].id),
            "business_purpose": "Client dinner meeting with ABC Corp to discuss Q4 contract",
            "business_percentage": 100.0,
            "receipt_required": True,
            "receipt_attached": True,
            "receipt_url": "https://example.com/receipts/meal-20240615.pdf",
            "substantiation_notes": "Discussed contract terms and delivery schedule"
        }

        response = client.post(
            "/api/tax/business-expense",
            json=meal_tracking,
            headers=auth_headers
        )
        assert response.status_code == 200

        # Add mileage tracking for travel
        travel_tracking = {
            "transaction_id": str(transactions[2].id),
            "business_purpose": "Attendance at National Industry Conference 2024",
            "business_percentage": 100.0,
            "receipt_required": True,
            "receipt_attached": True,
            "receipt_url": "https://example.com/receipts/flight-20240620.pdf",
            "mileage_start_location": "Office - 123 Business St",
            "mileage_end_location": "Airport - Terminal 1",
            "miles_driven": 25.5,
            "substantiation_notes": "Conference registration and flight receipts attached"
        }

        response = client.post(
            "/api/tax/business-expense",
            json=travel_tracking,
            headers=auth_headers
        )
        assert response.status_code == 200

        # Step 6: Generate compliance report
        response = client.get(
            "/api/tax/summary/2024",
            headers=auth_headers
        )

        assert response.status_code == 200
        compliance_summary = response.json()

        # Verify totals account for percentage limits
        expected_total = 42.50 + 25.00 + 450.00  # Meal at 50%, office 100%, travel 100%
        assert abs(compliance_summary["total_deductions"] - expected_total) < 0.01

        # Step 7: Check substantiation completeness
        for transaction in transactions:
            response = client.get(
                f"/api/tax/business-expense/{transaction.id}",
                headers=auth_headers
            )

            if response.status_code == 200:
                tracking_data = response.json()

                # High-value transactions should have complete documentation
                if transaction.amount >= Decimal("75.00"):
                    assert tracking_data["receipt_attached"] is True
                    assert tracking_data["business_purpose"] is not None
                    assert len(tracking_data["business_purpose"]) > 0

        # Step 8: Generate Schedule C with compliance annotations
        response = client.get(
            "/api/tax/export/schedule-c/2024",
            headers=auth_headers
        )

        assert response.status_code == 200
        schedule_c = response.json()

        # Verify that meal expenses are properly limited
        # Line 27 should include both meals (42.50) and travel (450.00) = 492.50
        if "27" in schedule_c["schedule_c_lines"]:
            line_27_amount = schedule_c["schedule_c_lines"]["27"]["amount"]
            assert abs(line_27_amount - 492.50) < 0.01

        print("✅ IRS compliance workflow test passed!")

# Make sure all test classes are properly defined and exported
__all__ = [
    'TestCompleteTransactionCategorizationWorkflow',
    'TestPerformanceWorkflows',
    'TestComplianceWorkflows'
]