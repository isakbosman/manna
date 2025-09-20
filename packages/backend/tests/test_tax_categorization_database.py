"""Database transaction and rollback tests for tax categorization system."""

import pytest
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import text

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


class TestDatabaseConstraints:
    """Test database constraints and integrity rules."""

    def test_chart_of_account_unique_code_constraint(self, db_session):
        """Test that account codes must be unique per user."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Create first account
        account1 = ChartOfAccount(
            user_id=user.id,
            account_code="5100",
            account_name="Office Expense",
            account_type="expense",
            normal_balance="debit"
        )
        db_session.add(account1)
        db_session.commit()

        # Try to create second account with same code for same user
        account2 = ChartOfAccount(
            user_id=user.id,
            account_code="5100",  # Duplicate code
            account_name="Another Office Expense",
            account_type="expense",
            normal_balance="debit"
        )
        db_session.add(account2)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_chart_of_account_different_users_same_code(self, db_session):
        """Test that different users can have same account codes."""
        # Create two users
        user1 = User(
            email="user1@example.com",
            username="user1",
            hashed_password="hashedpass",
            is_active=True
        )
        user2 = User(
            email="user2@example.com",
            username="user2",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.flush()

        # Create accounts with same code for different users
        account1 = ChartOfAccount(
            user_id=user1.id,
            account_code="5100",
            account_name="Office Expense - User 1",
            account_type="expense",
            normal_balance="debit"
        )
        account2 = ChartOfAccount(
            user_id=user2.id,
            account_code="5100",  # Same code, different user
            account_name="Office Expense - User 2",
            account_type="expense",
            normal_balance="debit"
        )

        db_session.add(account1)
        db_session.add(account2)
        db_session.commit()  # Should succeed

        # Verify both accounts exist
        accounts = db_session.query(ChartOfAccount).filter_by(account_code="5100").all()
        assert len(accounts) == 2

    def test_tax_category_unique_code_constraint(self, db_session):
        """Test that tax category codes must be unique globally."""
        category1 = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            tax_line="Line 18",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(category1)
        db_session.commit()

        # Try to create another category with same code
        category2 = TaxCategory(
            category_code="SCHED_C_18",  # Duplicate code
            category_name="Another Office expense",
            tax_form="Schedule C",
            tax_line="Line 18b",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(category2)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_business_expense_tracking_unique_transaction(self, db_session):
        """Test that business expense tracking is unique per transaction."""
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
            name="Test transaction"
        )
        db_session.add(transaction)
        db_session.flush()

        # Create first tracking record
        tracking1 = BusinessExpenseTracking(
            transaction_id=transaction.id,
            user_id=user.id,
            business_purpose="First purpose"
        )
        db_session.add(tracking1)
        db_session.commit()

        # Try to create second tracking record for same transaction
        tracking2 = BusinessExpenseTracking(
            transaction_id=transaction.id,  # Duplicate transaction_id
            user_id=user.id,
            business_purpose="Second purpose"
        )
        db_session.add(tracking2)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_category_mapping_unique_user_category_date(self, db_session):
        """Test that category mappings are unique per user/category/date."""
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

        # Create first mapping
        mapping1 = CategoryMapping(
            user_id=user.id,
            source_category_id=category.id,
            chart_account_id=chart_account.id,
            tax_category_id=tax_category.id,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(mapping1)
        db_session.commit()

        # Try to create second mapping with same user/category/date
        mapping2 = CategoryMapping(
            user_id=user.id,
            source_category_id=category.id,  # Same category
            chart_account_id=chart_account.id,
            tax_category_id=tax_category.id,
            effective_date=date(2024, 1, 1)  # Same date
        )
        db_session.add(mapping2)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_valid_account_type_constraint(self, db_session):
        """Test account type constraint validation."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Try to create account with invalid type
        account = ChartOfAccount(
            user_id=user.id,
            account_code="9999",
            account_name="Invalid Account",
            account_type="invalid_type",  # Not in allowed values
            normal_balance="debit"
        )
        db_session.add(account)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_valid_normal_balance_constraint(self, db_session):
        """Test normal balance constraint validation."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Try to create account with invalid normal balance
        account = ChartOfAccount(
            user_id=user.id,
            account_code="1100",
            account_name="Cash Account",
            account_type="asset",
            normal_balance="invalid_balance"  # Not 'debit' or 'credit'
        )
        db_session.add(account)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_business_percentage_range_constraint(self, db_session):
        """Test business percentage constraint (0-100)."""
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
            name="Test transaction"
        )
        db_session.add(transaction)
        db_session.flush()

        # Try to create tracking with invalid percentage > 100
        tracking = BusinessExpenseTracking(
            transaction_id=transaction.id,
            user_id=user.id,
            business_percentage=Decimal("150.00")  # Invalid: > 100
        )
        db_session.add(tracking)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

        # Try to create tracking with invalid percentage < 0
        tracking2 = BusinessExpenseTracking(
            transaction_id=transaction.id,
            user_id=user.id,
            business_percentage=Decimal("-10.00")  # Invalid: < 0
        )
        db_session.add(tracking2)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

    def test_foreign_key_constraints(self, db_session):
        """Test foreign key constraint violations."""
        # Try to create chart account with non-existent user
        account = ChartOfAccount(
            user_id="nonexistent-user-id",
            account_code="1100",
            account_name="Cash Account",
            account_type="asset",
            normal_balance="debit"
        )
        db_session.add(account)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()


class TestTransactionRollbacks:
    """Test transaction rollback scenarios."""

    def test_tax_categorization_service_rollback_on_error(self, db_session):
        """Test that TaxCategorizationService rolls back on errors."""
        service = TaxCategorizationService(db_session)

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
            name="Test transaction"
        )
        db_session.add(transaction)
        db_session.flush()

        tax_category = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.commit()

        # Mock commit to raise an error
        original_commit = db_session.commit
        db_session.commit = Mock(side_effect=SQLAlchemyError("Database error"))

        # Track rollback calls
        rollback_called = False
        original_rollback = db_session.rollback

        def track_rollback():
            nonlocal rollback_called
            rollback_called = True
            original_rollback()

        db_session.rollback = Mock(side_effect=track_rollback)

        with pytest.raises(SQLAlchemyError):
            service.categorize_for_tax(
                transaction_id=str(transaction.id),
                user_id=str(user.id),
                tax_category_id=str(tax_category.id)
            )

        # Verify rollback was called
        assert rollback_called
        db_session.rollback.assert_called_once()

        # Restore original methods
        db_session.commit = original_commit
        db_session.rollback = original_rollback

    def test_chart_of_accounts_service_rollback_on_create_error(self, db_session):
        """Test that ChartOfAccountsService rolls back on creation errors."""
        service = ChartOfAccountsService(db_session)

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Mock commit to raise an error after add
        original_commit = db_session.commit
        db_session.commit = Mock(side_effect=SQLAlchemyError("Database error"))

        rollback_called = False
        original_rollback = db_session.rollback

        def track_rollback():
            nonlocal rollback_called
            rollback_called = True
            original_rollback()

        db_session.rollback = Mock(side_effect=track_rollback)

        with pytest.raises(SQLAlchemyError):
            service.create_account(
                user_id=str(user.id),
                account_code="5100",
                account_name="Office Expense",
                account_type="expense",
                normal_balance="debit"
            )

        # Verify rollback was called
        assert rollback_called

        # Restore original methods
        db_session.commit = original_commit
        db_session.rollback = original_rollback

    def test_partial_transaction_rollback(self, db_session):
        """Test rollback of partially completed operations."""
        service = TaxCategorizationService(db_session)

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
            name="Test transaction"
        )
        db_session.add(transaction)
        db_session.flush()

        tax_category = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.commit()

        # Record initial transaction state
        initial_tax_category_id = transaction.tax_category_id
        initial_deductible_amount = transaction.deductible_amount

        # Mock the audit record creation to fail
        with patch.object(service, '_create_audit_record', side_effect=SQLAlchemyError("Audit error")):
            with pytest.raises(SQLAlchemyError):
                service.categorize_for_tax(
                    transaction_id=str(transaction.id),
                    user_id=str(user.id),
                    tax_category_id=str(tax_category.id)
                )

        # Refresh transaction from database
        db_session.refresh(transaction)

        # Verify transaction state was rolled back
        assert transaction.tax_category_id == initial_tax_category_id
        assert transaction.deductible_amount == initial_deductible_amount

        # Verify no business expense tracking was created
        tracking_count = db_session.query(BusinessExpenseTracking).filter_by(
            transaction_id=transaction.id
        ).count()
        assert tracking_count == 0

        # Verify no audit record was created
        audit_count = db_session.query(CategorizationAudit).filter_by(
            transaction_id=transaction.id
        ).count()
        assert audit_count == 0

    def test_bulk_operation_partial_rollback(self, db_session):
        """Test that bulk operations handle partial failures correctly."""
        service = TaxCategorizationService(db_session)

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
                name=f"Test transaction {i}"
            )
            db_session.add(transaction)
            db_session.flush()
            transactions.append(transaction)

        tax_category = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            is_active=True,
            effective_date=date(2024, 1, 1)
        )
        db_session.add(tax_category)
        db_session.commit()

        # Mock categorize_for_tax to fail on second transaction
        original_method = service.categorize_for_tax

        def mock_categorize_for_tax(transaction_id, **kwargs):
            if transaction_id == str(transactions[1].id):
                raise ValueError("Simulated error on second transaction")
            return original_method(transaction_id, **kwargs)

        service.categorize_for_tax = mock_categorize_for_tax

        result = service.bulk_categorize_for_tax(
            transaction_ids=[str(t.id) for t in transactions],
            user_id=str(user.id),
            tax_category_id=str(tax_category.id)
        )

        # Verify that 2 succeeded and 1 failed
        assert result["success_count"] == 2
        assert result["error_count"] == 1
        assert len(result["errors"]) == 1
        assert result["errors"][0]["transaction_id"] == str(transactions[1].id)

        # Verify successful transactions were processed
        assert len(result["results"]) == 2

    def test_cascade_delete_business_expense_tracking(self, db_session):
        """Test cascade delete of business expense tracking when transaction is deleted."""
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
            name="Test transaction"
        )
        db_session.add(transaction)
        db_session.flush()

        tracking = BusinessExpenseTracking(
            transaction_id=transaction.id,
            user_id=user.id,
            business_purpose="Test purpose"
        )
        db_session.add(tracking)

        audit = CategorizationAudit(
            transaction_id=transaction.id,
            user_id=user.id,
            action_type="categorize"
        )
        db_session.add(audit)
        db_session.commit()

        # Verify records exist
        assert db_session.query(BusinessExpenseTracking).filter_by(transaction_id=transaction.id).count() == 1
        assert db_session.query(CategorizationAudit).filter_by(transaction_id=transaction.id).count() == 1

        # Delete transaction
        db_session.delete(transaction)
        db_session.commit()

        # Verify cascade delete worked
        assert db_session.query(BusinessExpenseTracking).filter_by(transaction_id=transaction.id).count() == 0
        assert db_session.query(CategorizationAudit).filter_by(transaction_id=transaction.id).count() == 0

    def test_concurrent_modification_handling(self, db_session):
        """Test handling of concurrent modifications."""
        # This test simulates optimistic locking scenarios
        service = ChartOfAccountsService(db_session)

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
            normal_balance="debit"
        )
        db_session.add(account)
        db_session.commit()

        # Simulate concurrent update by modifying updated_at directly
        db_session.execute(
            text("UPDATE chart_of_accounts SET updated_at = NOW() WHERE id = :id"),
            {"id": account.id}
        )
        db_session.commit()

        # Try to update the account (would fail with proper optimistic locking)
        try:
            updated_account = service.update_account(
                account_id=str(account.id),
                user_id=str(user.id),
                account_name="Updated Office Expense"
            )
            # Should succeed without optimistic locking
            assert updated_account.account_name == "Updated Office Expense"
        except Exception as e:
            # If optimistic locking is implemented, this would raise an exception
            assert "concurrent modification" in str(e).lower()


class TestDatabasePerformance:
    """Test database performance and optimization."""

    def test_bulk_insert_performance(self, db_session, performance_timer):
        """Test performance of bulk operations."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Create many accounts using bulk operations
        accounts = []
        for i in range(100):
            account = ChartOfAccount(
                user_id=user.id,
                account_code=f"{5000 + i}",
                account_name=f"Test Account {i}",
                account_type="expense",
                normal_balance="debit"
            )
            accounts.append(account)

        performance_timer.start()
        db_session.bulk_save_objects(accounts)
        db_session.commit()
        performance_timer.stop()

        # Verify all accounts were created
        account_count = db_session.query(ChartOfAccount).filter_by(user_id=user.id).count()
        assert account_count == 100

        # Performance assertion
        assert performance_timer.elapsed_ms < 5000  # Should complete within 5 seconds

    def test_query_optimization_indexes(self, db_session):
        """Test that database indexes are working effectively."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Create many accounts
        accounts = []
        for i in range(50):
            account = ChartOfAccount(
                user_id=user.id,
                account_code=f"{5000 + i}",
                account_name=f"Test Account {i}",
                account_type="expense" if i % 2 == 0 else "asset",
                normal_balance="debit"
            )
            accounts.append(account)

        db_session.bulk_save_objects(accounts)
        db_session.commit()

        # Test indexed queries perform well
        # Query by user_id (should be indexed)
        user_accounts = db_session.query(ChartOfAccount).filter_by(
            user_id=user.id,
            is_active=True
        ).all()
        assert len(user_accounts) == 50

        # Query by account_type (should be indexed)
        expense_accounts = db_session.query(ChartOfAccount).filter_by(
            user_id=user.id,
            account_type="expense",
            is_active=True
        ).all()
        assert len(expense_accounts) == 25

        # Query by account_code (should be indexed)
        specific_account = db_session.query(ChartOfAccount).filter_by(
            account_code="5010"
        ).first()
        assert specific_account is not None

    def test_complex_query_performance(self, db_session):
        """Test performance of complex queries."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Create tax categories
        tax_categories = []
        for i in range(10):
            tax_category = TaxCategory(
                category_code=f"SCHED_C_{i}",
                category_name=f"Business Expense {i}",
                tax_form="Schedule C",
                is_active=True,
                effective_date=date(2024, 1, 1)
            )
            tax_categories.append(tax_category)

        db_session.bulk_save_objects(tax_categories)
        db_session.commit()

        # Create transactions with tax categorization
        transactions = []
        for i in range(100):
            transaction = Transaction(
                account_id="acc-123",
                plaid_transaction_id=f"txn-{i}",
                amount=Decimal(f"{50 + i}"),
                name=f"Transaction {i}",
                tax_category_id=tax_categories[i % 10].id,
                deductible_amount=Decimal(f"{40 + i}"),
                is_tax_deductible=True,
                tax_year=2024
            )
            transactions.append(transaction)

        db_session.bulk_save_objects(transactions)
        db_session.commit()

        # Complex query: tax summary with joins and aggregations
        from sqlalchemy import func
        query = db_session.query(
            TaxCategory.category_code,
            TaxCategory.category_name,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.deductible_amount).label('total_deductions')
        ).join(
            Transaction, Transaction.tax_category_id == TaxCategory.id
        ).filter(
            Transaction.tax_year == 2024,
            Transaction.is_tax_deductible == True
        ).group_by(
            TaxCategory.category_code,
            TaxCategory.category_name
        ).all()

        # Verify query results
        assert len(query) == 10  # Should have 10 tax categories
        for result in query:
            assert result.transaction_count == 10  # Each category has 10 transactions
            assert result.total_deductions > 0


