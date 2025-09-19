"""Tests for tax categorization system."""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from ..models.tax_categorization import (
    TaxCategory, ChartOfAccount, BusinessExpenseTracking,
    CategoryMapping, CategorizationAudit
)
from ..models.transaction import Transaction
from ..models.user import User
from ..models.category import Category
from ..src.services.tax_categorization_service import TaxCategorizationService
from ..src.services.chart_of_accounts_service import ChartOfAccountsService


class TestTaxCategorizationService:
    """Test tax categorization service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = Mock(spec=Session)
        self.service = TaxCategorizationService(self.session)

    def test_auto_detect_tax_category_with_mapping(self):
        """Test auto-detection using existing category mapping."""
        # Create mock objects
        transaction = Mock(spec=Transaction)
        transaction.category_id = "category-123"
        transaction.name = "Office supplies"
        transaction.merchant_name = "Staples"
        transaction.description = "Business supplies"

        mapping = Mock(spec=CategoryMapping)
        mapping.tax_category_id = "tax-cat-123"
        mapping.chart_account_id = "chart-acc-123"
        mapping.confidence_score = Decimal("0.95")

        # Mock session query
        self.session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mapping

        result = self.service.auto_detect_tax_category(transaction, "user-123")

        assert result["tax_category_id"] == "tax-cat-123"
        assert result["chart_account_id"] == "chart-acc-123"
        assert result["confidence"] == 0.95
        assert result["source"] == "category_mapping"

    def test_auto_detect_tax_category_keyword_matching(self):
        """Test auto-detection using keyword matching."""
        # Create mock objects
        transaction = Mock(spec=Transaction)
        transaction.category_id = None
        transaction.name = "Gas station fuel"
        transaction.merchant_name = "Shell"
        transaction.description = "Vehicle fuel"

        tax_category = Mock(spec=TaxCategory)
        tax_category.id = "tax-cat-vehicle"
        tax_category.category_name = "Car and truck expenses"
        tax_category.keywords = ["gas", "fuel", "vehicle", "car"]
        tax_category.exclusions = []

        chart_account = Mock(spec=ChartOfAccount)
        chart_account.id = "chart-acc-vehicle"

        # Mock session queries
        self.session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        self.session.query.return_value.filter.return_value.all.return_value = [tax_category]
        self.session.query.return_value.filter.return_value.first.return_value = chart_account

        with patch.object(self.service, '_calculate_keyword_match_score', return_value=0.5):
            result = self.service.auto_detect_tax_category(transaction, "user-123")

        assert result["tax_category_id"] == "tax-cat-vehicle"
        assert result["chart_account_id"] == "chart-acc-vehicle"
        assert result["confidence"] == 0.5
        assert result["source"] == "keyword_matching"

    def test_calculate_keyword_match_score(self):
        """Test keyword match score calculation."""
        tax_category = Mock(spec=TaxCategory)
        tax_category.keywords = ["office", "supplies", "paper", "pens"]
        tax_category.exclusions = ["personal"]

        # Test full match
        score = self.service._calculate_keyword_match_score("office supplies paper", tax_category)
        assert score == 0.75  # 3 out of 4 keywords matched

        # Test exclusion
        tax_category.exclusions = ["personal"]
        score = self.service._calculate_keyword_match_score("office supplies personal", tax_category)
        assert score == 0.0  # Excluded due to "personal"

    def test_categorize_for_tax_success(self):
        """Test successful tax categorization."""
        # Create mock objects
        transaction = Mock(spec=Transaction)
        transaction.id = "trans-123"
        transaction.amount_decimal = Decimal("100.00")
        transaction.tax_category_id = None
        transaction.chart_account_id = None

        tax_category = Mock(spec=TaxCategory)
        tax_category.id = "tax-cat-123"
        tax_category.category_name = "Office expense"
        tax_category.tax_form = "Schedule C"
        tax_category.tax_line = "Line 18"
        tax_category.is_currently_effective.return_value = True
        tax_category.calculate_deductible_amount.return_value = Decimal("100.00")

        chart_account = Mock(spec=ChartOfAccount)
        chart_account.id = "chart-acc-123"
        chart_account.account_name = "Office Expense"

        # Mock session queries
        self.session.query.return_value.filter_by.return_value.first.side_effect = [
            transaction,  # Transaction query
            tax_category,  # Tax category query
            chart_account  # Chart account query
        ]

        with patch.object(self.service, '_requires_substantiation', return_value=True), \
             patch.object(self.service, '_create_or_update_business_tracking'), \
             patch.object(self.service, '_create_audit_record'):

            result = self.service.categorize_for_tax(
                transaction_id="trans-123",
                user_id="user-123",
                tax_category_id="tax-cat-123",
                chart_account_id="chart-acc-123"
            )

        assert result["success"] is True
        assert result["transaction_id"] == "trans-123"
        assert result["tax_category"] == "Office expense"
        assert result["chart_account"] == "Office Expense"
        assert result["deductible_amount"] == 100.00
        assert result["requires_substantiation"] is True

    def test_get_tax_summary(self):
        """Test tax summary generation."""
        # Create mock transactions
        transaction1 = Mock(spec=Transaction)
        transaction1.deductible_amount = Decimal("100.00")
        transaction1.requires_substantiation = True
        transaction1.substantiation_complete = False
        transaction1.tax_category = Mock()
        transaction1.tax_category.category_code = "SCHED_C_18"
        transaction1.tax_category.category_name = "Office expense"
        transaction1.tax_category.tax_form = "Schedule C"
        transaction1.tax_category.tax_line = "Line 18"

        transaction2 = Mock(spec=Transaction)
        transaction2.deductible_amount = Decimal("50.00")
        transaction2.requires_substantiation = False
        transaction2.substantiation_complete = True
        transaction2.tax_category = Mock()
        transaction2.tax_category.category_code = "SCHED_C_18"
        transaction2.tax_category.category_name = "Office expense"
        transaction2.tax_category.tax_form = "Schedule C"
        transaction2.tax_category.tax_line = "Line 18"

        # Mock session query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = [transaction1, transaction2]
        self.session.query.return_value = mock_query

        result = self.service.get_tax_summary("user-123", 2024)

        assert result["tax_year"] == 2024
        assert result["total_deductions"] == 150.00
        assert "SCHED_C_18" in result["categories"]
        assert result["categories"]["SCHED_C_18"]["total_amount"] == 150.00
        assert result["categories"]["SCHED_C_18"]["transaction_count"] == 2
        assert result["categories"]["SCHED_C_18"]["requires_substantiation"] == 1

    def test_requires_substantiation(self):
        """Test substantiation requirement logic."""
        transaction = Mock(spec=Transaction)
        transaction.amount_decimal = Decimal("100.00")

        # Test amount threshold
        assert self.service._requires_substantiation(transaction, None) is True

        # Test documentation required
        tax_category = Mock(spec=TaxCategory)
        tax_category.documentation_required = True
        assert self.service._requires_substantiation(transaction, tax_category) is True

        # Test specific categories
        tax_category.documentation_required = False
        tax_category.category_name = "Travel"
        assert self.service._requires_substantiation(transaction, tax_category) is True

        # Test normal case
        transaction.amount_decimal = Decimal("50.00")
        tax_category.category_name = "Office expense"
        assert self.service._requires_substantiation(transaction, tax_category) is False


class TestChartOfAccountsService:
    """Test chart of accounts service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = Mock(spec=Session)
        self.service = ChartOfAccountsService(self.session)

    def test_create_account_success(self):
        """Test successful account creation."""
        # Mock existing account check
        self.session.query.return_value.filter_by.return_value.first.return_value = None

        account = self.service.create_account(
            user_id="user-123",
            account_code="5100",
            account_name="Advertising Expense",
            account_type="expense",
            normal_balance="debit",
            description="Marketing and advertising costs"
        )

        assert account.account_code == "5100"
        assert account.account_name == "Advertising Expense"
        assert account.account_type == "expense"
        assert account.normal_balance == "debit"
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()

    def test_create_account_duplicate_code(self):
        """Test account creation with duplicate code."""
        # Mock existing account
        existing_account = Mock(spec=ChartOfAccount)
        self.session.query.return_value.filter_by.return_value.first.return_value = existing_account

        with pytest.raises(ValueError, match="Account code .* already exists"):
            self.service.create_account(
                user_id="user-123",
                account_code="5100",
                account_name="Advertising Expense",
                account_type="expense",
                normal_balance="debit"
            )

    def test_get_account_balance(self):
        """Test account balance calculation."""
        account = Mock(spec=ChartOfAccount)
        account.id = "acc-123"
        account.normal_balance = "debit"

        # Mock account query
        self.session.query.return_value.filter_by.return_value.first.return_value = account

        # Mock transaction sum queries
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.scalar.side_effect = [Decimal("500.00"), Decimal("200.00")]  # debits, credits
        self.session.query.return_value.filter.return_value = mock_query

        balance = self.service.get_account_balance("acc-123", "user-123")

        assert balance == Decimal("300.00")  # 500 - 200 for debit account
        assert account.current_balance == Decimal("300.00")

    def test_get_trial_balance(self):
        """Test trial balance generation."""
        # Create mock accounts
        asset_account = Mock(spec=ChartOfAccount)
        asset_account.id = "acc-1"
        asset_account.account_code = "1100"
        asset_account.account_name = "Checking Account"
        asset_account.account_type = "asset"
        asset_account.normal_balance = "debit"

        liability_account = Mock(spec=ChartOfAccount)
        liability_account.id = "acc-2"
        liability_account.account_code = "2000"
        liability_account.account_name = "Accounts Payable"
        liability_account.account_type = "liability"
        liability_account.normal_balance = "credit"

        # Mock queries
        self.session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [
            asset_account, liability_account
        ]

        with patch.object(self.service, 'get_account_balance') as mock_balance:
            mock_balance.side_effect = [Decimal("1000.00"), Decimal("500.00")]

            result = self.service.get_trial_balance("user-123")

        assert len(result["accounts"]) == 2
        assert result["total_debits"] == 1000.00
        assert result["total_credits"] == 500.00
        assert result["is_balanced"] is False  # 1000 != 500

    def test_delete_account_with_transactions(self):
        """Test soft delete of account with transactions."""
        account = Mock(spec=ChartOfAccount)
        account.is_system_account = False

        # Mock account query
        self.session.query.return_value.filter_by.return_value.first.return_value = account

        # Mock transaction count
        self.session.query.return_value.filter_by.return_value.count.return_value = 5

        result = self.service.delete_account("acc-123", "user-123")

        assert result is True
        assert account.is_active is False
        self.session.commit.assert_called_once()

    def test_delete_system_account_raises_error(self):
        """Test that deleting system account raises error."""
        account = Mock(spec=ChartOfAccount)
        account.is_system_account = True

        self.session.query.return_value.filter_by.return_value.first.return_value = account

        with pytest.raises(ValueError, match="Cannot delete system accounts"):
            self.service.delete_account("acc-123", "user-123")


