"""Comprehensive tests for tax categorization system."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Import models
from models.tax_categorization import (
    TaxCategory, ChartOfAccount, BusinessExpenseTracking,
    CategoryMapping, CategorizationAudit
)
from models.transaction import Transaction
from models.user import User
from models.category import Category

# Import services
from src.services.tax_categorization_service import TaxCategorizationService
from src.services.chart_of_accounts_service import ChartOfAccountsService


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def sample_user():
    """Create a sample user."""
    user = Mock(spec=User)
    user.id = "user-123"
    user.email = "test@example.com"
    return user


@pytest.fixture
def sample_transaction():
    """Create a sample transaction."""
    transaction = Mock(spec=Transaction)
    transaction.id = "trans-123"
    transaction.account_id = "acc-123"
    transaction.amount = Decimal("100.00")
    transaction.amount_decimal = Decimal("100.00")
    transaction.name = "Office supplies purchase"
    transaction.merchant_name = "Staples"
    transaction.description = "Business office supplies"
    transaction.category_id = "cat-123"
    transaction.tax_category_id = None
    transaction.chart_account_id = None
    transaction.business_use_percentage = Decimal("0.00")
    transaction.deductible_amount = None
    transaction.requires_substantiation = False
    transaction.substantiation_complete = False
    transaction.schedule_c_line = None
    transaction.tax_notes = None
    return transaction


@pytest.fixture
def sample_tax_category():
    """Create a sample tax category."""
    tax_category = Mock(spec=TaxCategory)
    tax_category.id = "tax-cat-123"
    tax_category.category_code = "SCHED_C_18"
    tax_category.category_name = "Office expense"
    tax_category.tax_form = "Schedule C"
    tax_category.tax_line = "Line 18"
    tax_category.description = "Office supplies and expenses"
    tax_category.deduction_type = "ordinary"
    tax_category.percentage_limit = None
    tax_category.dollar_limit = None
    tax_category.documentation_required = False
    tax_category.is_business_expense = True
    tax_category.is_active = True
    tax_category.effective_date = date(2024, 1, 1)
    tax_category.expiration_date = None
    tax_category.keywords = ["office", "supplies", "paper", "pens"]
    tax_category.exclusions = ["personal"]
    tax_category.is_currently_effective.return_value = True
    tax_category.calculate_deductible_amount.return_value = Decimal("100.00")
    return tax_category


@pytest.fixture
def sample_chart_account():
    """Create a sample chart of accounts entry."""
    account = Mock(spec=ChartOfAccount)
    account.id = "chart-acc-123"
    account.user_id = "user-123"
    account.account_code = "5100"
    account.account_name = "Office Expense"
    account.account_type = "expense"
    account.normal_balance = "debit"
    account.is_active = True
    account.is_system_account = False
    account.current_balance = Decimal("0.00")
    account.tax_category = "Office expense"
    account.tax_line_mapping = "Line 18"
    account.requires_1099 = False
    account.description = "Office supplies and related expenses"
    return account


class TestTaxCategorizationService:
    """Comprehensive tests for TaxCategorizationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.service = TaxCategorizationService(self.mock_session)

    def test_categorize_for_tax_success_with_provided_ids(self, sample_transaction, sample_tax_category, sample_chart_account):
        """Test successful tax categorization with provided category and account IDs."""
        # Setup mocks
        self.mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_transaction,  # Transaction query
            sample_tax_category,  # Tax category query
            sample_chart_account  # Chart account query
        ]

        with patch.object(self.service, '_requires_substantiation', return_value=True), \
             patch.object(self.service, '_create_or_update_business_tracking'), \
             patch.object(self.service, '_create_audit_record'):

            result = self.service.categorize_for_tax(
                transaction_id="trans-123",
                user_id="user-123",
                tax_category_id="tax-cat-123",
                chart_account_id="chart-acc-123",
                business_percentage=Decimal("100.00"),
                business_purpose="Office supplies for business"
            )

        # Assertions
        assert result["success"] is True
        assert result["transaction_id"] == "trans-123"
        assert result["tax_category"] == "Office expense"
        assert result["chart_account"] == "Office Expense"
        assert result["deductible_amount"] == 100.00
        assert result["requires_substantiation"] is True

        # Verify transaction updates
        assert sample_transaction.tax_category_id == "tax-cat-123"
        assert sample_transaction.chart_account_id == "chart-acc-123"
        assert sample_transaction.business_use_percentage == Decimal("100.00")
        assert sample_transaction.deductible_amount == Decimal("100.00")
        assert sample_transaction.schedule_c_line == "Line 18"
        assert sample_transaction.requires_substantiation is True

        self.mock_session.commit.assert_called_once()

    def test_categorize_for_tax_with_auto_detection(self, sample_transaction, sample_tax_category, sample_chart_account):
        """Test tax categorization with auto-detection."""
        # Setup mocks
        self.mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_transaction,  # Transaction query
            sample_tax_category,  # Tax category query
            sample_chart_account  # Chart account query
        ]

        with patch.object(self.service, 'auto_detect_tax_category', return_value={
            "tax_category_id": "tax-cat-123",
            "chart_account_id": "chart-acc-123"
        }), \
        patch.object(self.service, '_requires_substantiation', return_value=False), \
        patch.object(self.service, '_create_or_update_business_tracking'), \
        patch.object(self.service, '_create_audit_record'):

            result = self.service.categorize_for_tax(
                transaction_id="trans-123",
                user_id="user-123"
            )

        assert result["success"] is True
        self.mock_session.commit.assert_called_once()

    def test_categorize_for_tax_invalid_transaction(self):
        """Test categorization with invalid transaction ID."""
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Transaction .* not found"):
            self.service.categorize_for_tax(
                transaction_id="invalid-id",
                user_id="user-123"
            )

    def test_categorize_for_tax_invalid_tax_category(self, sample_transaction):
        """Test categorization with invalid tax category."""
        # Mock transaction found, but tax category not found
        self.mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            sample_transaction,  # Transaction query
            None  # Tax category query
        ]

        with pytest.raises(ValueError, match="Invalid or inactive tax category"):
            self.service.categorize_for_tax(
                transaction_id="trans-123",
                user_id="user-123",
                tax_category_id="invalid-tax-cat"
            )

    def test_categorize_for_tax_rollback_on_error(self, sample_transaction):
        """Test that database is rolled back on error."""
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = sample_transaction
        self.mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            self.service.categorize_for_tax(
                transaction_id="trans-123",
                user_id="user-123"
            )

        self.mock_session.rollback.assert_called_once()

    def test_auto_detect_tax_category_with_mapping(self):
        """Test auto-detection using existing category mapping."""
        transaction = Mock(spec=Transaction)
        transaction.category_id = "cat-123"
        transaction.name = "Office supplies"
        transaction.merchant_name = "Staples"
        transaction.description = "Business supplies"

        mapping = Mock(spec=CategoryMapping)
        mapping.tax_category_id = "tax-cat-123"
        mapping.chart_account_id = "chart-acc-123"
        mapping.confidence_score = Decimal("0.95")

        # Mock successful mapping query
        self.mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mapping

        result = self.service.auto_detect_tax_category(transaction, "user-123")

        assert result["tax_category_id"] == "tax-cat-123"
        assert result["chart_account_id"] == "chart-acc-123"
        assert result["confidence"] == 0.95
        assert result["source"] == "category_mapping"

    def test_auto_detect_tax_category_keyword_matching(self, sample_tax_category):
        """Test auto-detection using keyword matching."""
        transaction = Mock(spec=Transaction)
        transaction.category_id = None
        transaction.name = "Gas station fuel"
        transaction.merchant_name = "Shell"
        transaction.description = "Vehicle fuel"

        chart_account = Mock(spec=ChartOfAccount)
        chart_account.id = "chart-acc-vehicle"

        # Mock no mapping found, but tax categories available
        mock_query_chain = Mock()
        mock_query_chain.filter.return_value.order_by.return_value.first.return_value = None  # No mapping
        mock_query_chain.filter.return_value.all.return_value = [sample_tax_category]  # Available categories
        self.mock_session.query.return_value = mock_query_chain

        # Mock chart account query
        mock_chart_query = Mock()
        mock_chart_query.filter.return_value.first.return_value = chart_account
        self.mock_session.query.side_effect = [mock_query_chain, mock_query_chain, mock_chart_query]

        with patch.object(self.service, '_calculate_keyword_match_score', return_value=0.5):
            result = self.service.auto_detect_tax_category(transaction, "user-123")

        assert result["tax_category_id"] == "tax-cat-123"
        assert result["chart_account_id"] == "chart-acc-vehicle"
        assert result["confidence"] == 0.5
        assert result["source"] == "keyword_matching"

    def test_auto_detect_tax_category_no_match(self):
        """Test auto-detection when no matches found."""
        transaction = Mock(spec=Transaction)
        transaction.category_id = None
        transaction.name = "Unknown transaction"
        transaction.merchant_name = None
        transaction.description = None

        # Mock no mapping and no good keyword matches
        mock_query_chain = Mock()
        mock_query_chain.filter.return_value.order_by.return_value.first.return_value = None
        mock_query_chain.filter.return_value.all.return_value = []
        self.mock_session.query.return_value = mock_query_chain

        result = self.service.auto_detect_tax_category(transaction, "user-123")

        assert result["tax_category_id"] is None
        assert result["chart_account_id"] is None
        assert result["confidence"] == 0.0
        assert result["source"] == "no_match"

    def test_calculate_keyword_match_score(self, sample_tax_category):
        """Test keyword match score calculation."""
        # Test full match
        score = self.service._calculate_keyword_match_score(
            "office supplies paper pens", sample_tax_category
        )
        assert score == 1.0  # All 4 keywords matched

        # Test partial match
        score = self.service._calculate_keyword_match_score(
            "office supplies", sample_tax_category
        )
        assert score == 0.5  # 2 out of 4 keywords matched

        # Test exclusion
        score = self.service._calculate_keyword_match_score(
            "office supplies personal", sample_tax_category
        )
        assert score == 0.0  # Excluded due to "personal"

        # Test no keywords
        sample_tax_category.keywords = []
        score = self.service._calculate_keyword_match_score("office", sample_tax_category)
        assert score == 0.0

    def test_get_tax_summary(self):
        """Test tax summary generation."""
        # Create mock transactions
        transaction1 = Mock(spec=Transaction)
        transaction1.deductible_amount = Decimal("150.00")
        transaction1.requires_substantiation = True
        transaction1.substantiation_complete = False
        transaction1.tax_category = Mock()
        transaction1.tax_category.category_code = "SCHED_C_18"
        transaction1.tax_category.category_name = "Office expense"
        transaction1.tax_category.tax_form = "Schedule C"
        transaction1.tax_category.tax_line = "Line 18"

        transaction2 = Mock(spec=Transaction)
        transaction2.deductible_amount = Decimal("75.00")
        transaction2.requires_substantiation = False
        transaction2.substantiation_complete = True
        transaction2.tax_category = Mock()
        transaction2.tax_category.category_code = "SCHED_C_27"
        transaction2.tax_category.category_name = "Travel"
        transaction2.tax_category.tax_form = "Schedule C"
        transaction2.tax_category.tax_line = "Line 27a"

        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = [transaction1, transaction2]
        self.mock_session.query.return_value = mock_query

        result = self.service.get_tax_summary("user-123", 2024)

        assert result["tax_year"] == 2024
        assert result["total_deductions"] == 225.00
        assert result["transaction_count"] == 2
        assert len(result["categories"]) == 2

        # Check office expense category
        office_cat = result["categories"]["SCHED_C_18"]
        assert office_cat["category_name"] == "Office expense"
        assert office_cat["total_amount"] == 150.00
        assert office_cat["transaction_count"] == 1
        assert office_cat["requires_substantiation"] == 1

        # Check travel category
        travel_cat = result["categories"]["SCHED_C_27"]
        assert travel_cat["category_name"] == "Travel"
        assert travel_cat["total_amount"] == 75.00
        assert travel_cat["transaction_count"] == 1
        assert travel_cat["requires_substantiation"] == 0

    def test_bulk_categorize_for_tax_success(self):
        """Test successful bulk categorization."""
        transaction_ids = ["trans-1", "trans-2", "trans-3"]

        # Mock individual categorization calls
        with patch.object(self.service, 'categorize_for_tax') as mock_categorize:
            mock_categorize.return_value = {
                "success": True,
                "transaction_id": "trans-1",
                "tax_category": "Office expense"
            }

            result = self.service.bulk_categorize_for_tax(
                transaction_ids=transaction_ids,
                user_id="user-123",
                tax_category_id="tax-cat-123"
            )

        assert result["success_count"] == 3
        assert result["error_count"] == 0
        assert len(result["results"]) == 3
        assert len(result["errors"]) == 0
        assert mock_categorize.call_count == 3

    def test_bulk_categorize_for_tax_with_errors(self):
        """Test bulk categorization with some errors."""
        transaction_ids = ["trans-1", "trans-2", "trans-3"]

        # Mock categorization with some failures
        with patch.object(self.service, 'categorize_for_tax') as mock_categorize:
            def side_effect(transaction_id, **kwargs):
                if transaction_id == "trans-2":
                    raise ValueError("Invalid transaction")
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "tax_category": "Office expense"
                }

            mock_categorize.side_effect = side_effect

            result = self.service.bulk_categorize_for_tax(
                transaction_ids=transaction_ids,
                user_id="user-123",
                tax_category_id="tax-cat-123"
            )

        assert result["success_count"] == 2
        assert result["error_count"] == 1
        assert len(result["results"]) == 2
        assert len(result["errors"]) == 1
        assert result["errors"][0]["transaction_id"] == "trans-2"
        assert "Invalid transaction" in result["errors"][0]["error"]

    def test_get_schedule_c_export(self):
        """Test Schedule C export functionality."""
        with patch.object(self.service, 'get_tax_summary') as mock_summary:
            mock_summary.return_value = {
                "tax_year": 2024,
                "total_deductions": 500.00,
                "categories": {
                    "SCHED_C_18": {
                        "category_name": "Office expense",
                        "tax_form": "Schedule C",
                        "tax_line": "Line 18",
                        "total_amount": 200.00,
                        "transaction_count": 3
                    },
                    "SCHED_C_27": {
                        "category_name": "Travel",
                        "tax_form": "Schedule C",
                        "tax_line": "Line 27a",
                        "total_amount": 300.00,
                        "transaction_count": 2
                    }
                }
            }

            result = self.service.get_schedule_c_export("user-123", 2024)

        assert result["tax_year"] == 2024
        assert "18" in result["schedule_c_lines"]
        assert "27" in result["schedule_c_lines"]
        assert result["schedule_c_lines"]["18"]["amount"] == 200.00
        assert result["schedule_c_lines"]["27"]["amount"] == 300.00
        assert result["total_expenses"] == 500.00

    def test_requires_substantiation_amount_threshold(self):
        """Test substantiation requirement based on amount threshold."""
        transaction = Mock(spec=Transaction)
        transaction.amount_decimal = Decimal("75.00")

        # Amount >= $75 should require substantiation
        assert self.service._requires_substantiation(transaction, None) is True

        # Amount < $75 should not require substantiation (if no other rules)
        transaction.amount_decimal = Decimal("50.00")
        assert self.service._requires_substantiation(transaction, None) is False

    def test_requires_substantiation_documentation_required(self):
        """Test substantiation requirement based on tax category documentation requirement."""
        transaction = Mock(spec=Transaction)
        transaction.amount_decimal = Decimal("25.00")  # Below threshold

        tax_category = Mock(spec=TaxCategory)
        tax_category.documentation_required = True
        tax_category.category_name = "Regular expense"

        assert self.service._requires_substantiation(transaction, tax_category) is True

    def test_requires_substantiation_special_categories(self):
        """Test substantiation requirement for special categories."""
        transaction = Mock(spec=Transaction)
        transaction.amount_decimal = Decimal("25.00")  # Below threshold

        tax_category = Mock(spec=TaxCategory)
        tax_category.documentation_required = False

        # Test each special category
        special_categories = ["Travel", "Meals", "Entertainment", "Car and truck expenses"]
        for category_name in special_categories:
            tax_category.category_name = category_name
            assert self.service._requires_substantiation(transaction, tax_category) is True

        # Test normal category
        tax_category.category_name = "Office expense"
        assert self.service._requires_substantiation(transaction, tax_category) is False

    def test_create_or_update_business_tracking_new(self, sample_transaction):
        """Test creating new business expense tracking record."""
        # Mock no existing tracking
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch.object(self.service, '_requires_substantiation', return_value=True):
            self.service._create_or_update_business_tracking(
                transaction=sample_transaction,
                user_id="user-123",
                business_percentage=Decimal("80.00"),
                business_purpose="Client meeting expenses"
            )

        self.mock_session.add.assert_called_once()
        added_tracking = self.mock_session.add.call_args[0][0]
        assert added_tracking.transaction_id == "trans-123"
        assert added_tracking.user_id == "user-123"
        assert added_tracking.business_percentage == Decimal("80.00")
        assert added_tracking.business_purpose == "Client meeting expenses"

    def test_create_or_update_business_tracking_existing(self, sample_transaction):
        """Test updating existing business expense tracking record."""
        existing_tracking = Mock(spec=BusinessExpenseTracking)
        existing_tracking.business_percentage = Decimal("50.00")
        existing_tracking.business_purpose = "Old purpose"

        # Mock existing tracking found
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = existing_tracking

        self.service._create_or_update_business_tracking(
            transaction=sample_transaction,
            user_id="user-123",
            business_percentage=Decimal("75.00"),
            business_purpose="Updated purpose"
        )

        # Verify updates
        assert existing_tracking.business_percentage == Decimal("75.00")
        assert existing_tracking.business_purpose == "Updated purpose"
        self.mock_session.add.assert_not_called()

    def test_create_audit_record(self, sample_transaction):
        """Test audit record creation."""
        self.service._create_audit_record(
            transaction=sample_transaction,
            user_id="user-123",
            action_type="tax_categorize",
            old_tax_category_id="old-tax-123",
            new_tax_category_id="new-tax-123",
            reason="Manual categorization"
        )

        self.mock_session.add.assert_called_once()
        audit = self.mock_session.add.call_args[0][0]
        assert audit.transaction_id == "trans-123"
        assert audit.user_id == "user-123"
        assert audit.action_type == "tax_categorize"


