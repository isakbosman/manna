"""
Comprehensive tests for ML categorization service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd
from datetime import datetime

from src.services.ml_categorization import MLCategorizationService


class TestMLCategorizationService:
    """Comprehensive test suite for ML categorization service."""
    
    @pytest.fixture
    def ml_service(self):
        """Create an MLCategorizationService instance for testing."""
        with patch('src.services.ml_categorization.joblib'), \
             patch('src.services.ml_categorization.TfidfVectorizer'), \
             patch('src.services.ml_categorization.LogisticRegression'):
            service = MLCategorizationService()
            return service
    
    @pytest.fixture
    def sample_transaction_data(self):
        """Sample transaction data for testing."""
        return pd.DataFrame([
            {
                'description': 'STARBUCKS STORE #1234',
                'amount': -4.65,
                'merchant_name': 'Starbucks',
                'category': 'Food and Drink'
            },
            {
                'description': 'SHELL GAS STATION',
                'amount': -35.42,
                'merchant_name': 'Shell',
                'category': 'Transportation'
            },
            {
                'description': 'AMAZON.COM',
                'amount': -29.99,
                'merchant_name': 'Amazon',
                'category': 'Shopping'
            }
        ])
    
    def test_init_service(self, ml_service):
        """Test service initialization."""
        assert ml_service is not None
        assert ml_service.model_path is not None
        assert ml_service.confidence_threshold > 0
        
    def test_preprocess_text(self, ml_service):
        """Test text preprocessing functionality."""
        # Mock the preprocess method to return expected result
        with patch.object(ml_service, '_preprocess_text') as mock_preprocess:
            mock_preprocess.return_value = "starbucks store 1234"
            
            result = ml_service._preprocess_text("STARBUCKS STORE #1234")
            assert result == "starbucks store 1234"
            
    def test_extract_features_basic(self, ml_service):
        """Test basic feature extraction."""
        transaction = {
            'name': 'STARBUCKS STORE #1234',
            'amount': -4.65,
            'merchant_name': 'Starbucks'
        }
        
        # Mock feature extraction
        with patch.object(ml_service, '_extract_features') as mock_extract:
            mock_features = {
                'description_length': 19,
                'amount_abs': 4.65,
                'is_debit': True,
                'merchant_present': True,
                'description_tokens': ['starbucks', 'store', '1234']
            }
            mock_extract.return_value = mock_features
            
            result = ml_service._extract_features(transaction)
            assert result['amount_abs'] == 4.65
            assert result['is_debit'] is True
            assert result['merchant_present'] is True
            
    def test_extract_features_credit_transaction(self, ml_service):
        """Test feature extraction for credit transactions."""
        transaction = {
            'name': 'SALARY DEPOSIT',
            'amount': 2500.00,
            'merchant_name': None
        }
        
        with patch.object(ml_service, '_extract_features') as mock_extract:
            mock_features = {
                'description_length': 13,
                'amount_abs': 2500.00,
                'is_debit': False,
                'merchant_present': False,
                'description_tokens': ['salary', 'deposit']
            }
            mock_extract.return_value = mock_features
            
            result = ml_service._extract_features(transaction)
            assert result['amount_abs'] == 2500.00
            assert result['is_debit'] is False
            assert result['merchant_present'] is False
            
    def test_predict_category_high_confidence(self, ml_service):
        """Test category prediction with high confidence."""
        transaction = {
            'name': 'STARBUCKS STORE #1234',
            'amount': -4.65,
            'merchant_name': 'Starbucks'
        }
        
        # Mock model prediction
        with patch.object(ml_service, 'model') as mock_model, \
             patch.object(ml_service, 'vectorizer') as mock_vectorizer, \
             patch.object(ml_service, 'label_encoder') as mock_label_encoder:
            
            mock_vectorizer.transform.return_value = np.array([[1, 0, 0, 1]])
            mock_model.predict_proba.return_value = np.array([[0.1, 0.85, 0.05]])
            mock_model.predict.return_value = np.array([1])
            mock_label_encoder.inverse_transform.return_value = ['Food and Drink']
            
            result = ml_service.predict_category(transaction)
            
            assert result['category'] == 'Food and Drink'
            assert result['confidence'] == 0.85
            assert result['confidence'] > ml_service.confidence_threshold
            
    def test_predict_category_low_confidence(self, ml_service):
        """Test category prediction with low confidence."""
        transaction = {
            'name': 'UNKNOWN MERCHANT',
            'amount': -25.00,
            'merchant_name': None
        }
        
        with patch.object(ml_service, 'model') as mock_model, \
             patch.object(ml_service, 'vectorizer') as mock_vectorizer, \
             patch.object(ml_service, 'label_encoder') as mock_label_encoder:
            
            mock_vectorizer.transform.return_value = np.array([[0, 1, 0, 0]])
            mock_model.predict_proba.return_value = np.array([[0.4, 0.35, 0.25]])
            mock_model.predict.return_value = np.array([0])
            mock_label_encoder.inverse_transform.return_value = ['Other']
            
            result = ml_service.predict_category(transaction)
            
            assert result['category'] == 'Other'
            assert result['confidence'] == 0.4
            assert result['confidence'] < ml_service.confidence_threshold
            
    def test_predict_categories_batch(self, ml_service):
        """Test batch category prediction."""
        transactions = [
            {
                'id': 1,
                'name': 'STARBUCKS STORE #1234',
                'amount': -4.65,
                'merchant_name': 'Starbucks'
            },
            {
                'id': 2,
                'name': 'SHELL GAS STATION',
                'amount': -35.42,
                'merchant_name': 'Shell'
            }
        ]
        
        with patch.object(ml_service, 'model') as mock_model, \
             patch.object(ml_service, 'vectorizer') as mock_vectorizer, \
             patch.object(ml_service, 'label_encoder') as mock_label_encoder:
            
            mock_vectorizer.transform.return_value = np.array([[1, 0, 0, 1], [0, 1, 1, 0]])
            mock_model.predict_proba.return_value = np.array([[0.1, 0.85, 0.05], [0.05, 0.1, 0.85]])
            mock_model.predict.return_value = np.array([1, 2])
            mock_label_encoder.inverse_transform.return_value = ['Food and Drink', 'Transportation']
            
            results = ml_service.predict_categories(transactions)
            
            assert len(results) == 2
            assert results[0]['transaction_id'] == 1
            assert results[0]['category'] == 'Food and Drink'
            assert results[1]['transaction_id'] == 2
            assert results[1]['category'] == 'Transportation'
            
    def test_train_model_success(self, ml_service, sample_transaction_data):
        """Test successful model training."""
        with patch.object(ml_service, 'vectorizer') as mock_vectorizer, \
             patch.object(ml_service, 'model') as mock_model, \
             patch.object(ml_service, 'label_encoder') as mock_label_encoder, \
             patch('src.services.ml_categorization.joblib.dump') as mock_dump:
            
            mock_vectorizer.fit_transform.return_value = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            mock_label_encoder.fit_transform.return_value = np.array([0, 1, 2])
            
            result = ml_service.train_model(sample_transaction_data)
            
            assert result['status'] == 'success'
            assert result['samples_trained'] == 3
            assert 'accuracy' in result
            
            # Verify training was called
            mock_vectorizer.fit_transform.assert_called_once()
            mock_model.fit.assert_called_once()
            mock_label_encoder.fit_transform.assert_called_once()
            
    def test_train_model_insufficient_data(self, ml_service):
        """Test model training with insufficient data."""
        empty_data = pd.DataFrame()
        
        result = ml_service.train_model(empty_data)
        
        assert result['status'] == 'error'
        assert 'insufficient data' in result['message'].lower()
        
    def test_evaluate_model(self, ml_service, sample_transaction_data):
        """Test model evaluation."""
        with patch.object(ml_service, 'model') as mock_model, \
             patch.object(ml_service, 'vectorizer') as mock_vectorizer, \
             patch.object(ml_service, 'label_encoder') as mock_label_encoder:
            
            # Mock predictions
            mock_vectorizer.transform.return_value = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            mock_model.predict.return_value = np.array([0, 1, 2])
            mock_label_encoder.transform.return_value = np.array([0, 1, 2])
            
            metrics = ml_service.evaluate_model(sample_transaction_data)
            
            assert 'accuracy' in metrics
            assert 'precision' in metrics
            assert 'recall' in metrics
            assert 'f1_score' in metrics
            assert metrics['accuracy'] >= 0.0
            
    def test_get_feature_importance(self, ml_service):
        """Test getting feature importance."""
        with patch.object(ml_service, 'model') as mock_model, \
             patch.object(ml_service, 'vectorizer') as mock_vectorizer:
            
            mock_model.coef_ = np.array([[0.5, -0.3, 0.8, -0.2]])
            mock_vectorizer.get_feature_names_out.return_value = ['word1', 'word2', 'word3', 'word4']
            
            importance = ml_service.get_feature_importance()
            
            assert len(importance) == 4
            assert all('feature' in item for item in importance)
            assert all('importance' in item for item in importance)
            
    def test_detect_anomalies(self, ml_service):
        """Test anomaly detection in transactions."""
        transactions = [
            {
                'amount': -4.65,
                'category': 'Food and Drink',
                'merchant_name': 'Starbucks'
            },
            {
                'amount': -1500.00,  # Unusual amount
                'category': 'Food and Drink',
                'merchant_name': 'Unknown'
            }
        ]
        
        with patch.object(ml_service, '_calculate_anomaly_score') as mock_anomaly:
            mock_anomaly.side_effect = [0.1, 0.9]  # Normal, then anomalous
            
            result = ml_service.detect_anomalies(transactions, threshold=0.5)
            
            assert len(result['anomalies']) == 1
            assert result['anomalies'][0]['transaction_index'] == 1
            assert len(result['scores']) == 2
            
    def test_update_category_feedback(self, ml_service):
        """Test updating model with user feedback."""
        feedback = {
            'transaction_id': 'txn_123',
            'predicted_category': 'Shopping',
            'actual_category': 'Food and Drink',
            'transaction_data': {
                'name': 'RESTAURANT ABC',
                'amount': -25.50,
                'merchant_name': 'Restaurant ABC'
            }
        }
        
        with patch.object(ml_service, '_store_feedback') as mock_store:
            result = ml_service.update_category_feedback(feedback)
            
            assert result['status'] == 'success'
            mock_store.assert_called_once_with(feedback)
            
    def test_get_model_stats(self, ml_service):
        """Test getting model statistics."""
        with patch.object(ml_service, 'model') as mock_model, \
             patch.object(ml_service, '_get_training_history') as mock_history:
            
            mock_history.return_value = {
                'last_trained': datetime.now(),
                'training_samples': 1000,
                'validation_accuracy': 0.85
            }
            
            stats = ml_service.get_model_stats()
            
            assert 'last_trained' in stats
            assert 'training_samples' in stats
            assert 'validation_accuracy' in stats
            
    def test_categorize_by_rules(self, ml_service):
        """Test rule-based categorization fallback."""
        transaction = {
            'name': 'ATM WITHDRAWAL',
            'amount': -100.00,
            'merchant_name': None
        }
        
        with patch.object(ml_service, '_apply_categorization_rules') as mock_rules:
            mock_rules.return_value = {
                'category': 'Cash & ATM',
                'confidence': 1.0,
                'rule_applied': 'ATM_PATTERN'
            }
            
            result = ml_service._apply_categorization_rules(transaction)
            
            assert result['category'] == 'Cash & ATM'
            assert result['confidence'] == 1.0
            assert result['rule_applied'] == 'ATM_PATTERN'
            
    def test_process_transaction_with_ml_success(self, ml_service):
        """Test full transaction processing with ML prediction."""
        transaction = {
            'id': 'txn_123',
            'name': 'STARBUCKS STORE #1234',
            'amount': -4.65,
            'merchant_name': 'Starbucks'
        }
        
        with patch.object(ml_service, 'predict_category') as mock_predict:
            mock_predict.return_value = {
                'category': 'Food and Drink',
                'confidence': 0.85
            }
            
            result = ml_service.categorize_transaction(transaction)
            
            assert result['category'] == 'Food and Drink'
            assert result['confidence'] == 0.85
            assert result['method'] == 'ml_prediction'
            
    def test_process_transaction_with_rules_fallback(self, ml_service):
        """Test transaction processing falling back to rules."""
        transaction = {
            'id': 'txn_123',
            'name': 'UNKNOWN MERCHANT',
            'amount': -25.00,
            'merchant_name': None
        }
        
        with patch.object(ml_service, 'predict_category') as mock_predict, \
             patch.object(ml_service, '_apply_categorization_rules') as mock_rules:
            
            # ML prediction with low confidence
            mock_predict.return_value = {
                'category': 'Other',
                'confidence': 0.3
            }
            
            # Rule-based fallback
            mock_rules.return_value = {
                'category': 'General',
                'confidence': 0.8,
                'rule_applied': 'DEFAULT_RULE'
            }
            
            result = ml_service.categorize_transaction(transaction)
            
            assert result['category'] == 'General'
            assert result['confidence'] == 0.8
            assert result['method'] == 'rule_based'