#!/usr/bin/env python3
"""
Create admin user for Manna Financial Platform
This script creates a single admin user with known credentials
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, "/app")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from datetime import datetime
import uuid

# Import models
from models.user import User
from models.database import Base

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://manna:manna@localhost:5432/manna_dev"
)

def create_admin_user():
    """Create the admin user with known credentials."""
    
    # Create database engine
    engine = create_engine(DATABASE_URL)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        existing_user = db.query(User).filter(User.email == "admin@manna.com").first()
        
        if existing_user:
            print("❌ Admin user already exists!")
            print(f"   Email: admin@manna.com")
            print(f"   User ID: {existing_user.id}")
            
            # Update password if user exists
            response = input("Do you want to reset the password? (y/n): ")
            if response.lower() == 'y':
                existing_user.password_hash = pwd_context.hash("MannaAdmin2024!")
                existing_user.updated_at = datetime.utcnow()
                db.commit()
                print("✅ Password has been reset to: MannaAdmin2024!")
            return
        
        # Create new admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            email="admin@manna.com",
            password_hash=pwd_context.hash("MannaAdmin2024!"),
            first_name="Admin",
            last_name="User",
            is_active=True,
            is_verified=True,
            is_admin=True,  # Set as admin
            business_name="Manna Financial LLC",
            business_type="llc",
            business_ein="12-3456789",  # Sample EIN
            timezone="America/Los_Angeles",
            phone="+1-555-0100",
            address_line1="123 Financial Plaza",
            address_line2="Suite 100",
            address_city="San Francisco",
            address_state="CA",
            address_postal_code="94105",
            address_country="USA",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login=None,
            email_verified_at=datetime.utcnow(),
            notification_preferences={
                "email": True,
                "sms": False,
                "push": True,
                "transaction_alerts": True,
                "weekly_summary": True,
                "monthly_reports": True
            },
            settings={
                "dashboard_layout": "default",
                "theme": "light",
                "currency": "USD",
                "fiscal_year_start": "january",
                "date_format": "MM/DD/YYYY"
            }
        )
        
        # Add and commit
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print("\n" + "="*50)
        print("🔐 ADMIN CREDENTIALS")
        print("="*50)
        print(f"Email:    admin@manna.com")
        print(f"Password: MannaAdmin2024!")
        print(f"User ID:  {admin_user.id}")
        print("="*50)
        print("\n⚠️  IMPORTANT: Change this password after first login!")
        print("📝 These credentials are for development only.")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creating Manna Admin User...")
    create_admin_user()
    print("\n✨ Done!")