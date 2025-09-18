#!/usr/bin/env python
"""Standalone script to seed the database."""

import sys
import os

# Add the backend package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import SessionLocal, init_db
from seeds.seed_data import create_seed_data, clear_seed_data

def main():
    """Run the database seeding."""
    print("Initializing database...")
    init_db()

    print("Creating seed data...")
    try:
        with SessionLocal() as session:
            # Clear existing seed data first
            try:
                clear_seed_data(session)
            except Exception as e:
                print(f"Note: Could not clear existing data (this is normal for first run): {e}")

            # Create new seed data
            create_seed_data(session)

        print("✓ Database seeded successfully!")
        return 0
    except Exception as e:
        print(f"✗ Error seeding database: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())