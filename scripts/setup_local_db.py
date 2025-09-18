#!/usr/bin/env python
"""
Setup script for local PostgreSQL database.
Creates the database schema and seeds it with test data.
"""

import os
import sys
import uuid
from datetime import datetime

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'backend'))

# Import after path is set
from src.database import SessionLocal, init_db, engine
from src.database.models import User, Institution, PlaidItem, Account, Transaction, Category
from sqlalchemy import text

def create_database():
    """Create the database if it doesn't exist."""
    # Get the database URL from environment or use default
    db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres@localhost:5432/manna')

    # Extract database name
    db_name = db_url.split('/')[-1].split('?')[0]

    # Connect to postgres database to create our database
    postgres_url = db_url.rsplit('/', 1)[0] + '/postgres'

    from sqlalchemy import create_engine
    postgres_engine = create_engine(postgres_url)

    try:
        with postgres_engine.connect() as conn:
            conn.execute(text("COMMIT"))  # Exit any transaction
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            if not result.fetchone():
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"✅ Created database: {db_name}")
            else:
                print(f"ℹ️  Database already exists: {db_name}")
    except Exception as e:
        print(f"⚠️  Could not create database (may already exist): {e}")
    finally:
        postgres_engine.dispose()

def seed_database():
    """Seed the database with test data."""
    session = SessionLocal()

    try:
        # Create test user with specific ID for Plaid testing
        test_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        existing_user = session.query(User).filter(User.id == test_user_id).first()

        if not existing_user:
            test_user = User(
                id=test_user_id,
                email="test@example.com",
                username="testuser",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY3pp1dYDHIrV3.",  # "password"
                full_name="Test User",
                is_active=True,
                is_superuser=False
            )
            session.add(test_user)
            print(f"✅ Created test user with ID: {test_user_id}")
        else:
            test_user = existing_user
            print(f"ℹ️  Test user already exists with ID: {test_user_id}")

        # Create a sample institution
        institution = session.query(Institution).filter(
            Institution.plaid_institution_id == "ins_test"
        ).first()

        if not institution:
            institution = Institution(
                plaid_institution_id="ins_test",
                name="Test Bank",
                url="https://testbank.com",
                primary_color="#0066b2",
                logo_url="https://plaid.com/images/test-bank-logo.png"
            )
            session.add(institution)
            session.flush()  # Flush to get the ID
            print("✅ Created test institution")
        else:
            print("ℹ️  Test institution already exists")

        # Create sample categories
        categories_data = [
            {"name": "Food & Dining", "parent_category": "Expenses", "description": "Restaurant and grocery expenses", "color": "#FF6B6B"},
            {"name": "Transportation", "parent_category": "Expenses", "description": "Gas, public transit, rideshare", "color": "#4ECDC4"},
            {"name": "Shopping", "parent_category": "Expenses", "description": "Retail and online shopping", "color": "#45B7D1"},
            {"name": "Income", "parent_category": None, "description": "Salary, freelance, and other income", "color": "#95E77E"},
            {"name": "Transfer", "parent_category": None, "description": "Account transfers", "color": "#FFA07A"},
        ]

        for cat_data in categories_data:
            category = session.query(Category).filter(
                Category.name == cat_data["name"]
            ).first()

            if not category:
                category = Category(**cat_data)
                session.add(category)
                print(f"✅ Created category: {cat_data['name']}")

        # Create sample Plaid item
        plaid_item = session.query(PlaidItem).filter(
            PlaidItem.user_id == test_user.id
        ).first()

        if not plaid_item:
            plaid_item = PlaidItem(
                user_id=test_user.id,
                institution_id=institution.id,
                plaid_item_id="test_item_id",
                access_token="test_access_token",
                is_active=True
            )
            session.add(plaid_item)
            session.flush()  # Flush to get the ID
            print("✅ Created test Plaid item")
        else:
            print("ℹ️  Test Plaid item already exists")

        # Create sample account
        account = session.query(Account).filter(
            Account.user_id == test_user.id
        ).first()

        if not account:
            account = Account(
                user_id=test_user.id,
                plaid_item_id=plaid_item.id,
                plaid_account_id="test_account_id",
                name="Test Checking Account",
                official_name="Test Bank Checking",
                type="depository",
                subtype="checking",
                mask="1234",
                current_balance_cents=500000,  # $5000.00 in cents
                available_balance_cents=450000,  # $4500.00 in cents
                iso_currency_code="USD",
                is_active=True
            )
            session.add(account)
            print("✅ Created test account")
        else:
            print("ℹ️  Test account already exists")

        # Commit all changes
        session.commit()
        print("\n✅ Database seeded successfully!")

    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def main():
    """Main setup function."""
    print("🚀 Setting up local database for Manna Financial Platform\n")

    # Check for DATABASE_URL environment variable
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ℹ️  No DATABASE_URL found in environment, using default:")
        print("   postgresql://postgres@localhost:5432/manna")
        print("\n   To use a different database, set the DATABASE_URL environment variable:")
        print("   export DATABASE_URL=postgresql://username:password@localhost:5432/dbname\n")
    else:
        print(f"📍 Using database URL from environment: {db_url}\n")

    # Create database if needed
    create_database()

    # Initialize tables
    print("\n📊 Creating database tables...")
    try:
        init_db()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return 1

    # Seed database
    print("\n🌱 Seeding database with test data...")
    seed_database()

    print("\n🎉 Setup complete! You can now:")
    print("   1. Update your .env file with the DATABASE_URL if needed")
    print("   2. Run the backend: cd packages/backend && uvicorn src.main:app --reload")
    print("   3. Run the frontend: cd packages/frontend && pnpm dev")
    print("\n📝 Test user credentials:")
    print("   Email: test@example.com")
    print("   Password: password")
    print("   User ID: 00000000-0000-0000-0000-000000000001")

    return 0

if __name__ == "__main__":
    sys.exit(main())