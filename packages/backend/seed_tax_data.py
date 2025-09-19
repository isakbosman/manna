#!/usr/bin/env python3
"""Seed tax categorization data (tax categories and chart of accounts)."""

import os
import sys
from sqlalchemy.orm import Session

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal, create_tables
from seeds.seed_tax_data import seed_tax_categories, seed_chart_of_accounts
from models.user import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Seed tax categorization data."""
    try:
        # Create tables if they don't exist
        logger.info("Creating database tables...")
        create_tables()

        # Create session
        session = SessionLocal()

        try:
            # Seed tax categories (these are global, not user-specific)
            logger.info("Seeding tax categories...")
            tax_categories = seed_tax_categories(session)
            logger.info(f"Created {len(tax_categories)} tax categories")

            # Find a test user or create one
            test_user = session.query(User).filter_by(email="test@manna.com").first()
            if not test_user:
                logger.info("Creating test user...")
                test_user = User(
                    email="test@manna.com",
                    password_hash="$2b$12$sample_hash_for_testing",
                    first_name="Test",
                    last_name="User",
                    is_active=True,
                    is_verified=True,
                    business_name="Manna Financial LLC",
                    business_type="llc",
                    timezone="America/Los_Angeles"
                )
                session.add(test_user)
                session.commit()

            # Seed chart of accounts for the test user
            logger.info(f"Seeding chart of accounts for user {test_user.email}...")
            chart_accounts = seed_chart_of_accounts(session, str(test_user.id))
            logger.info(f"Created {len(chart_accounts)} chart of accounts entries")

            logger.info("Tax categorization data seeded successfully!")

        except Exception as e:
            session.rollback()
            logger.error(f"Error seeding data: {e}")
            raise
        finally:
            session.close()

    except Exception as e:
        logger.error(f"Failed to seed tax data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()