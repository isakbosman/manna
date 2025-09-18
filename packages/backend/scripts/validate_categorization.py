#!/usr/bin/env python3
"""
Simple validation script for the transaction categorization system.
Tests core functionality without requiring full dependency stack.
"""

import os
import sys
import logging
import tempfile
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Any
from uuid import uuid4

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_imports():
    """Test that core modules can be imported."""
    logger.info("Validating imports...")

    try:
        # Test basic imports
        from src.schemas.transaction import Transaction, TransactionCategorization
        from src.schemas.category import CategoryCreate, CategoryRule
        logger.info("✓ Schema imports successful")

        # Test database models (may fail due to database dependency)
        try:
            from src.database.models import Transaction as TransactionModel
            logger.info("✓ Database model imports successful")
        except Exception as e:
            logger.warning(f"⚠ Database model imports failed (expected): {e}")

        # Test ML service imports
        try:
            from src.services.ml_categorization import FeatureExtractor
            logger.info("✓ ML service imports successful")
        except Exception as e:
            logger.warning(f"⚠ ML service imports failed: {e}")
            return False

        return True

    except Exception as e:
        logger.error(f"✗ Import validation failed: {e}")
        return False

def validate_feature_extraction():
    """Test feature extraction functionality."""
    logger.info("Validating feature extraction...")

    try:
        from src.services.ml_categorization import FeatureExtractor

        # Create a mock transaction class for testing
        class MockTransaction:
            def __init__(self):
                self.id = "test-id"
                self.name = "Starbucks Coffee Shop"
                self.merchant_name = "Starbucks"
                self.amount = -5.75
                self.amount_cents = -575
                self.date = date.today()
                self.description = "Coffee purchase"

        extractor = FeatureExtractor()
        mock_transaction = MockTransaction()

        # Test text feature extraction
        text_features = extractor.extract_text_features(mock_transaction)
        assert len(text_features) > 0, "Text features should not be empty"
        assert "starbucks" in text_features.lower(), "Should contain merchant name"
        logger.info(f"✓ Text features extracted: {text_features[:50]}...")

        # Test amount feature extraction
        amount_features = extractor.extract_amount_features(mock_transaction)
        assert isinstance(amount_features, dict), "Amount features should be a dict"
        assert "amount_raw" in amount_features, "Should contain raw amount"
        assert amount_features["amount_raw"] == -5.75, "Raw amount should match"
        logger.info(f"✓ Amount features extracted: {len(amount_features)} features")

        # Test temporal feature extraction
        temporal_features = extractor.extract_temporal_features(mock_transaction)
        assert isinstance(temporal_features, dict), "Temporal features should be a dict"
        assert "month" in temporal_features, "Should contain month"
        assert temporal_features["month"] == mock_transaction.date.month, "Month should match"
        logger.info(f"✓ Temporal features extracted: {len(temporal_features)} features")

        # Test merchant feature extraction
        merchant_features = extractor.extract_merchant_features(mock_transaction)
        assert isinstance(merchant_features, dict), "Merchant features should be a dict"
        # Should detect coffee shop
        logger.info(f"✓ Merchant features extracted: {len(merchant_features)} features")

        # Test full feature extraction
        full_features = extractor.extract_all_features(mock_transaction)
        assert hasattr(full_features, 'text_features'), "Should have text features"
        assert hasattr(full_features, 'amount_features'), "Should have amount features"
        assert hasattr(full_features, 'temporal_features'), "Should have temporal features"
        assert hasattr(full_features, 'merchant_features'), "Should have merchant features"
        logger.info("✓ Full feature extraction successful")

        return True

    except Exception as e:
        logger.error(f"✗ Feature extraction validation failed: {e}")
        return False

def validate_rule_patterns():
    """Test rule pattern functionality."""
    logger.info("Validating rule patterns...")

    try:
        from src.services.ml_categorization import MLCategorizationService

        # Create ML service with temporary model path
        with tempfile.TemporaryDirectory() as temp_dir:
            ml_service = MLCategorizationService(model_path=Path(temp_dir))

            # Test rule patterns exist
            assert hasattr(ml_service, 'rule_patterns'), "Should have rule patterns"
            assert isinstance(ml_service.rule_patterns, dict), "Rule patterns should be a dict"
            assert len(ml_service.rule_patterns) > 0, "Should have some rule patterns"

            # Check for common categories
            expected_categories = ["Food & Dining", "Transportation", "Shopping", "Income"]
            for category in expected_categories:
                assert category in ml_service.rule_patterns, f"Should have rules for {category}"
                rules = ml_service.rule_patterns[category]
                assert len(rules) > 0, f"Should have rules for {category}"
                logger.info(f"✓ Found {len(rules)} rules for {category}")

            logger.info("✓ Rule pattern validation successful")
            return True

    except Exception as e:
        logger.error(f"✗ Rule pattern validation failed: {e}")
        return False

