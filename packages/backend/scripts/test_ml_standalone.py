#!/usr/bin/env python3
"""
Standalone test for ML categorization components without external dependencies.
"""

import os
import sys
import logging
import tempfile
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
from uuid import uuid4
import json
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockTransaction:
    """Mock transaction for testing without database dependencies."""

    def __init__(self, name: str, merchant_name: str = None, amount: float = 0, description: str = ""):
        self.id = str(uuid4())
        self.name = name
        self.merchant_name = merchant_name
        self.amount = amount
        self.amount_cents = int(amount * 100)
        self.date = date.today()
        self.description = description
        self.user_category = None
        self.primary_category = None
        self.is_reconciled = False
        self.pending = False
        self.tags = []
        self.notes = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class StandaloneFeatureExtractor:
    """Standalone feature extractor for testing."""

    def __init__(self):
        self.amount_bins = [0, 10, 50, 100, 500, 1000, float('inf')]
        self.amount_labels = ['micro', 'small', 'medium', 'large', 'xlarge', 'huge']

    def extract_text_features(self, transaction) -> str:
        """Extract and clean text features from transaction."""
        text_parts = []

        if transaction.name:
            text_parts.append(transaction.name.lower())

        if transaction.merchant_name:
            text_parts.append(transaction.merchant_name.lower())

        if hasattr(transaction, 'description') and transaction.description:
            text_parts.append(transaction.description.lower())

        full_text = " ".join(text_parts)
        full_text = re.sub(r'[^\w\s]', ' ', full_text)
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        return full_text

    def extract_amount_features(self, transaction) -> Dict[str, float]:
        """Extract amount-based features."""
        amount = float(transaction.amount)

        features = {
            'amount_raw': amount,
            'amount_abs': abs(amount),
            'amount_log': abs(amount) + 1,  # Simplified log
            'is_round_number': float(amount % 1 == 0),
            'is_even_dollar': float(amount % 10 == 0),
            'amount_magnitude': len(str(int(abs(amount)))),
        }

        # Amount bins (simplified)
        abs_amount = abs(amount)
        for i, threshold in enumerate(self.amount_bins[1:]):
            if abs_amount <= threshold:
                bin_label = self.amount_labels[i]
                for label in self.amount_labels:
                    features[f'amount_bin_{label}'] = float(label == bin_label)
                break

        return features

    def extract_temporal_features(self, transaction) -> Dict[str, Any]:
        """Extract time-based features."""
        dt = transaction.date

        features = {
            'hour': 12,  # Default hour since we don't have time
            'day_of_week': dt.weekday(),
            'day_of_month': dt.day,
            'month': dt.month,
            'quarter': (dt.month - 1) // 3 + 1,
            'is_weekend': float(dt.weekday() >= 5),
            'is_month_start': float(dt.day <= 3),
            'is_month_end': float(dt.day >= 28),
        }

        return features

    def extract_merchant_features(self, transaction) -> Dict[str, Any]:
        """Extract merchant-specific features."""
        features = {}

        if transaction.merchant_name:
            merchant = transaction.merchant_name.lower()

            features.update({
                'is_online_merchant': float(any(x in merchant for x in ['amazon', 'ebay', '.com', 'online'])),
                'is_gas_station': float(any(x in merchant for x in ['shell', 'exxon', 'chevron', 'bp', 'gas'])),
                'is_grocery': float(any(x in merchant for x in ['walmart', 'target', 'kroger', 'safeway', 'grocery'])),
                'is_restaurant': float(any(x in merchant for x in ['restaurant', 'cafe', 'coffee', 'pizza', 'mcdonalds'])),
                'is_bank': float(any(x in merchant for x in ['bank', 'credit union', 'atm', 'deposit'])),
                'is_subscription': float(any(x in merchant for x in ['netflix', 'spotify', 'subscription', 'monthly'])),
            })
        else:
            features.update({
                'is_online_merchant': 0.0,
                'is_gas_station': 0.0,
                'is_grocery': 0.0,
                'is_restaurant': 0.0,
                'is_bank': 0.0,
                'is_subscription': 0.0,
            })

        return features