class TestTaxCategoryModel:
    """Test tax category model methods."""

    def test_is_currently_effective(self):
        """Test current effectiveness check."""
        tax_category = TaxCategory(
            category_code="TEST",
            category_name="Test Category",
            tax_form="Schedule C",
            is_active=True,
            effective_date=date(2024, 1, 1),
            expiration_date=date(2024, 12, 31)
        )

        # Mock today's date
        with patch('builtins.date') as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)
            assert tax_category.is_currently_effective() is True

            mock_date.today.return_value = date(2025, 1, 1)
            assert tax_category.is_currently_effective() is False

    def test_calculate_deductible_amount(self):
        """Test deductible amount calculation."""
        tax_category = TaxCategory(
            category_code="MEALS",
            category_name="Meals",
            tax_form="Schedule C",
            percentage_limit=Decimal("50.00"),
            effective_date=date(2024, 1, 1)
        )

        # Test percentage limit
        amount = Decimal("100.00")
        deductible = tax_category.calculate_deductible_amount(amount)
        assert deductible == Decimal("50.00")

        # Test without limits
        tax_category.percentage_limit = None
        deductible = tax_category.calculate_deductible_amount(amount)
        assert deductible == Decimal("100.00")


class TestBusinessExpenseTracking:
    """Test business expense tracking model."""

    def test_calculate_business_amount(self):
        """Test business amount calculation."""
        tracking = BusinessExpenseTracking(
            transaction_id="trans-123",
            user_id="user-123",
            business_percentage=Decimal("75.00")
        )

        business_amount = tracking.calculate_business_amount(Decimal("100.00"))
        assert business_amount == Decimal("75.00")

    def test_is_substantiation_complete(self):
        """Test substantiation completeness check."""
        tracking = BusinessExpenseTracking(
            transaction_id="trans-123",
            user_id="user-123",
            business_purpose="Client meeting",
            receipt_required=True,
            receipt_attached=False
        )

        # Missing receipt
        assert tracking.is_substantiation_complete() is False

        # Complete substantiation
        tracking.receipt_attached = True
        assert tracking.is_substantiation_complete() is True

        # Missing business purpose
        tracking.business_purpose = None
        assert tracking.is_substantiation_complete() is False