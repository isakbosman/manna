#!/usr/bin/env python3
"""Setup script for tax categorization system."""

import os
import sys
import logging
from datetime import date

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models.database import get_session
from models.user import User
from seeds.seed_tax_data import seed_tax_categories, seed_chart_of_accounts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_tax_categorization_system():
    """Set up the tax categorization system with initial data."""

    logger.info("Starting tax categorization system setup...")

    with get_session() as session:
        try:
            # 1. Seed tax categories (system-wide)
            logger.info("Seeding tax categories...")
            tax_categories = seed_tax_categories(session)
            logger.info(f"Created {len(tax_categories)} tax categories")

            # 2. Set up chart of accounts for all existing users
            users = session.query(User).all()
            logger.info(f"Setting up chart of accounts for {len(users)} users...")

            for user in users:
                logger.info(f"Creating chart of accounts for user: {user.email}")
                accounts = seed_chart_of_accounts(session, str(user.id))
                logger.info(f"Created {len(accounts)} accounts for user {user.email}")

            logger.info("Tax categorization system setup completed successfully!")

        except Exception as e:
            logger.error(f"Error setting up tax categorization system: {e}")
            session.rollback()
            raise


def verify_setup():
    """Verify that the setup was successful."""

    logger.info("Verifying tax categorization setup...")

    with get_session() as session:
        # Check tax categories
        from models.tax_categorization import TaxCategory, ChartOfAccount

        tax_category_count = session.query(TaxCategory).count()
        logger.info(f"Total tax categories: {tax_category_count}")

        # Check chart of accounts for first user
        users = session.query(User).limit(1).all()
        if users:
            user = users[0]
            account_count = session.query(ChartOfAccount).filter_by(user_id=user.id).count()
            logger.info(f"Chart of accounts entries for user {user.email}: {account_count}")

        logger.info("Verification completed!")


def migrate_existing_transactions():
    """Migrate existing transactions to use the new tax categorization fields."""

    logger.info("Migrating existing transactions...")

    with get_session() as session:
        from models.transaction import Transaction
        from models.tax_categorization import CategoryMapping, ChartOfAccount, TaxCategory

        # Get all transactions that need tax categorization
        transactions = session.query(Transaction).filter(
            Transaction.tax_category_id.is_(None)
        ).all()

        logger.info(f"Found {len(transactions)} transactions to migrate")

        migrated_count = 0
        for transaction in transactions:
            try:
                # Set tax year if not set
                if not transaction.tax_year and transaction.date:
                    transaction.tax_year = transaction.date.year

                # Try to auto-categorize based on existing category
                if transaction.category_id and transaction.account:
                    user_id = transaction.account.user_id

                    # Look for existing category mapping
                    mapping = session.query(CategoryMapping).filter_by(
                        user_id=user_id,
                        source_category_id=transaction.category_id,
                        is_active=True
                    ).first()

                    if mapping:
                        transaction.tax_category_id = mapping.tax_category_id
                        transaction.chart_account_id = mapping.chart_account_id
                        transaction.business_use_percentage = mapping.business_percentage_default

                        # Calculate deductible amount
                        if transaction.is_business and transaction.business_use_percentage:
                            business_amount = transaction.amount_decimal * (transaction.business_use_percentage / 100)
                            transaction.deductible_amount = business_amount

                        migrated_count += 1

            except Exception as e:
                logger.warning(f"Failed to migrate transaction {transaction.id}: {e}")
                continue

        session.commit()
        logger.info(f"Successfully migrated {migrated_count} transactions")


def main():
    """Main execution function."""

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "setup":
            setup_tax_categorization_system()
        elif command == "verify":
            verify_setup()
        elif command == "migrate":
            migrate_existing_transactions()
        elif command == "all":
            setup_tax_categorization_system()
            migrate_existing_transactions()
            verify_setup()
        else:
            print("Usage: python setup_tax_categorization.py [setup|verify|migrate|all]")
            sys.exit(1)
    else:
        # Default: run full setup
        setup_tax_categorization_system()
        migrate_existing_transactions()
        verify_setup()


if __name__ == "__main__":
    main()