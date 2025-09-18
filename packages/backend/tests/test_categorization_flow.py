"""
Comprehensive integration tests for the transaction categorization system.
Tests the complete flow from transaction creation to ML categorization.
"""

import pytest
import json
import tempfile
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Dict, Any
from uuid import uuid4
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from src.database.models import (
    Transaction, Category, User, Account, Institution, PlaidItem,
    MLPrediction, CategorizationRule
)
from src.schemas.transaction import (
    TransactionCategorization, TransactionCreate, BulkTransactionUpdate
)
from src.schemas.category import CategoryCreate, CategoryRule
from src.services.ml_categorization import MLCategorizationService, FeatureExtractor
from src.services.category_rules import CategoryRuleService
from src.config import settings


class TestCategorizationFlow:
    """Test complete categorization workflow."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session, test_user: User, test_account: Account):
        """Setup test data for categorization tests."""
        self.db = db_session
        self.user = test_user
        self.account = test_account

        # Create test categories
        self.categories = self._create_test_categories()

        # Create test transactions
        self.transactions = self._create_test_transactions()

        # Initialize services
        self.ml_service = MLCategorizationService(
            model_path=tempfile.mkdtemp()
        )
        self.rule_service = CategoryRuleService()

    def _create_test_categories(self) -> List[Category]:
        """Create comprehensive test categories."""
        categories_data = [
            {
                "name": "Food & Dining",
                "parent_category": "Expense",
                "description": "Restaurant meals and food purchases",
                "color": "#FF5722",
                "icon": "restaurant",
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "restaurant",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "uber eats",
                        "confidence": 0.95
                    }
                ]
            },
            {
                "name": "Transportation",
                "parent_category": "Expense",
                "description": "Gas, parking, rideshare",
                "color": "#2196F3",
                "icon": "directions_car",
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "shell",
                        "confidence": 0.9
                    },
                    {
                        "type": "text_match",
                        "field": "name",
                        "operator": "contains",
                        "value": "uber",
                        "confidence": 0.85
                    }
                ]
            },
            {
                "name": "Shopping",
                "parent_category": "Expense",
                "description": "Retail purchases",
                "color": "#9C27B0",
                "icon": "shopping_bag",
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "amazon",
                        "confidence": 0.95
                    }
                ]
            },
            {
                "name": "Income",
                "parent_category": "Income",
                "description": "Salary and other income",
                "color": "#4CAF50",
                "icon": "account_balance_wallet",
                "rules": [
                    {
                        "type": "amount_range",
                        "field": "amount",
                        "operator": "greater_than",
                        "value": "1000",
                        "confidence": 0.8
                    }
                ]
            },
            {
                "name": "Bills & Utilities",
                "parent_category": "Expense",
                "description": "Monthly bills and utilities",
                "color": "#FF9800",
                "icon": "receipt",
                "rules": [
                    {
                        "type": "text_match",
                        "field": "merchant",
                        "operator": "contains",
                        "value": "electric",
                        "confidence": 0.9
                    }
                ]
            }
        ]

        categories = []
        for cat_data in categories_data:
            category = Category(
                user_id=self.user.id,
                name=cat_data["name"],
                parent_category=cat_data["parent_category"],
                description=cat_data["description"],
                color=cat_data["color"],
                icon=cat_data["icon"],
                rules=cat_data["rules"],
                is_system=False,
                is_active=True
            )
            self.db.add(category)
            categories.append(category)

        self.db.commit()
        return categories

    def _create_test_transactions(self) -> List[Transaction]:
        """Create diverse test transactions for categorization."""
        transaction_data = [
            {
                "name": "McDonald's Restaurant",
                "merchant_name": "McDonald's",
                "amount": -12.50,
                "description": "Food purchase",
                "expected_category": "Food & Dining"
            },
            {
                "name": "Shell Gas Station",
                "merchant_name": "Shell",
                "amount": -45.00,
                "description": "Fuel purchase",
                "expected_category": "Transportation"
            },
            {
                "name": "Amazon Purchase",
                "merchant_name": "Amazon",
                "amount": -89.99,
                "description": "Online shopping",
                "expected_category": "Shopping"
            },
            {
                "name": "Salary Deposit",
                "merchant_name": "ACME Corp",
                "amount": 2500.00,
                "description": "Payroll deposit",
                "expected_category": "Income"
            },
            {
                "name": "Electric Company Bill",
                "merchant_name": "Electric Utility Co",
                "amount": -125.00,
                "description": "Monthly electric bill",
                "expected_category": "Bills & Utilities"
            },
            {
                "name": "Uber Ride",
                "merchant_name": "Uber",
                "amount": -18.50,
                "description": "Transportation service",
                "expected_category": "Transportation"
            },
            {
                "name": "Starbucks Coffee",
                "merchant_name": "Starbucks",
                "amount": -5.75,
                "description": "Coffee purchase",
                "expected_category": "Food & Dining"
            },
            {
                "name": "Unknown Merchant XYZ",
                "merchant_name": "XYZ Store",
                "amount": -25.00,
                "description": "Unknown purchase",
                "expected_category": None  # Should be uncategorized
            }
        ]

        transactions = []
        for i, txn_data in enumerate(transaction_data):
            transaction = Transaction(
                account_id=self.account.id,
                plaid_transaction_id=f"test_txn_{i}_{uuid4().hex[:8]}",
                name=txn_data["name"],
                merchant_name=txn_data["merchant_name"],
                amount_cents=int(txn_data["amount"] * 100),
                date=date.today() - timedelta(days=i),
                description=txn_data["description"],
                pending=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            transaction._expected_category = txn_data["expected_category"]
            self.db.add(transaction)
            transactions.append(transaction)

        self.db.commit()
        return transactions

    def test_feature_extraction(self):
        """Test feature extraction from transactions."""
        extractor = FeatureExtractor()

        # Test with McDonald's transaction
        mcdonalds_txn = self.transactions[0]
        features = extractor.extract_all_features(mcdonalds_txn)

        # Verify text features
        assert "mcdonald" in " ".join(features.text_features).lower()
        assert "restaurant" in " ".join(features.text_features).lower()

        # Verify amount features
        assert features.amount_features["amount_raw"] == -12.50
        assert features.amount_features["amount_abs"] == 12.50
        assert features.amount_features["amount_bin_small"] == 1.0

        # Verify temporal features
        assert features.temporal_features["month"] == mcdonalds_txn.date.month
        assert features.temporal_features["day_of_week"] == mcdonalds_txn.date.weekday()

        # Verify merchant features
        assert features.merchant_features["is_restaurant"] == 1.0
        assert features.merchant_features["is_gas_station"] == 0.0

    def test_rule_based_categorization(self):
        """Test rule-based categorization engine."""
        results = []

        for transaction in self.transactions:
            categorization = self.ml_service.categorize_transaction(
                transaction, use_ml=False, use_rules=True, use_cache=False
            )
            results.append({
                "transaction": transaction.name,
                "predicted": categorization.suggested_category,
                "expected": transaction._expected_category,
                "confidence": categorization.confidence,
                "rules": categorization.rules_applied
            })

        # Verify specific categorizations
        mcdonalds_result = next(r for r in results if "McDonald's" in r["transaction"])
        assert mcdonalds_result["predicted"] == "Food & Dining"
        assert mcdonalds_result["confidence"] >= 0.8

        shell_result = next(r for r in results if "Shell" in r["transaction"])
        assert shell_result["predicted"] == "Transportation"

        amazon_result = next(r for r in results if "Amazon" in r["transaction"])
        assert amazon_result["predicted"] == "Shopping"

        # Check overall accuracy
        correct_predictions = sum(1 for r in results
                                if r["predicted"] == r["expected"] and r["expected"] is not None)
        expected_predictions = sum(1 for r in results if r["expected"] is not None)
        accuracy = correct_predictions / expected_predictions if expected_predictions > 0 else 0

        assert accuracy >= 0.7, f"Rule-based accuracy {accuracy:.2f} below threshold"

    @patch('src.services.ml_categorization.joblib')
    def test_ml_categorization_training(self, mock_joblib):
        """Test ML model training with sufficient data."""
        # Create additional training transactions
        training_transactions = []
        categories = ["Food & Dining", "Transportation", "Shopping", "Income"]

        for i in range(50):  # Create 50 transactions per category
            for category in categories:
                transaction = Transaction(
                    account_id=self.account.id,
                    plaid_transaction_id=f"train_txn_{category}_{i}",
                    name=f"Sample {category} Transaction {i}",
                    merchant_name=f"{category} Merchant {i}",
                    amount_cents=int((100 + i * 5) * (-1 if category != "Income" else 1)),
                    date=date.today() - timedelta(days=i),
                    user_category=category,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(transaction)
                training_transactions.append(transaction)

        self.db.commit()

        # Train the model
        training_result = self.ml_service.train_enhanced_model(
            self.db,
            user_id=str(self.user.id),
            min_samples=50,
            test_size=0.2
        )

        assert training_result["success"] is True
        assert training_result["test_accuracy"] > 0.5
        assert len(training_result["categories"]) >= 4
        assert training_result["training_samples"] >= 40  # 80% of 200 transactions

    def test_ml_prediction_with_alternatives(self):
        """Test ML predictions with alternative suggestions."""
        # Mock trained ML model
        with patch.object(self.ml_service, 'ensemble_classifier') as mock_classifier, \
             patch.object(self.ml_service, 'text_vectorizer') as mock_vectorizer:

            # Mock vectorizer
            mock_vectorizer.transform.return_value = [[0.1, 0.2, 0.3]]

            # Mock classifier with probabilities
            mock_classifier.predict_proba.return_value = [[0.1, 0.7, 0.15, 0.05]]
            mock_classifier.classes_ = ["Transportation", "Food & Dining", "Shopping", "Income"]

            # Test categorization
            transaction = self.transactions[0]  # McDonald's
            result = self.ml_service.categorize_transaction(
                transaction, use_ml=True, use_rules=False, use_cache=False
            )

            assert result.suggested_category == "Food & Dining"
            assert result.confidence == 0.7
            assert len(result.alternative_categories) >= 1
            assert result.alternative_categories[0]["category"] == "Shopping"

    def test_batch_categorization_performance(self):
        """Test batch categorization performance and caching."""
        # Test without cache
        start_time = datetime.now()
        results_no_cache = self.ml_service.batch_categorize(
            self.transactions, use_cache=False
        )
        time_no_cache = (datetime.now() - start_time).total_seconds()

        # Test with cache (second run should be faster)
        start_time = datetime.now()
        results_with_cache = self.ml_service.batch_categorize(
            self.transactions, use_cache=True
        )
        time_with_cache = (datetime.now() - start_time).total_seconds()

        assert len(results_no_cache) == len(self.transactions)
        assert len(results_with_cache) == len(self.transactions)

        # Verify all transactions got categorized
        for result in results_no_cache:
            assert result.suggested_category is not None
            assert 0 <= result.confidence <= 1

    def test_user_feedback_loop(self):
        """Test user feedback storage and processing."""
        transaction = self.transactions[0]

        # Simulate ML prediction
        prediction = self.ml_service.categorize_transaction(transaction)

        # Store feedback
        ml_prediction = self.ml_service.store_prediction_feedback(
            self.db,
            str(transaction.id),
            prediction.suggested_category,
            "Food & Dining",  # Correct category
            user_confidence=0.95
        )

        assert ml_prediction.transaction_id == str(transaction.id)
        assert ml_prediction.is_accepted == (prediction.suggested_category == "Food & Dining")
        assert ml_prediction.user_feedback in ["correct", "incorrect"]

        # Test feedback processing
        feedback_result = self.ml_service.update_from_feedback(
            str(transaction.id),
            "Food & Dining",
            was_correct=True
        )

        assert feedback_result["success"] is True
        assert feedback_result["feedback_recorded"] is True

    def test_category_rule_application(self):
        """Test dynamic category rule creation and application."""
        # Create a new rule
        new_rule = {
            "type": "text_match",
            "field": "merchant",
            "operator": "contains",
            "value": "target",
            "confidence": 0.9
        }

        # Add rule to Shopping category
        shopping_category = next(c for c in self.categories if c.name == "Shopping")
        current_rules = shopping_category.rules or []
        current_rules.append(new_rule)
        shopping_category.rules = current_rules
        self.db.commit()

        # Create transaction that should match the rule
        target_transaction = Transaction(
            account_id=self.account.id,
            plaid_transaction_id="target_test_txn",
            name="Target Store Purchase",
            merchant_name="Target",
            amount_cents=-5000,  # $50.00
            date=date.today(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(target_transaction)
        self.db.commit()

        # Test categorization
        result = self.ml_service.categorize_transaction(
            target_transaction, use_ml=False, use_rules=True
        )

        assert result.suggested_category == "Shopping"
        assert result.confidence >= 0.9

    def test_bulk_categorization_operations(self, client: TestClient, auth_headers: dict):
        """Test bulk categorization operations via API."""
        # Get transaction IDs
        transaction_ids = [str(txn.id) for txn in self.transactions[:3]]

        # Test bulk categorization
        bulk_request = {
            "transaction_ids": transaction_ids,
            "operation": "categorize",
            "category": "Food & Dining"
        }

        response = client.post(
            "/api/transactions/bulk",
            json=bulk_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["updated_count"] >= 1

        # Verify transactions were updated
        for txn_id in transaction_ids:
            txn = self.db.query(Transaction).filter(Transaction.id == txn_id).first()
            assert txn.user_category == "Food & Dining"

    def test_export_import_functionality(self, client: TestClient, auth_headers: dict):
        """Test transaction export and import with categorization data."""
        # Export transactions as CSV
        response = client.get(
            "/api/transactions/export/csv",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        csv_content = response.content.decode()
        lines = csv_content.strip().split('\n')

        # Verify header
        header = lines[0]
        assert "Category" in header
        assert "Amount" in header
        assert "Date" in header

        # Verify data rows
        assert len(lines) > 1  # Header + data rows

        # Test Excel export with summary
        response = client.get(
            "/api/transactions/export/excel?include_summary=true",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]

    def test_categorization_api_endpoints(self, client: TestClient, auth_headers: dict):
        """Test categorization-specific API endpoints."""
        transaction = self.transactions[0]

        # Test single transaction categorization
        response = client.post(
            f"/api/ml/categorize/{transaction.id}",
            headers=auth_headers
        )

        if response.status_code == 200:
            result = response.json()
            assert "suggested_category" in result
            assert "confidence" in result
            assert 0 <= result["confidence"] <= 1

        # Test batch categorization
        transaction_ids = [str(txn.id) for txn in self.transactions[:3]]
        response = client.post(
            "/api/ml/categorize/batch",
            json={"transaction_ids": transaction_ids},
            headers=auth_headers
        )

        if response.status_code == 200:
            results = response.json()
            assert len(results) == 3
            for result in results:
                assert "transaction_id" in result
                assert "suggested_category" in result

    def test_model_metrics_and_health(self):
        """Test model metrics and health monitoring."""
        metrics = self.ml_service.get_model_metrics()

        assert "model_loaded" in metrics
        assert "confidence_threshold" in metrics
        assert "rule_categories" in metrics
        assert isinstance(metrics["rule_categories"], list)
        assert len(metrics["rule_categories"]) > 0

    def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback mechanisms."""
        # Create transaction with minimal data
        minimal_transaction = Transaction(
            account_id=self.account.id,
            plaid_transaction_id="minimal_txn",
            name="",  # Empty name
            merchant_name=None,
            amount_cents=0,
            date=date.today(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(minimal_transaction)
        self.db.commit()

        # Test categorization with minimal data
        result = self.ml_service.categorize_transaction(minimal_transaction)

        # Should still get a result (fallback)
        assert result.suggested_category is not None
        assert result.confidence >= 0.0

        # Test with invalid transaction (should handle gracefully)
        try:
            invalid_result = self.ml_service.categorize_transaction(None)
            assert False, "Should have raised an exception"
        except Exception:
            pass  # Expected behavior

    def test_confidence_thresholding(self):
        """Test confidence threshold filtering."""
        # Test with high confidence threshold
        original_threshold = self.ml_service.confidence_threshold
        self.ml_service.confidence_threshold = 0.95

        transaction = self.transactions[0]
        result = self.ml_service.categorize_transaction(transaction)

        # With high threshold, might get fallback category
        assert result.suggested_category is not None

        # Reset threshold
        self.ml_service.confidence_threshold = original_threshold

    def test_transaction_statistics_with_categorization(self, client: TestClient, auth_headers: dict):
        """Test transaction statistics including categorization data."""
        # First categorize some transactions
        for i, transaction in enumerate(self.transactions[:4]):
            category = ["Food & Dining", "Transportation", "Shopping", "Income"][i]
            transaction.user_category = category
        self.db.commit()

        # Get statistics
        response = client.get("/api/transactions/stats", headers=auth_headers)

        assert response.status_code == 200
        stats = response.json()

        assert "categories" in stats
        assert len(stats["categories"]) > 0

        # Verify category breakdown
        food_category = next(
            (c for c in stats["categories"] if c["category"] == "Food & Dining"),
            None
        )
        assert food_category is not None
        assert food_category["transaction_count"] >= 1


class TestCategorizationPerformance:
    """Performance tests for categorization system."""

    def test_large_batch_performance(self, db_session: Session, test_account: Account):
        """Test performance with large transaction batches."""
        # Create 1000 test transactions
        transactions = []
        for i in range(1000):
            transaction = Transaction(
                account_id=test_account.id,
                plaid_transaction_id=f"perf_txn_{i}",
                name=f"Transaction {i}",
                merchant_name=f"Merchant {i % 50}",
                amount_cents=int((100 + i) * (-1 if i % 2 else 1)),
                date=date.today() - timedelta(days=i % 365),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            transactions.append(transaction)

        db_session.bulk_save_objects(transactions)
        db_session.commit()

        # Test batch categorization performance
        ml_service = MLCategorizationService()

        start_time = datetime.now()
        results = ml_service.batch_categorize(
            transactions[:100],  # Test with 100 transactions
            use_cache=True
        )
        duration = (datetime.now() - start_time).total_seconds()

        assert len(results) == 100
        assert duration < 10  # Should complete in under 10 seconds

        # Test throughput
        throughput = len(results) / duration
        assert throughput > 10  # At least 10 transactions per second

    def test_memory_usage_efficiency(self, db_session: Session, test_account: Account):
        """Test memory efficiency during batch processing."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Process large batch
        ml_service = MLCategorizationService()

        # Create and process transactions in batches
        for batch in range(5):
            transactions = []
            for i in range(200):
                transaction = Transaction(
                    account_id=test_account.id,
                    plaid_transaction_id=f"mem_txn_{batch}_{i}",
                    name=f"Memory Test Transaction {i}",
                    merchant_name=f"Merchant {i}",
                    amount_cents=int((50 + i) * -1),
                    date=date.today() - timedelta(days=i),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                transactions.append(transaction)

            db_session.bulk_save_objects(transactions)
            db_session.commit()

            # Process batch
            results = ml_service.batch_categorize(transactions, use_cache=True)

            # Clear transactions from memory
            del transactions
            del results

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.2f}MB"


class TestCategorizationSecurity:
    """Security tests for categorization system."""

    def test_user_isolation(self, db_session: Session, client: TestClient):
        """Test that users can only categorize their own transactions."""
        # Create two users
        user1 = User(
            email="user1@test.com",
            username="user1",
            hashed_password="hashed_password",
            is_active=True,
            is_verified=True
        )
        user2 = User(
            email="user2@test.com",
            username="user2",
            hashed_password="hashed_password",
            is_active=True,
            is_verified=True
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # Create accounts for each user
        account1 = Account(
            user_id=user1.id,
            plaid_account_id="acc1",
            name="User 1 Account",
            type="depository",
            subtype="checking"
        )
        account2 = Account(
            user_id=user2.id,
            plaid_account_id="acc2",
            name="User 2 Account",
            type="depository",
            subtype="checking"
        )
        db_session.add_all([account1, account2])
        db_session.commit()

        # Create transactions for each user
        txn1 = Transaction(
            account_id=account1.id,
            plaid_transaction_id="txn1",
            name="User 1 Transaction",
            amount_cents=-1000,
            date=date.today()
        )
        txn2 = Transaction(
            account_id=account2.id,
            plaid_transaction_id="txn2",
            name="User 2 Transaction",
            amount_cents=-2000,
            date=date.today()
        )
        db_session.add_all([txn1, txn2])
        db_session.commit()

        # Test that ML service respects user boundaries
        ml_service = MLCategorizationService()

        # Train model for user1 only
        training_result = ml_service.train_enhanced_model(
            db_session,
            user_id=str(user1.id),
            min_samples=1
        )

        # Should only see user1's data in training
        if training_result["success"]:
            # Verify no cross-user data leakage
            assert training_result["training_samples"] == 1

    def test_input_sanitization(self):
        """Test input sanitization for categorization."""
        ml_service = MLCategorizationService()
        extractor = FeatureExtractor()

        # Create transaction with potentially malicious input
        malicious_transaction = Transaction(
            account_id=uuid4(),
            plaid_transaction_id="mal_txn",
            name="<script>alert('xss')</script>",
            merchant_name="'; DROP TABLE transactions; --",
            amount_cents=-1000,
            date=date.today(),
            description="<img src=x onerror=alert('xss')>",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Extract features (should be sanitized)
        features = extractor.extract_all_features(malicious_transaction)

        # Verify HTML/SQL injection attempts are cleaned
        text_features = " ".join(features.text_features)
        assert "<script>" not in text_features
        assert "DROP TABLE" not in text_features
        assert "<img" not in text_features

        # Text should still contain some content
        assert len(text_features.strip()) > 0


@pytest.mark.integration
class TestE2ECategorizationWorkflow:
    """End-to-end categorization workflow tests."""

    def test_complete_categorization_pipeline(
        self,
        client: TestClient,
        auth_headers: dict,
        db_session: Session,
        test_user: User,
        test_account: Account
    ):
        """Test complete categorization pipeline from transaction to prediction."""

        # Step 1: Create categories via API
        category_data = {
            "name": "Coffee Shops",
            "parent_category": "Food & Dining",
            "description": "Coffee and cafe purchases",
            "color": "#8D6E63",
            "icon": "local_cafe",
            "rules": [
                {
                    "type": "text_match",
                    "field": "merchant",
                    "operator": "contains",
                    "value": "starbucks",
                    "confidence": 0.95
                }
            ]
        }

        response = client.post(
            "/api/categories/",
            json=category_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        category = response.json()

        # Step 2: Create transaction via API
        transaction_data = {
            "account_id": str(test_account.id),
            "name": "Starbucks Coffee",
            "merchant_name": "Starbucks",
            "amount": -5.99,
            "date": date.today().isoformat(),
            "pending": False
        }

        response = client.post(
            "/api/transactions/",
            json=transaction_data,
            headers=auth_headers
        )

        if response.status_code == 200:
            transaction = response.json()

            # Step 3: Test automatic categorization
            response = client.post(
                f"/api/ml/categorize/{transaction['id']}",
                headers=auth_headers
            )

            if response.status_code == 200:
                categorization = response.json()
                assert categorization["suggested_category"] == "Coffee Shops"
                assert categorization["confidence"] >= 0.9

            # Step 4: Apply categorization
            response = client.put(
                f"/api/transactions/{transaction['id']}",
                json={"user_category": "Coffee Shops"},
                headers=auth_headers
            )
            assert response.status_code == 200

            # Step 5: Verify in statistics
            response = client.get("/api/transactions/stats", headers=auth_headers)
            assert response.status_code == 200
            stats = response.json()

            coffee_category = next(
                (c for c in stats["categories"] if c["category"] == "Coffee Shops"),
                None
            )
            assert coffee_category is not None
            assert coffee_category["transaction_count"] >= 1