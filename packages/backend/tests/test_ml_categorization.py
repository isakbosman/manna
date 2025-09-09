"""Tests for ML categorization service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from datetime import date

from src.database.models import User, Account, Transaction
from src.services.ml_categorization import MLCategorizationService


class TestMLCategorizationEndpoints:
    """Test suite for ML categorization endpoints."""
    
    def test_categorize_single_transaction(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session,
        mock_ml_service
    ):
        """Test categorizing a single transaction."""
        # Create uncategorized transaction
        transaction = Transaction(
            user_id=test_user.id,
            account_id=sample_account.id,
            plaid_transaction_id="txn_categorize_test",
            amount_cents=-2500,
            iso_currency_code="USD",
            date=date.today(),
            name="Target Store #1234",
            merchant_name="Target",
            payment_channel="in store",
            pending=False
        )
        db_session.add(transaction)
        db_session.commit()
        
        # Mock ML response
        mock_ml_service.categorize_transaction.return_value = {
            "primary_category": "Shopping",
            "detailed_category": "General Merchandise",
            "confidence": 0.92
        }
        
        response = client.post(
            f"/api/v1/ml/categorize/transaction/{transaction.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["primary_category"] == "Shopping"
        assert data["detailed_category"] == "General Merchandise"
        assert data["confidence_level"] == 0.92
        
        # Verify transaction was updated
        db_session.refresh(transaction)
        assert transaction.primary_category == "Shopping"
        assert transaction.detailed_category == "General Merchandise"
        assert transaction.confidence_level == 0.92
    
    def test_categorize_transaction_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test categorizing non-existent transaction."""
        from uuid import uuid4
        
        fake_id = uuid4()
        response = client.post(
            f"/api/v1/ml/categorize/transaction/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_batch_categorize_transactions(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session,
        mock_ml_service
    ):
        """Test batch categorization of multiple transactions."""
        # Create multiple uncategorized transactions
        transactions = []
        transaction_data = [
            {"name": "Starbucks Coffee", "merchant": "Starbucks", "amount": -500},
            {"name": "Shell Gas Station", "merchant": "Shell", "amount": -4500},
            {"name": "Amazon Purchase", "merchant": "Amazon.com", "amount": -2999},
        ]
        
        for i, txn_data in enumerate(transaction_data):
            transaction = Transaction(
                user_id=test_user.id,
                account_id=sample_account.id,
                plaid_transaction_id=f"txn_batch_{i}",
                amount_cents=txn_data["amount"],
                iso_currency_code="USD",
                date=date.today(),
                name=txn_data["name"],
                merchant_name=txn_data["merchant"],
                payment_channel="in store",
                pending=False
            )
            db_session.add(transaction)
            transactions.append(transaction)
        
        db_session.commit()
        
        # Mock batch ML response
        mock_ml_service.batch_categorize.return_value = [
            {
                "transaction_id": str(transactions[0].id),
                "primary_category": "Food and Drink",
                "detailed_category": "Coffee Shops",
                "confidence": 0.95
            },
            {
                "transaction_id": str(transactions[1].id),
                "primary_category": "Transportation",
                "detailed_category": "Gas Stations",
                "confidence": 0.88
            },
            {
                "transaction_id": str(transactions[2].id),
                "primary_category": "Shopping",
                "detailed_category": "Online Marketplaces",
                "confidence": 0.93
            }
        ]
        
        request_data = {
            "transaction_ids": [str(txn.id) for txn in transactions],
            "force_recategorize": False
        }
        
        response = client.post(
            "/api/v1/ml/categorize/batch",
            json=request_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["processed_count"] == 3
        assert len(data["results"]) == 3
        
        # Verify all transactions were categorized
        for i, transaction in enumerate(transactions):
            db_session.refresh(transaction)
            expected_categories = [
                ("Food and Drink", "Coffee Shops"),
                ("Transportation", "Gas Stations"),
                ("Shopping", "Online Marketplaces")
            ]
            primary, detailed = expected_categories[i]
            assert transaction.primary_category == primary
            assert transaction.detailed_category == detailed
    
    def test_train_model_with_user_data(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session,
        mock_ml_service
    ):
        """Test training ML model with user-categorized data."""
        # Create transactions with user categories
        transactions = []
        for i in range(5):
            transaction = Transaction(
                user_id=test_user.id,
                account_id=sample_account.id,
                plaid_transaction_id=f"txn_train_{i}",
                amount_cents=-(1000 + i * 100),
                iso_currency_code="USD",
                date=date.today(),
                name=f"Training Transaction {i}",
                merchant_name=f"Merchant {i}",
                user_category="Business Expense",
                payment_channel="online",
                pending=False
            )
            db_session.add(transaction)
            transactions.append(transaction)
        
        db_session.commit()
        
        # Mock training response
        mock_ml_service.train_user_model.return_value = {
            "model_id": "user_model_123",
            "training_samples": 5,
            "accuracy": 0.85,
            "status": "completed"
        }
        
        response = client.post(
            "/api/v1/ml/train",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["model_id"] == "user_model_123"
        assert data["training_samples"] == 5
        assert data["accuracy"] == 0.85
    
    def test_get_categorization_suggestions(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        sample_account: Account,
        db_session: Session,
        mock_ml_service
    ):
        """Test getting categorization suggestions for similar transactions."""
        # Create a transaction
        transaction = Transaction(
            user_id=test_user.id,
            account_id=sample_account.id,
            plaid_transaction_id="txn_suggestion_test",
            amount_cents=-2500,
            iso_currency_code="USD",
            date=date.today(),
            name="Starbucks Store #1234",
            merchant_name="Starbucks",
            payment_channel="in store",
            pending=False
        )
        db_session.add(transaction)
        db_session.commit()
        
        # Mock suggestions response
        mock_ml_service.get_suggestions.return_value = [
            {
                "category": "Food and Drink",
                "subcategory": "Coffee Shops",
                "confidence": 0.95,
                "reason": "Similar merchant name"
            },
            {
                "category": "Food and Drink",
                "subcategory": "Fast Food",
                "confidence": 0.75,
                "reason": "Similar transaction pattern"
            }
        ]
        
        response = client.get(
            f"/api/v1/ml/suggestions/{transaction.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["suggestions"]) == 2
        assert data["suggestions"][0]["category"] == "Food and Drink"
        assert data["suggestions"][0]["confidence"] == 0.95
    
    def test_model_performance_metrics(
        self,
        client: TestClient,
        auth_headers: dict,
        mock_ml_service
    ):
        """Test getting ML model performance metrics."""
        # Mock performance metrics
        mock_ml_service.get_model_metrics.return_value = {
            "accuracy": 0.89,
            "precision": 0.91,
            "recall": 0.87,
            "f1_score": 0.89,
            "total_predictions": 1247,
            "correct_predictions": 1110,
            "last_trained": "2024-01-15T10:30:00Z",
            "training_samples": 2500
        }
        
        response = client.get(
            "/api/v1/ml/metrics",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["accuracy"] == 0.89
        assert data["total_predictions"] == 1247
        assert data["training_samples"] == 2500


class TestMLCategorizationService:
    """Test the ML categorization service directly."""
    
    @pytest.fixture
    def ml_service(self):
        """Create ML service instance for testing."""
        return MLCategorizationService()
    
    def test_extract_features_from_transaction(
        self,
        ml_service,
        sample_account: Account,
        test_user: User,
        db_session: Session
    ):
        """Test feature extraction from transaction data."""
        transaction = Transaction(
            user_id=test_user.id,
            account_id=sample_account.id,
            plaid_transaction_id="feature_test",
            amount_cents=-2500,
            iso_currency_code="USD",
            date=date.today(),
            name="Starbucks Store #1234",
            merchant_name="Starbucks",
            payment_channel="in store",
            pending=False
        )
        db_session.add(transaction)
        db_session.commit()
        
        with patch.object(ml_service, '_extract_features') as mock_extract:
            mock_extract.return_value = {
                "amount": -25.0,
                "merchant_name": "starbucks",
                "transaction_name": "starbucks store",
                "day_of_week": 1,
                "hour_of_day": 14,
                "is_weekend": False,
                "payment_channel": "in store"
            }
            
            features = ml_service._extract_features(transaction)
            
            assert features["amount"] == -25.0
            assert features["merchant_name"] == "starbucks"
            assert "day_of_week" in features
            assert "payment_channel" in features
    
    def test_predict_category(
        self,
        ml_service,
        sample_account: Account,
        test_user: User,
        db_session: Session
    ):
        """Test category prediction for a transaction."""
        transaction = Transaction(
            user_id=test_user.id,
            account_id=sample_account.id,
            plaid_transaction_id="predict_test",
            amount_cents=-3500,
            iso_currency_code="USD",
            date=date.today(),
            name="Shell Gas Station",
            merchant_name="Shell",
            payment_channel="in store",
            pending=False
        )
        db_session.add(transaction)
        db_session.commit()
        
        with patch.object(ml_service, 'predict_category') as mock_predict:
            mock_predict.return_value = {
                "primary_category": "Transportation",
                "detailed_category": "Gas Stations",
                "confidence": 0.88
            }
            
            result = ml_service.predict_category(transaction)
            
            assert result["primary_category"] == "Transportation"
            assert result["detailed_category"] == "Gas Stations"
            assert result["confidence"] == 0.88
    
    def test_batch_prediction(
        self,
        ml_service,
        sample_account: Account,
        test_user: User,
        db_session: Session
    ):
        """Test batch prediction for multiple transactions."""
        transactions = []
        for i in range(3):
            transaction = Transaction(
                user_id=test_user.id,
                account_id=sample_account.id,
                plaid_transaction_id=f"batch_predict_{i}",
                amount_cents=-(1000 + i * 500),
                iso_currency_code="USD",
                date=date.today(),
                name=f"Test Transaction {i}",
                merchant_name=f"Merchant {i}",
                payment_channel="online",
                pending=False
            )
            db_session.add(transaction)
            transactions.append(transaction)
        
        db_session.commit()
        
        with patch.object(ml_service, 'batch_predict') as mock_batch:
            mock_batch.return_value = [
                {
                    "transaction_id": str(transactions[0].id),
                    "primary_category": "Shopping",
                    "confidence": 0.85
                },
                {
                    "transaction_id": str(transactions[1].id),
                    "primary_category": "Food and Drink",
                    "confidence": 0.90
                },
                {
                    "transaction_id": str(transactions[2].id),
                    "primary_category": "Entertainment",
                    "confidence": 0.78
                }
            ]
            
            results = ml_service.batch_predict(transactions)
            
            assert len(results) == 3
            assert results[0]["primary_category"] == "Shopping"
            assert results[1]["primary_category"] == "Food and Drink"
            assert results[2]["primary_category"] == "Entertainment"
    
    def test_model_training(
        self,
        ml_service,
        test_user: User,
        sample_account: Account,
        db_session: Session
    ):
        """Test training model with user data."""
        # Create training data
        training_transactions = []
        categories = ["Food and Drink", "Transportation", "Shopping"]
        
        for i, category in enumerate(categories):
            for j in range(5):  # 5 transactions per category
                transaction = Transaction(
                    user_id=test_user.id,
                    account_id=sample_account.id,
                    plaid_transaction_id=f"train_{i}_{j}",
                    amount_cents=-(1000 + j * 100),
                    iso_currency_code="USD",
                    date=date.today(),
                    name=f"Training Transaction {i}_{j}",
                    user_category=category,
                    payment_channel="online",
                    pending=False
                )
                db_session.add(transaction)
                training_transactions.append(transaction)
        
        db_session.commit()
        
        with patch.object(ml_service, 'train_model') as mock_train:
            mock_train.return_value = {
                "model_id": "trained_model_123",
                "accuracy": 0.92,
                "training_samples": 15,
                "features_used": ["amount", "merchant_name", "transaction_name"]
            }
            
            result = ml_service.train_model(test_user.id)
            
            assert result["model_id"] == "trained_model_123"
            assert result["accuracy"] == 0.92
            assert result["training_samples"] == 15


class TestMLCategorizationSecurity:
    """Test ML categorization endpoint security."""
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that ML endpoints require authentication."""
        from uuid import uuid4
        
        endpoints = [
            f"/api/v1/ml/categorize/transaction/{uuid4()}",
            "/api/v1/ml/categorize/batch",
            "/api/v1/ml/train",
            "/api/v1/ml/metrics",
        ]
        
        for endpoint in endpoints:
            if "batch" in endpoint or "train" in endpoint:
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint) if "metrics" in endpoint else client.post(endpoint)
            assert response.status_code == 401
    
    def test_transaction_access_control(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        sample_account: Account,
        db_session: Session
    ):
        """Test that users can only categorize their own transactions."""
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
            plaid_transaction_id="other_user_txn",
            amount_cents=-1500,
            iso_currency_code="USD",
            date=date.today(),
            name="Other User Transaction",
            payment_channel="online",
            pending=False
        )
        db_session.add(other_transaction)
        db_session.commit()
        
        # Try to categorize other user's transaction
        response = client.post(
            f"/api/v1/ml/categorize/transaction/{other_transaction.id}",
            headers=auth_headers
        )
        assert response.status_code == 404  # Should not be found