class TestDataIntegrity:
    """Test data integrity and consistency."""

    def test_referential_integrity_enforcement(self, db_session):
        """Test that referential integrity is properly enforced."""
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

        transaction = Transaction(
            account_id="acc-123",
            plaid_transaction_id="txn-123",
            amount=Decimal("100.00"),
            name="Test transaction",
            tax_category_id=tax_category.id,
            chart_account_id=chart_account.id
        )
        db_session.add(transaction)
        db_session.commit()

        # Try to delete tax_category that is referenced by transaction
        db_session.delete(tax_category)

        # This should either:
        # 1. Raise an IntegrityError (if foreign key constraint exists)
        # 2. Set transaction.tax_category_id to NULL (if nullable with SET NULL)
        # 3. Succeed (if no constraint - which would be a design issue)

        try:
            db_session.commit()
            # If commit succeeds, check if reference was nullified
            db_session.refresh(transaction)
            assert transaction.tax_category_id is None, "Tax category reference should be nullified"
        except IntegrityError:
            # This is expected behavior with proper foreign key constraints
            db_session.rollback()

    def test_data_consistency_after_operations(self, db_session):
        """Test that data remains consistent after various operations."""
        service = TaxCategorizationService(db_session)

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
            name="Test transaction"
        )
        db_session.add(transaction)
        db_session.flush()

        tax_category = TaxCategory(
            category_code="SCHED_C_18",
            category_name="Office expense",
            tax_form="Schedule C",
            is_active=True,
            effective_date=date(2024, 1, 1),
            percentage_limit=Decimal("50.00")
        )
        db_session.add(tax_category)
        db_session.commit()

        # Perform categorization
        result = service.categorize_for_tax(
            transaction_id=str(transaction.id),
            user_id=str(user.id),
            tax_category_id=str(tax_category.id),
            business_percentage=Decimal("100.00")
        )

        # Verify consistency
        db_session.refresh(transaction)

        # Check that deductible amount respects percentage limit
        expected_deductible = transaction.amount * (Decimal("50.00") / Decimal("100"))
        assert transaction.deductible_amount == expected_deductible

        # Check that business expense tracking exists
        tracking = db_session.query(BusinessExpenseTracking).filter_by(
            transaction_id=transaction.id
        ).first()
        assert tracking is not None
        assert tracking.business_percentage == Decimal("100.00")

        # Check that audit record exists
        audit = db_session.query(CategorizationAudit).filter_by(
            transaction_id=transaction.id,
            action_type="tax_categorize"
        ).first()
        assert audit is not None

    def test_decimal_precision_consistency(self, db_session):
        """Test that decimal values maintain proper precision."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Test with precise decimal values
        account = ChartOfAccount(
            user_id=user.id,
            account_code="1100",
            account_name="Cash",
            account_type="asset",
            normal_balance="debit",
            current_balance=Decimal("1234.56789")  # More precision than expected
        )
        db_session.add(account)
        db_session.commit()

        # Verify precision is maintained according to schema
        db_session.refresh(account)
        # Should be rounded to 2 decimal places (15,2 precision)
        assert account.current_balance == Decimal("1234.57")

        # Test business percentage precision
        transaction = Transaction(
            account_id="acc-123",
            plaid_transaction_id="txn-123",
            amount=Decimal("100.00"),
            name="Test transaction"
        )
        db_session.add(transaction)
        db_session.flush()

        tracking = BusinessExpenseTracking(
            transaction_id=transaction.id,
            user_id=user.id,
            business_percentage=Decimal("75.555")  # More precision than expected
        )
        db_session.add(tracking)
        db_session.commit()

        db_session.refresh(tracking)
        # Should be rounded to 2 decimal places (5,2 precision)
        assert tracking.business_percentage == Decimal("75.56")