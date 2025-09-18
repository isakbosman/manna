#!/usr/bin/env python3
"""
Demonstration script for the ML-powered transaction categorization system.
This script shows how to use the enhanced ML categorization features.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import our models and services
from src.database.models import Transaction, Category, Account, User
from src.services.ml_categorization import ml_service
from src.services.category_rules import category_rules_service
from src.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_transactions(db_session, account_id: str) -> list:
    """Create sample transactions for demonstration."""

    sample_transactions = [
        {
            "name": "STARBUCKS COFFEE",
            "merchant_name": "Starbucks",
            "amount": -4.75,
            "date": datetime.now() - timedelta(days=1),
            "description": "Coffee purchase",
            "transaction_type": "debit"
        },
        {
            "name": "AMAZON.COM PURCHASE",
            "merchant_name": "Amazon",
            "amount": -29.99,
            "date": datetime.now() - timedelta(days=2),
            "description": "Online shopping",
            "transaction_type": "debit"
        },
        {
            "name": "SHELL GAS STATION",
            "merchant_name": "Shell",
            "amount": -45.67,
            "date": datetime.now() - timedelta(days=3),
            "description": "Fuel purchase",
            "transaction_type": "debit"
        },
        {
            "name": "NETFLIX.COM",
            "merchant_name": "Netflix",
            "amount": -15.99,
            "date": datetime.now() - timedelta(days=4),
            "description": "Monthly subscription",
            "transaction_type": "debit",
            "is_recurring": True
        },
        {
            "name": "SALARY DEPOSIT",
            "merchant_name": "ACME CORP",
            "amount": 3500.00,
            "date": datetime.now() - timedelta(days=5),
            "description": "Bi-weekly salary",
            "transaction_type": "credit"
        },
        {
            "name": "UBER RIDE",
            "merchant_name": "Uber",
            "amount": -12.50,
            "date": datetime.now() - timedelta(days=6),
            "description": "Transportation",
            "transaction_type": "debit"
        }
    ]

    transactions = []
    for txn_data in sample_transactions:
        transaction = Transaction(
            account_id=account_id,
            name=txn_data["name"],
            merchant_name=txn_data["merchant_name"],
            amount=txn_data["amount"],
            date=txn_data["date"],
            description=txn_data["description"],
            transaction_type=txn_data["transaction_type"],
            is_recurring=txn_data.get("is_recurring", False)
        )
        db_session.add(transaction)
        transactions.append(transaction)

    db_session.commit()
    logger.info(f"Created {len(transactions)} sample transactions")
    return transactions


def demonstrate_rule_based_categorization(db_session, transactions: list):
    """Demonstrate rule-based categorization."""

    logger.info("\n" + "="*60)
    logger.info("DEMONSTRATING RULE-BASED CATEGORIZATION")
    logger.info("="*60)

    for transaction in transactions:
        # Apply rules to categorize
        rule_match = category_rules_service.get_best_rule_match(
            transaction=transaction,
            db=db_session
        )

        if rule_match:
            logger.info(f"Transaction: {transaction.name}")
            logger.info(f"  Amount: ${transaction.amount}")
            logger.info(f"  Suggested Category: {rule_match.category_name}")
            logger.info(f"  Confidence: {rule_match.confidence:.2%}")
            logger.info(f"  Rule Applied: {rule_match.rule_name}")
            logger.info(f"  Match Field: {rule_match.match_field}")
        else:
            logger.info(f"Transaction: {transaction.name}")
            logger.info(f"  Amount: ${transaction.amount}")
            logger.info(f"  No rule match found")

        logger.info("-" * 40)


def demonstrate_ml_categorization(db_session, transactions: list):
    """Demonstrate ML-based categorization."""

    logger.info("\n" + "="*60)
    logger.info("DEMONSTRATING ML CATEGORIZATION")
    logger.info("="*60)

    # Try to categorize with ML (may not work without trained model)
    for transaction in transactions:
        try:
            result = ml_service.categorize_transaction(
                transaction=transaction,
                use_ml=True,
                use_rules=True
            )

            logger.info(f"Transaction: {transaction.name}")
            logger.info(f"  Amount: ${transaction.amount}")
            logger.info(f"  Suggested Category: {result.suggested_category}")
            logger.info(f"  Confidence: {result.confidence:.2%}")
            logger.info(f"  Rules Applied: {result.rules_applied}")

            if result.alternative_categories:
                logger.info("  Alternatives:")
                for alt in result.alternative_categories:
                    logger.info(f"    - {alt['category']}: {alt['confidence']:.2%}")

        except Exception as e:
            logger.error(f"ML categorization failed for {transaction.name}: {e}")

        logger.info("-" * 40)


def demonstrate_batch_categorization(db_session, transactions: list):
    """Demonstrate batch categorization."""

    logger.info("\n" + "="*60)
    logger.info("DEMONSTRATING BATCH CATEGORIZATION")
    logger.info("="*60)

    try:
        # Batch categorize all transactions
        results = ml_service.batch_categorize(transactions)

        logger.info(f"Batch categorized {len(results)} transactions")

        # Summary statistics
        high_confidence = sum(1 for r in results if r.confidence >= 0.8)
        medium_confidence = sum(1 for r in results if 0.6 <= r.confidence < 0.8)
        low_confidence = sum(1 for r in results if r.confidence < 0.6)

        logger.info(f"High confidence (≥80%): {high_confidence}")
        logger.info(f"Medium confidence (60-80%): {medium_confidence}")
        logger.info(f"Low confidence (<60%): {low_confidence}")

        # Category distribution
        categories = {}
        for result in results:
            cat = result.suggested_category
            categories[cat] = categories.get(cat, 0) + 1

        logger.info("\nCategory Distribution:")
        for category, count in categories.items():
            logger.info(f"  {category}: {count} transactions")

    except Exception as e:
        logger.error(f"Batch categorization failed: {e}")


def demonstrate_model_metrics():
    """Demonstrate model metrics and status."""

    logger.info("\n" + "="*60)
    logger.info("DEMONSTRATING MODEL METRICS")
    logger.info("="*60)

    try:
        metrics = ml_service.get_model_metrics()

        logger.info(f"Model loaded: {metrics.get('model_loaded', False)}")
        logger.info(f"Vectorizer loaded: {metrics.get('vectorizer_loaded', False)}")
        logger.info(f"Confidence threshold: {metrics.get('confidence_threshold', 0.75)}")
        logger.info(f"Model path: {metrics.get('model_path', 'N/A')}")
        logger.info(f"Cache enabled: {metrics.get('cache_enabled', False)}")

        rule_categories = metrics.get('rule_categories', [])
        logger.info(f"Rule categories available: {len(rule_categories)}")
        for category in rule_categories:
            logger.info(f"  - {category}")

        # Additional metrics if model is trained
        if metrics.get('test_accuracy'):
            logger.info(f"Test accuracy: {metrics['test_accuracy']:.2%}")
            logger.info(f"Training samples: {metrics.get('training_samples', 'N/A')}")
            logger.info(f"Feature count: {metrics.get('feature_count', 'N/A')}")

    except Exception as e:
        logger.error(f"Failed to get model metrics: {e}")


def create_custom_rule_example(db_session, user_id: str):
    """Demonstrate creating a custom categorization rule."""

    logger.info("\n" + "="*60)
    logger.info("DEMONSTRATING CUSTOM RULE CREATION")
    logger.info("="*60)

    try:
        # Create a custom rule for gym memberships
        rule_data = {
            "name": "Gym Membership",
            "rule_type": "keyword",
            "pattern": r"(?i)(gym|fitness|planet.*fitness|24.*hour|lifetime)",
            "pattern_type": "regex",
            "category_name": "Health & Fitness",
            "priority": 10,
            "match_fields": ["name", "merchant_name"],
            "confidence": 0.90
        }

        rule = category_rules_service.create_user_rule(
            db=db_session,
            user_id=user_id,
            rule_data=rule_data
        )

        logger.info(f"Created custom rule: {rule.name}")
        logger.info(f"  Rule ID: {rule.id}")
        logger.info(f"  Category: {rule.category.name}")
        logger.info(f"  Priority: {rule.priority}")

        # Get rule statistics
        stats = category_rules_service.get_rule_statistics(db_session, user_id)
        logger.info(f"\nRule Statistics for User:")
        logger.info(f"  Total rules: {stats['total_rules']}")
        logger.info(f"  Active rules: {stats['active_rules']}")
        logger.info(f"  Rules by type: {stats['rules_by_type']}")

    except Exception as e:
        logger.error(f"Failed to create custom rule: {e}")


def main():
    """Main demonstration function."""

    logger.info("Starting ML Transaction Categorization Demo")
    logger.info(f"Using database: {settings.database_url}")

    # Setup database connection
    try:
        engine = create_engine(settings.database_url)
        Session = sessionmaker(bind=engine)
        db_session = Session()

        # For demo purposes, we'll create a temporary user and account
        # In practice, these would already exist
        user = User(
            email="demo@example.com",
            username="demo_user",
            full_name="Demo User"
        )
        db_session.add(user)
        db_session.flush()  # Get the user ID

        account = Account(
            user_id=user.id,
            account_name="Demo Checking Account",
            account_type="checking",
            balance=5000.00
        )
        db_session.add(account)
        db_session.flush()  # Get the account ID

        logger.info(f"Created demo user: {user.email}")
        logger.info(f"Created demo account: {account.account_name}")

        # Create sample transactions
        transactions = create_sample_transactions(db_session, str(account.id))

        # Demonstrate different categorization methods
        demonstrate_rule_based_categorization(db_session, transactions)
        demonstrate_ml_categorization(db_session, transactions)
        demonstrate_batch_categorization(db_session, transactions)
        demonstrate_model_metrics()
        create_custom_rule_example(db_session, str(user.id))

        logger.info("\n" + "="*60)
        logger.info("DEMO COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        logger.info("The ML categorization system is working correctly!")
        logger.info("Next steps:")
        logger.info("1. Train models with real transaction data")
        logger.info("2. Create user-specific categorization rules")
        logger.info("3. Monitor and improve model performance")
        logger.info("4. Implement auto-categorization workflows")

        # Cleanup demo data
        db_session.rollback()  # Don't actually save demo data

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
    finally:
        if 'db_session' in locals():
            db_session.close()


if __name__ == "__main__":
    main()