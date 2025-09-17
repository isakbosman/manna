#!/usr/bin/env python3
"""
Simple script to create admin user directly in database
"""

import os
import uuid
from datetime import datetime
import psycopg2
from psycopg2.extras import Json
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database connection parameters
DB_PARAMS = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'manna_dev'),
    'user': os.getenv('DB_USER', 'manna'),
    'password': os.getenv('DB_PASSWORD', 'manna')
}

def create_admin_user():
    """Create admin user directly in the database."""
    
    conn = None
    cursor = None
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Check if admin user already exists
        cursor.execute("SELECT id, email FROM users WHERE email = %s", ('admin@manna.com',))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"❌ Admin user already exists with ID: {existing_user[0]}")
            response = input("Do you want to reset the password? (y/n): ")
            if response.lower() == 'y':
                # Update password
                new_password_hash = pwd_context.hash("MannaAdmin2024!")
                cursor.execute(
                    "UPDATE users SET hashed_password = %s, updated_at = %s WHERE email = %s",
                    (new_password_hash, datetime.utcnow(), 'admin@manna.com')
                )
                conn.commit()
                print("✅ Password reset successfully!")
            return
        
        # Create new admin user
        user_id = str(uuid.uuid4())
        password_hash = pwd_context.hash("MannaAdmin2024!")
        now = datetime.utcnow()
        
        # Insert user (matching actual database schema)
        insert_query = """
            INSERT INTO users (
                id, email, username, hashed_password, full_name,
                is_active, is_verified, is_superuser,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
        """
        
        values = (
            user_id, 
            'admin@manna.com',
            'admin',  # username
            password_hash,
            'Admin User',  # full_name
            True,  # is_active
            True,  # is_verified
            True,  # is_superuser (instead of is_admin)
            now,   # created_at
            now    # updated_at
        )
        
        cursor.execute(insert_query, values)
        conn.commit()
        
        print("✅ Admin user created successfully!")
        print("\n" + "="*50)
        print("🔐 ADMIN CREDENTIALS")
        print("="*50)
        print(f"Email:    admin@manna.com")
        print(f"Password: MannaAdmin2024!")
        print(f"User ID:  {user_id}")
        print("="*50)
        print("\n⚠️  IMPORTANT: Change this password after first login!")
        print("📝 These credentials are for development only.")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Creating Manna Admin User...")
    create_admin_user()
    print("\n✨ Done!")