class TestChartOfAccountsService:
    """Comprehensive tests for ChartOfAccountsService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.service = ChartOfAccountsService(self.mock_session)

    def test_create_account_success(self):
        """Test successful account creation."""
        # Mock no existing account with same code
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = self.service.create_account(
            user_id="user-123",
            account_code="5100",
            account_name="Advertising Expense",
            account_type="expense",
            normal_balance="debit",
            description="Marketing and advertising costs",
            tax_category="Advertising",
            tax_line_mapping="Line 8"
        )

        # Verify account properties
        assert result.user_id == "user-123"
        assert result.account_code == "5100"
        assert result.account_name == "Advertising Expense"
        assert result.account_type == "expense"
        assert result.normal_balance == "debit"
        assert result.description == "Marketing and advertising costs"
        assert result.tax_category == "Advertising"
        assert result.tax_line_mapping == "Line 8"
        assert result.current_balance == Decimal("0.00")

        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()

    def test_create_account_duplicate_code(self):
        """Test account creation with duplicate code fails."""
        existing_account = Mock(spec=ChartOfAccount)
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = existing_account

        with pytest.raises(ValueError, match="Account code .* already exists"):
            self.service.create_account(
                user_id="user-123",
                account_code="5100",
                account_name="Advertising Expense",
                account_type="expense",
                normal_balance="debit"
            )

        self.mock_session.rollback.assert_called_once()

    def test_create_account_with_invalid_parent(self):
        """Test account creation with invalid parent account."""
        # Mock no existing account with same code, but invalid parent
        self.mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            None,  # No existing account with code
            None   # Parent account not found
        ]

        with pytest.raises(ValueError, match="Parent account .* not found"):
            self.service.create_account(
                user_id="user-123",
                account_code="5100",
                account_name="Advertising Expense",
                account_type="expense",
                normal_balance="debit",
                parent_account_id="invalid-parent"
            )

        self.mock_session.rollback.assert_called_once()

    def test_create_account_rollback_on_error(self):
        """Test that database is rolled back on error."""
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None
        self.mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            self.service.create_account(
                user_id="user-123",
                account_code="5100",
                account_name="Advertising Expense",
                account_type="expense",
                normal_balance="debit"
            )

        self.mock_session.rollback.assert_called_once()

    def test_update_account_success(self, sample_chart_account):
        """Test successful account update."""
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = sample_chart_account

        result = self.service.update_account(
            account_id="chart-acc-123",
            user_id="user-123",
            account_name="Updated Office Expense",
            description="Updated description",
            tax_category="Updated tax category"
        )

        assert result.account_name == "Updated Office Expense"
        assert result.description == "Updated description"
        assert result.tax_category == "Updated tax category"
        self.mock_session.commit.assert_called_once()

    def test_update_account_not_found(self):
        """Test updating non-existent account."""
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Account .* not found"):
            self.service.update_account(
                account_id="nonexistent",
                user_id="user-123",
                account_name="New Name"
            )

    def test_update_account_system_account_restrictions(self):
        """Test that system accounts cannot have core fields modified."""
        system_account = Mock(spec=ChartOfAccount)
        system_account.is_system_account = True
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = system_account

        with pytest.raises(ValueError, match="Cannot modify core fields of system accounts"):
            self.service.update_account(
                account_id="system-acc-123",
                user_id="user-123",
                account_code="NEW_CODE"  # Restricted field
            )

    def test_get_account_balance_debit_account(self):
        """Test balance calculation for debit account."""
        account = Mock(spec=ChartOfAccount)
        account.id = "acc-123"
        account.normal_balance = "debit"

        self.mock_session.query.return_value.filter_by.return_value.first.return_value = account

        # Mock transaction sum queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [Decimal("750.00"), Decimal("250.00")]  # debits, credits
        self.mock_session.query.return_value.filter.return_value = mock_query

        balance = self.service.get_account_balance("acc-123", "user-123")

        # For debit account: debits - credits = 750 - 250 = 500
        assert balance == Decimal("500.00")
        assert account.current_balance == Decimal("500.00")
        self.mock_session.commit.assert_called_once()

    def test_get_account_balance_credit_account(self):
        """Test balance calculation for credit account."""
        account = Mock(spec=ChartOfAccount)
        account.id = "acc-123"
        account.normal_balance = "credit"

        self.mock_session.query.return_value.filter_by.return_value.first.return_value = account

        # Mock transaction sum queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [Decimal("200.00"), Decimal("800.00")]  # debits, credits
        self.mock_session.query.return_value.filter.return_value = mock_query

        balance = self.service.get_account_balance("acc-123", "user-123")

        # For credit account: credits - debits = 800 - 200 = 600
        assert balance == Decimal("600.00")
        assert account.current_balance == Decimal("600.00")

    def test_get_account_balance_with_date_filter(self):
        """Test balance calculation with as_of_date filter."""
        account = Mock(spec=ChartOfAccount)
        account.id = "acc-123"
        account.normal_balance = "debit"

        self.mock_session.query.return_value.filter_by.return_value.first.return_value = account

        # Mock query chain for date filtering
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [Decimal("500.00"), Decimal("100.00")]
        self.mock_session.query.return_value.filter.return_value = mock_query

        balance = self.service.get_account_balance("acc-123", "user-123", "2024-06-30")

        assert balance == Decimal("400.00")  # 500 - 100

    def test_get_trial_balance(self):
        """Test trial balance generation."""
        # Create mock accounts
        asset_account = Mock(spec=ChartOfAccount)
        asset_account.id = "acc-asset"
        asset_account.account_code = "1100"
        asset_account.account_name = "Cash"
        asset_account.account_type = "asset"
        asset_account.normal_balance = "debit"

        liability_account = Mock(spec=ChartOfAccount)
        liability_account.id = "acc-liability"
        liability_account.account_code = "2100"
        liability_account.account_name = "Accounts Payable"
        liability_account.account_type = "liability"
        liability_account.normal_balance = "credit"

        expense_account = Mock(spec=ChartOfAccount)
        expense_account.id = "acc-expense"
        expense_account.account_code = "5100"
        expense_account.account_name = "Office Expense"
        expense_account.account_type = "expense"
        expense_account.normal_balance = "debit"

        accounts = [asset_account, liability_account, expense_account]
        self.mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = accounts

        with patch.object(self.service, 'get_account_balance') as mock_balance:
            mock_balance.side_effect = [
                Decimal("1000.00"),  # Asset balance
                Decimal("500.00"),   # Liability balance
                Decimal("200.00")    # Expense balance
            ]

            result = self.service.get_trial_balance("user-123")

        assert len(result["accounts"]) == 3
        assert result["total_debits"] == 1200.00  # Asset + Expense
        assert result["total_credits"] == 500.00  # Liability
        assert result["is_balanced"] is False  # 1200 != 500
        assert result["as_of_date"] is None

        # Check individual account data
        asset_data = next(acc for acc in result["accounts"] if acc["account_code"] == "1100")
        assert asset_data["debit_balance"] == 1000.00
        assert asset_data["credit_balance"] == 0

        liability_data = next(acc for acc in result["accounts"] if acc["account_code"] == "2100")
        assert liability_data["debit_balance"] == 0
        assert liability_data["credit_balance"] == 500.00

    def test_get_accounts_by_type(self):
        """Test filtering accounts by type."""
        expense_accounts = [Mock(spec=ChartOfAccount), Mock(spec=ChartOfAccount)]
        self.mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = expense_accounts

        result = self.service.get_accounts_by_type("user-123", "expense")

        assert result == expense_accounts
        # Verify correct filter was called
        self.mock_session.query.return_value.filter_by.assert_called_with(
            user_id="user-123",
            account_type="expense",
            is_active=True
        )

    def test_get_account_hierarchy(self):
        """Test hierarchical account structure generation."""
        # Create parent account
        parent_account = Mock(spec=ChartOfAccount)
        parent_account.id = "parent-123"
        parent_account.parent_account_id = None
        parent_account.account_code = "5000"
        parent_account.account_name = "Expenses"

        # Create child account
        child_account = Mock(spec=ChartOfAccount)
        child_account.id = "child-123"
        child_account.parent_account_id = "parent-123"
        child_account.account_code = "5100"
        child_account.account_name = "Office Expense"

        accounts = [parent_account, child_account]
        self.mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = accounts

        with patch.object(self.service, '_account_to_dict') as mock_to_dict:
            mock_to_dict.side_effect = [
                {"id": "parent-123", "account_code": "5000", "children": []},
                {"id": "child-123", "account_code": "5100", "children": []}
            ]

            result = self.service.get_account_hierarchy("user-123")

        assert len(result) == 1  # Only parent should be at root level
        assert result[0]["id"] == "parent-123"
        assert len(result[0]["children"]) == 1  # Should have child
        assert result[0]["children"][0]["id"] == "child-123"

    def test_delete_account_with_transactions_soft_delete(self):
        """Test soft delete of account with transactions."""
        account = Mock(spec=ChartOfAccount)
        account.is_system_account = False
        account.is_active = True
        account.account_code = "5100"

        self.mock_session.query.return_value.filter_by.return_value.first.return_value = account
        self.mock_session.query.return_value.filter_by.return_value.count.return_value = 5  # Has transactions

        result = self.service.delete_account("acc-123", "user-123")

        assert result is True
        assert account.is_active is False  # Soft deleted
        self.mock_session.commit.assert_called_once()
        self.mock_session.delete.assert_not_called()  # Should not hard delete

    def test_delete_account_without_transactions_hard_delete(self):
        """Test hard delete of account without transactions."""
        account = Mock(spec=ChartOfAccount)
        account.is_system_account = False
        account.account_code = "5100"

        self.mock_session.query.return_value.filter_by.return_value.first.return_value = account
        self.mock_session.query.return_value.filter_by.return_value.count.return_value = 0  # No transactions

        result = self.service.delete_account("acc-123", "user-123")

        assert result is True
        self.mock_session.delete.assert_called_once_with(account)
        self.mock_session.commit.assert_called_once()

    def test_delete_account_system_account_error(self):
        """Test that deleting system account raises error."""
        system_account = Mock(spec=ChartOfAccount)
        system_account.is_system_account = True

        self.mock_session.query.return_value.filter_by.return_value.first.return_value = system_account

        with pytest.raises(ValueError, match="Cannot delete system accounts"):
            self.service.delete_account("system-acc", "user-123")

        self.mock_session.rollback.assert_called_once()

    def test_delete_account_not_found(self):
        """Test deleting non-existent account."""
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Account .* not found"):
            self.service.delete_account("nonexistent", "user-123")

    def test_generate_financial_statements(self):
        """Test financial statements generation."""
        with patch.object(self.service, 'get_trial_balance') as mock_trial_balance:
            mock_trial_balance.return_value = {
                "accounts": [
                    {
                        "account_code": "1100",
                        "account_name": "Cash",
                        "account_type": "asset",
                        "balance": 1000.00
                    },
                    {
                        "account_code": "2100",
                        "account_name": "Accounts Payable",
                        "account_type": "liability",
                        "balance": 500.00
                    },
                    {
                        "account_code": "3000",
                        "account_name": "Owner's Equity",
                        "account_type": "equity",
                        "balance": 300.00
                    },
                    {
                        "account_code": "4000",
                        "account_name": "Service Revenue",
                        "account_type": "revenue",
                        "balance": 800.00
                    },
                    {
                        "account_code": "5000",
                        "account_name": "Office Expense",
                        "account_type": "expense",
                        "balance": 200.00
                    }
                ]
            }

            result = self.service.generate_financial_statements("user-123", "2024-12-31")

        # Check balance sheet
        balance_sheet = result["balance_sheet"]
        assert balance_sheet["assets"]["total"] == 1000.00
        assert balance_sheet["liabilities"]["total"] == 500.00
        assert balance_sheet["equity"]["total"] == 300.00

        # Check income statement
        income_statement = result["income_statement"]
        assert income_statement["revenue"]["total"] == 800.00
        assert income_statement["expenses"]["total"] == 200.00
        assert income_statement["net_income"] == 600.00  # 800 - 200

        # Check that equity includes net income
        assert balance_sheet["equity"]["total_with_income"] == 900.00  # 300 + 600


class TestTaxCategoryModel:
    """Test TaxCategory model methods."""

    def test_is_currently_effective_active_within_dates(self):
        """Test effectiveness check for active category within date range."""
        tax_category = TaxCategory(
            category_code="TEST",
            category_name="Test Category",
            tax_form="Schedule C",
            is_active=True,
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 12, 31)
        )

        with patch('models.tax_categorization.date') as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)
            assert tax_category.is_currently_effective() is True

    def test_is_currently_effective_inactive(self):
        """Test effectiveness check for inactive category."""
        tax_category = TaxCategory(
            category_code="TEST",
            category_name="Test Category",
            tax_form="Schedule C",
            is_active=False,
            effective_date=date(2024, 1, 1)
        )

        with patch('models.tax_categorization.date') as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)
            assert tax_category.is_currently_effective() is False

    def test_is_currently_effective_before_effective_date(self):
        """Test effectiveness check before effective date."""
        tax_category = TaxCategory(
            category_code="TEST",
            category_name="Test Category",
            tax_form="Schedule C",
            is_active=True,
            effective_date=date(2024, 6, 1)
        )

        with patch('models.tax_categorization.date') as mock_date:
            mock_date.today.return_value = date(2024, 5, 15)  # Before effective date
            assert tax_category.is_currently_effective() is False

    def test_is_currently_effective_after_expiration(self):
        """Test effectiveness check after expiration date."""
        tax_category = TaxCategory(
            category_code="TEST",
            category_name="Test Category",
            tax_form="Schedule C",
            is_active=True,
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 6, 30)
        )

        with patch('models.tax_categorization.date') as mock_date:
            mock_date.today.return_value = date(2024, 7, 15)  # After expiration
            assert tax_category.is_currently_effective() is False

    def test_calculate_deductible_amount_with_percentage_limit(self):
        """Test deductible amount calculation with percentage limit."""
        tax_category = TaxCategory(
            category_code="MEALS",
            category_name="Meals",
            tax_form="Schedule C",
            percentage_limit=Decimal("50.00"),
            effective_date=date(2024, 1, 1)
        )

        amount = Decimal("100.00")
        deductible = tax_category.calculate_deductible_amount(amount)
        assert deductible == Decimal("50.00")  # 50% of 100

    def test_calculate_deductible_amount_no_limits(self):
        """Test deductible amount calculation without limits."""
        tax_category = TaxCategory(
            category_code="OFFICE",
            category_name="Office Expense",
            tax_form="Schedule C",
            percentage_limit=None,
            dollar_limit=None,
            effective_date=date(2024, 1, 1)
        )

        amount = Decimal("150.00")
        deductible = tax_category.calculate_deductible_amount(amount)
        assert deductible == Decimal("150.00")  # Full amount

    def test_calculate_deductible_amount_percentage_less_than_amount(self):
        """Test percentage limit that results in less than original amount."""
        tax_category = TaxCategory(
            category_code="ENTERTAINMENT",
            category_name="Entertainment",
            tax_form="Schedule C",
            percentage_limit=Decimal("0.00"),  # 0% deductible
            effective_date=date(2024, 1, 1)
        )

        amount = Decimal("200.00")
        deductible = tax_category.calculate_deductible_amount(amount)
        assert deductible == Decimal("0.00")


class TestBusinessExpenseTrackingModel:
    """Test BusinessExpenseTracking model methods."""

    def test_calculate_business_amount(self):
        """Test business amount calculation."""
        tracking = BusinessExpenseTracking(
            transaction_id="trans-123",
            user_id="user-123",
            business_percentage=Decimal("75.50")
        )

        total_amount = Decimal("200.00")
        business_amount = tracking.calculate_business_amount(total_amount)
        assert business_amount == Decimal("151.00")  # 75.5% of 200

    def test_calculate_business_amount_100_percent(self):
        """Test business amount calculation at 100%."""
        tracking = BusinessExpenseTracking(
            transaction_id="trans-123",
            user_id="user-123",
            business_percentage=Decimal("100.00")
        )

        total_amount = Decimal("150.00")
        business_amount = tracking.calculate_business_amount(total_amount)
        assert business_amount == Decimal("150.00")

    def test_calculate_business_amount_zero_percent(self):
        """Test business amount calculation at 0%."""
        tracking = BusinessExpenseTracking(
            transaction_id="trans-123",
            user_id="user-123",
            business_percentage=Decimal("0.00")
        )

        total_amount = Decimal("100.00")
        business_amount = tracking.calculate_business_amount(total_amount)
        assert business_amount == Decimal("0.00")

    def test_is_substantiation_complete_all_requirements_met(self):
        """Test substantiation completeness when all requirements are met."""
        tracking = BusinessExpenseTracking(
            transaction_id="trans-123",
            user_id="user-123",
            business_purpose="Client meeting dinner",
            receipt_required=True,
            receipt_attached=True
        )

        assert tracking.is_substantiation_complete() is True

    def test_is_substantiation_complete_missing_receipt(self):
        """Test substantiation completeness with missing receipt."""
        tracking = BusinessExpenseTracking(
            transaction_id="trans-123",
            user_id="user-123",
            business_purpose="Client meeting dinner",
            receipt_required=True,
            receipt_attached=False
        )

        assert tracking.is_substantiation_complete() is False

    def test_is_substantiation_complete_missing_purpose(self):
        """Test substantiation completeness with missing business purpose."""
        tracking = BusinessExpenseTracking(
            transaction_id="trans-123",
            user_id="user-123",
            business_purpose=None,
            receipt_required=True,
            receipt_attached=True
        )

        assert tracking.is_substantiation_complete() is False

    def test_is_substantiation_complete_no_receipt_required(self):
        """Test substantiation completeness when no receipt is required."""
        tracking = BusinessExpenseTracking(
            transaction_id="trans-123",
            user_id="user-123",
            business_purpose="Small office supply purchase",
            receipt_required=False,
            receipt_attached=False
        )

        assert tracking.is_substantiation_complete() is True


class TestCategoryMappingModel:
    """Test CategoryMapping model methods."""

    def test_is_currently_active_within_dates(self):
        """Test activity check within effective dates."""
        mapping = CategoryMapping(
            user_id="user-123",
            source_category_id="cat-123",
            chart_account_id="chart-123",
            tax_category_id="tax-123",
            is_active=True,
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 12, 31)
        )

        with patch('models.tax_categorization.date') as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)
            assert mapping.is_currently_active() is True

    def test_is_currently_active_inactive(self):
        """Test activity check for inactive mapping."""
        mapping = CategoryMapping(
            user_id="user-123",
            source_category_id="cat-123",
            chart_account_id="chart-123",
            tax_category_id="tax-123",
            is_active=False,
            effective_date=date(2024, 1, 1)
        )

        with patch('models.tax_categorization.date') as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)
            assert mapping.is_currently_active() is False

    def test_is_currently_active_expired(self):
        """Test activity check for expired mapping."""
        mapping = CategoryMapping(
            user_id="user-123",
            source_category_id="cat-123",
            chart_account_id="chart-123",
            tax_category_id="tax-123",
            is_active=True,
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 6, 30)
        )

        with patch('models.tax_categorization.date') as mock_date:
            mock_date.today.return_value = date(2024, 7, 15)  # After expiration
            assert mapping.is_currently_active() is False

    def test_confidence_decimal_property(self):
        """Test confidence decimal property."""
        mapping = CategoryMapping(
            user_id="user-123",
            source_category_id="cat-123",
            chart_account_id="chart-123",
            tax_category_id="tax-123",
            confidence_score=Decimal("0.8750"),
            effective_date=date(2024, 1, 1)
        )

        assert mapping.confidence_decimal == Decimal("0.8750")

    def test_confidence_decimal_property_none(self):
        """Test confidence decimal property when None."""
        mapping = CategoryMapping(
            user_id="user-123",
            source_category_id="cat-123",
            chart_account_id="chart-123",
            tax_category_id="tax-123",
            confidence_score=None,
            effective_date=date(2024, 1, 1)
        )

        assert mapping.confidence_decimal == Decimal("1.0000")