class StandaloneRuleEngine:
    """Standalone rule engine for testing."""

    def __init__(self):
        self.rule_patterns = self._initialize_rule_patterns()

    def _initialize_rule_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize rule-based patterns."""
        return {
            "Food & Dining": [
                {
                    "pattern": r"(?i)(starbucks|coffee|cafe|restaurant|dining|food|eat|pizza|subway|mcdonald)",
                    "confidence": 0.95,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(uber.*eats|doordash|grubhub|postmates|delivery|takeout)",
                    "confidence": 0.90,
                    "priority": 1
                },
            ],
            "Transportation": [
                {
                    "pattern": r"(?i)(uber|lyft|taxi|cab|rideshare)",
                    "confidence": 0.95,
                    "priority": 1
                },
                {
                    "pattern": r"(?i)(gas|fuel|shell|exxon|chevron|bp|mobil|citgo)",
                    "confidence": 0.90,
                    "priority": 1
                },
            ],
            "Shopping": [
                {
                    "pattern": r"(?i)(amazon|walmart|target|costco|best buy|home depot)",
                    "confidence": 0.95,
                    "priority": 1
                },
            ],
            "Income": [
                {
                    "pattern": r"(?i)(salary|payroll|direct.*deposit|income|wage|payment.*from)",
                    "confidence": 0.95,
                    "priority": 1
                },
            ],
        }

    def apply_rules(self, transaction) -> tuple:
        """Apply rules to transaction and return category, confidence, rule name."""
        text_to_match = f"{transaction.name} {transaction.merchant_name or ''} {getattr(transaction, 'description', '') or ''}"

        best_category = None
        best_confidence = 0.0
        best_rule_name = None

        for category, patterns in self.rule_patterns.items():
            for pattern_dict in patterns:
                if re.search(pattern_dict['pattern'], text_to_match):
                    if pattern_dict['confidence'] > best_confidence:
                        best_category = category
                        best_confidence = pattern_dict['confidence']
                        best_rule_name = f"{category} (P{pattern_dict.get('priority', 5)})"
                        break

        return best_category, best_confidence, best_rule_name

def test_feature_extraction():
    """Test feature extraction functionality."""
    logger.info("Testing feature extraction...")

    extractor = StandaloneFeatureExtractor()

    # Test cases
    test_transactions = [
        MockTransaction("Starbucks Coffee Shop", "Starbucks", -5.75, "Coffee purchase"),
        MockTransaction("Shell Gas Station", "Shell", -45.00, "Fuel purchase"),
        MockTransaction("Amazon Purchase", "Amazon", -89.99, "Online shopping"),
        MockTransaction("Salary Deposit", "ACME Corp", 2500.00, "Payroll deposit"),
    ]

    for transaction in test_transactions:
        logger.info(f"\nTesting transaction: {transaction.name}")

        # Test text features
        text_features = extractor.extract_text_features(transaction)
        assert len(text_features) > 0, "Text features should not be empty"
        logger.info(f"  Text features: {text_features}")

        # Test amount features
        amount_features = extractor.extract_amount_features(transaction)
        assert isinstance(amount_features, dict), "Amount features should be a dict"
        assert "amount_raw" in amount_features, "Should contain raw amount"
        logger.info(f"  Amount features: {len(amount_features)} features")

        # Test temporal features
        temporal_features = extractor.extract_temporal_features(transaction)
        assert isinstance(temporal_features, dict), "Temporal features should be a dict"
        assert "month" in temporal_features, "Should contain month"
        logger.info(f"  Temporal features: {len(temporal_features)} features")

        # Test merchant features
        merchant_features = extractor.extract_merchant_features(transaction)
        assert isinstance(merchant_features, dict), "Merchant features should be a dict"
        logger.info(f"  Merchant features: {len(merchant_features)} features")

    logger.info("✓ Feature extraction tests passed")
    return True

def test_rule_engine():
    """Test rule-based categorization."""
    logger.info("Testing rule engine...")

    rule_engine = StandaloneRuleEngine()

    # Test cases with expected results
    test_cases = [
        (MockTransaction("Starbucks Coffee", "Starbucks", -5.75), "Food & Dining"),
        (MockTransaction("Shell Gas Station", "Shell", -45.00), "Transportation"),
        (MockTransaction("Amazon Purchase", "Amazon", -89.99), "Shopping"),
        (MockTransaction("Salary Deposit", "ACME Corp", 2500.00), "Income"),
        (MockTransaction("Uber Ride", "Uber", -18.50), "Transportation"),
        (MockTransaction("McDonald's", "McDonald's", -12.50), "Food & Dining"),
    ]

    correct_predictions = 0
    total_predictions = 0

    for transaction, expected_category in test_cases:
        category, confidence, rule_name = rule_engine.apply_rules(transaction)

        logger.info(f"\nTransaction: {transaction.name}")
        logger.info(f"  Expected: {expected_category}")
        logger.info(f"  Predicted: {category}")
        logger.info(f"  Confidence: {confidence}")
        logger.info(f"  Rule: {rule_name}")

        if category == expected_category:
            correct_predictions += 1
            logger.info("  ✓ Correct prediction")
        else:
            logger.info("  ✗ Incorrect prediction")

        total_predictions += 1

    accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
    logger.info(f"\nRule engine accuracy: {correct_predictions}/{total_predictions} = {accuracy:.1%}")

    assert accuracy >= 0.8, f"Rule engine accuracy {accuracy:.1%} below 80% threshold"
    logger.info("✓ Rule engine tests passed")
    return True

def test_integration():
    """Test integration of feature extraction and rule engine."""
    logger.info("Testing integration...")

    extractor = StandaloneFeatureExtractor()
    rule_engine = StandaloneRuleEngine()

    # Create a comprehensive test transaction
    transaction = MockTransaction(
        "Starbucks Coffee Purchase",
        "Starbucks",
        -6.25,
        "Morning coffee and pastry"
    )

    # Extract features
    text_features = extractor.extract_text_features(transaction)
    amount_features = extractor.extract_amount_features(transaction)
    temporal_features = extractor.extract_temporal_features(transaction)
    merchant_features = extractor.extract_merchant_features(transaction)

    # Apply rules
    category, confidence, rule_name = rule_engine.apply_rules(transaction)

    # Verify integration
    assert len(text_features) > 0, "Should have text features"
    assert len(amount_features) > 0, "Should have amount features"
    assert len(temporal_features) > 0, "Should have temporal features"
    assert len(merchant_features) > 0, "Should have merchant features"
    assert category is not None, "Should have predicted category"
    assert confidence > 0, "Should have confidence score"

    logger.info(f"Integrated test results:")
    logger.info(f"  Transaction: {transaction.name}")
    logger.info(f"  Category: {category}")
    logger.info(f"  Confidence: {confidence}")
    logger.info(f"  Text features length: {len(text_features)}")
    logger.info(f"  Amount features count: {len(amount_features)}")
    logger.info(f"  Temporal features count: {len(temporal_features)}")
    logger.info(f"  Merchant features count: {len(merchant_features)}")

    logger.info("✓ Integration tests passed")
    return True

def test_performance():
    """Test performance with larger datasets."""
    logger.info("Testing performance...")

    extractor = StandaloneFeatureExtractor()
    rule_engine = StandaloneRuleEngine()

    # Generate test data
    test_data = []
    for i in range(100):
        transaction = MockTransaction(
            f"Test Transaction {i}",
            f"Test Merchant {i % 10}",
            -25.00 + (i % 50),
            f"Test description {i}"
        )
        test_data.append(transaction)

    # Time the processing
    import time
    start_time = time.time()

    results = []
    for transaction in test_data:
        # Extract features
        text_features = extractor.extract_text_features(transaction)
        amount_features = extractor.extract_amount_features(transaction)
        temporal_features = extractor.extract_temporal_features(transaction)
        merchant_features = extractor.extract_merchant_features(transaction)

        # Apply rules
        category, confidence, rule_name = rule_engine.apply_rules(transaction)

        results.append({
            "transaction_id": transaction.id,
            "category": category,
            "confidence": confidence
        })

    processing_time = time.time() - start_time
    throughput = len(test_data) / processing_time

    logger.info(f"Performance test results:")
    logger.info(f"  Transactions processed: {len(test_data)}")
    logger.info(f"  Processing time: {processing_time:.2f} seconds")
    logger.info(f"  Throughput: {throughput:.1f} transactions/second")
    logger.info(f"  Average time per transaction: {(processing_time/len(test_data))*1000:.1f} ms")

    # Performance assertions
    assert throughput > 50, f"Throughput {throughput:.1f} tx/s below 50 tx/s threshold"
    assert (processing_time/len(test_data)) < 0.1, "Average processing time too slow"

    logger.info("✓ Performance tests passed")
    return True

def main():
    """Run all standalone tests."""
    logger.info("Starting Standalone ML Categorization Tests")
    logger.info("=" * 60)

    tests = [
        ("Feature Extraction", test_feature_extraction),
        ("Rule Engine", test_rule_engine),
        ("Integration", test_integration),
        ("Performance", test_performance),
    ]

    results = {}

    for test_name, test_func in tests:
        logger.info(f"\n{'-'*40}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            results[test_name] = False

    # Generate report
    logger.info(f"\n{'='*60}")
    logger.info("STANDALONE TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    logger.info(f"Total tests: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {total - passed}")
    logger.info(f"Success rate: {(passed/total)*100:.1f}%")

    logger.info(f"\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name:<20} {status}")

    if all(results.values()):
        logger.info(f"\n🎉 All standalone tests passed!")
        return True
    else:
        logger.info(f"\n⚠️  Some tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)