def validate_schemas():
    """Test Pydantic schema validation."""
    logger.info("Validating schemas...")

    try:
        from src.schemas.transaction import TransactionCategorization, TransactionUpdate
        from src.schemas.category import CategoryCreate, CategoryRule

        # Test TransactionCategorization schema
        categorization = TransactionCategorization(
            transaction_id=uuid4(),
            suggested_category="Food & Dining",
            confidence=0.95,
            alternative_categories=[
                {"Coffee & Cafes": 0.85}
            ],
            rules_applied=["Rule: Starbucks pattern"]
        )
        assert categorization.confidence == 0.95, "Confidence should be preserved"
        logger.info("✓ TransactionCategorization schema validation successful")

        # Test CategoryRule schema
        rule = CategoryRule(
            type="text",
            field="merchant",
            operator="contains",
            value="starbucks",
            case_sensitive=False
        )
        assert rule.type == "text", "Rule type should be preserved"
        logger.info("✓ CategoryRule schema validation successful")

        # Test CategoryCreate schema
        category = CategoryCreate(
            name="Test Category",
            parent_category="Food & Dining",
            description="Test category description",
            color="#FF5722",
            icon="restaurant",
            rules=[rule.dict()]
        )
        assert category.name == "Test Category", "Category name should be preserved"
        logger.info("✓ CategoryCreate schema validation successful")

        return True

    except Exception as e:
        logger.error(f"✗ Schema validation failed: {e}")
        return False

def validate_file_structure():
    """Validate that all expected files exist."""
    logger.info("Validating file structure...")

    base_path = Path(__file__).parent.parent

    expected_files = [
        # Core source files
        "src/services/ml_categorization.py",
        "src/schemas/transaction.py",
        "src/schemas/category.py",

        # Test files
        "tests/test_categorization_flow.py",
        "tests/test_api_endpoints.py",
        "tests/conftest.py",

        # Scripts
        "scripts/demo_categorization.py",
        "scripts/run_tests.py",

        # Seeds
        "seeds/seed_categories.py",

        # Documentation
        "CATEGORIZATION_SYSTEM.md"
    ]

    missing_files = []
    for file_path in expected_files:
        full_path = base_path / file_path
        if full_path.exists():
            logger.info(f"✓ Found {file_path}")
        else:
            missing_files.append(file_path)
            logger.warning(f"✗ Missing {file_path}")

    if missing_files:
        logger.error(f"Missing {len(missing_files)} expected files")
        return False
    else:
        logger.info("✓ All expected files found")
        return True

def validate_configuration():
    """Test configuration loading."""
    logger.info("Validating configuration...")

    try:
        from src.config import settings

        # Check that essential settings exist
        assert hasattr(settings, 'database_url'), "Should have database_url"
        assert hasattr(settings, 'ml_model_path'), "Should have ml_model_path"
        assert hasattr(settings, 'ml_confidence_threshold'), "Should have ml_confidence_threshold"

        # Check types
        assert isinstance(settings.ml_confidence_threshold, (int, float)), "Confidence threshold should be numeric"
        assert 0 <= settings.ml_confidence_threshold <= 1, "Confidence threshold should be between 0 and 1"

        logger.info(f"✓ Configuration loaded successfully")
        logger.info(f"  Database URL: {str(settings.database_url)[:50]}...")
        logger.info(f"  ML Model Path: {settings.ml_model_path}")
        logger.info(f"  Confidence Threshold: {settings.ml_confidence_threshold}")

        return True

    except Exception as e:
        logger.error(f"✗ Configuration validation failed: {e}")
        return False

def main():
    """Run all validations."""
    logger.info("Starting Transaction Categorization System Validation")
    logger.info("=" * 60)

    validations = [
        ("File Structure", validate_file_structure),
        ("Configuration", validate_configuration),
        ("Imports", validate_imports),
        ("Schemas", validate_schemas),
        ("Feature Extraction", validate_feature_extraction),
        ("Rule Patterns", validate_rule_patterns),
    ]

    results = {}

    for name, validation_func in validations:
        logger.info(f"\n{'-'*40}")
        logger.info(f"Running: {name}")
        try:
            results[name] = validation_func()
        except Exception as e:
            logger.error(f"Validation {name} failed with exception: {e}")
            results[name] = False

    # Generate report
    logger.info(f"\n{'='*60}")
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    logger.info(f"Total validations: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {total - passed}")
    logger.info(f"Success rate: {(passed/total)*100:.1f}%")

    logger.info(f"\nDetailed Results:")
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {name:<20} {status}")

    if all(results.values()):
        logger.info(f"\n🎉 All validations passed! The categorization system is ready.")
        return True
    else:
        logger.info(f"\n⚠️  Some validations failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)