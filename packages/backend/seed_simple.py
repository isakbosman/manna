#!/usr/bin/env python
"""Simple script to seed the database with test user."""

import sys
import os
import uuid
from datetime import datetime

# Add the backend package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import SessionLocal, init_db
from src.database.models import User

def main():
    """Create a test user in the database."""
    print("Initializing database...")
    init_db()

    print("Creating test user...")
    try:
        session = SessionLocal()

        # Check if test user already exists
        test_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        existing_user = session.query(User).filter(User.id == test_user_id).first()

        if existing_user:
            print(f"Test user already exists with ID: {test_user_id}")
        else:
            # Create test user with specific ID
            test_user = User(
                id=test_user_id,
                email="test@example.com",
                username="testuser",
                hashed_password="$2b$12$sample_hash_for_testing",  # Not a real password hash
                full_name="Test User",
                is_active=True,
                is_superuser=False,
                created_at=datetime.utcnow()
            )
            session.add(test_user)
            session.commit()
            print(f"✓ Test user created with ID: {test_user_id}")

        # Also ensure we have a regular user for normal login
        regular_user = session.query(User).filter(User.email == "user@example.com").first()
        if not regular_user:
            regular_user = User(
                email="user@example.com",
                username="user",
                hashed_password="$2b$12$sample_hash_for_testing",  # Not a real password hash
                full_name="Regular User",
                is_active=True,
                is_superuser=False,
                created_at=datetime.utcnow()
            )
            session.add(regular_user)
            session.commit()
            print("✓ Regular user created")

        session.close()
        return 0
    except Exception as e:
        print(f"✗ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())