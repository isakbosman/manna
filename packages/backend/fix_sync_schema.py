#!/usr/bin/env python3
"""
Comprehensive script to fix Plaid sync schema issues.

This script:
1. Analyzes the current database schema
2. Identifies missing columns required for sync
3. Generates SQL to fix the schema
4. Provides instructions for applying the fix
"""

import sys
import os
sys.path.insert(0, '.')

from sqlalchemy import create_engine, text, inspect
from src.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_schema_issues():
    """Analyze current schema and identify issues."""

    print("=== Plaid Sync Schema Analysis ===\n")

    # Expected columns for plaid_items table based on the model
    expected_columns = {
        'id': 'UUID PRIMARY KEY',
        'user_id': 'UUID NOT NULL',
        'institution_id': 'UUID',
        'plaid_item_id': 'VARCHAR(255) UNIQUE NOT NULL',
        'plaid_access_token': 'VARCHAR(765) NOT NULL',  # Encrypted field is larger
        'status': 'VARCHAR(20) DEFAULT \'active\' NOT NULL',
        'error_code': 'VARCHAR(50)',
        'error_message': 'TEXT',
        'available_products': 'JSONB',
        'billed_products': 'JSONB',
        'webhook_url': 'VARCHAR(500)',
        'consent_expiration_time': 'TIMESTAMP WITH TIME ZONE',
        'last_successful_sync': 'TIMESTAMP WITH TIME ZONE',
        'last_sync_attempt': 'TIMESTAMP WITH TIME ZONE',  # CRITICAL for sync
        'cursor': 'VARCHAR(255)',  # CRITICAL for sync
        'max_days_back': 'INTEGER DEFAULT 730',
        'sync_frequency_hours': 'INTEGER DEFAULT 6',
        'is_active': 'BOOLEAN DEFAULT true NOT NULL',
        'requires_reauth': 'BOOLEAN DEFAULT false',
        'has_mfa': 'BOOLEAN DEFAULT false',
        'update_type': 'VARCHAR(20)',
        'extra_data': 'JSONB',
        'created_at': 'TIMESTAMP WITH TIME ZONE NOT NULL',
        'updated_at': 'TIMESTAMP WITH TIME ZONE NOT NULL',
        'version': 'INTEGER DEFAULT 1 NOT NULL'
    }

    # Critical columns that MUST exist for sync to work
    critical_columns = {
        'last_sync_attempt': 'TIMESTAMP WITH TIME ZONE',
        'cursor': 'VARCHAR(255)',
        'status': 'VARCHAR(20) DEFAULT \'active\' NOT NULL',
        'error_code': 'VARCHAR(50)',
        'error_message': 'TEXT',
        'requires_reauth': 'BOOLEAN DEFAULT false'
    }

    print("1. Expected schema for plaid_items table:")
    for col, col_type in expected_columns.items():
        is_critical = "🔥 CRITICAL" if col in critical_columns else ""
        print(f"   {col}: {col_type} {is_critical}")

    print("\n2. Database connection test:")
    try:
        # Try to connect to database
        engine = create_engine(settings.database_url)

        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT version()"))
            db_version = result.scalar()
            print(f"   ✅ Connected to PostgreSQL: {db_version[:50]}...")

            # Check if plaid_items table exists
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            if 'plaid_items' not in tables:
                print(f"   ❌ plaid_items table does not exist!")
                print(f"   📋 Available tables: {tables}")
                return generate_create_table_sql(expected_columns)
            else:
                print(f"   ✅ plaid_items table exists")

                # Check columns
                columns = inspector.get_columns('plaid_items')
                existing_columns = {col['name']: str(col['type']) for col in columns}

                print(f"\n3. Existing columns in plaid_items:")
                for col_name, col_type in existing_columns.items():
                    print(f"   {col_name}: {col_type}")

                print(f"\n4. Missing columns analysis:")
                missing_columns = []
                for col_name, col_def in critical_columns.items():
                    if col_name not in existing_columns:
                        missing_columns.append((col_name, col_def))
                        print(f"   ❌ MISSING: {col_name} ({col_def})")
                    else:
                        print(f"   ✅ EXISTS: {col_name}")

                if missing_columns:
                    print(f"\n5. 🔥 CRITICAL ISSUE FOUND:")
                    print(f"   {len(missing_columns)} critical columns are missing!")
                    print(f"   This explains why Plaid sync is not working.")
                    return generate_alter_table_sql(missing_columns)
                else:
                    print(f"\n5. ✅ All critical columns exist!")
                    print(f"   Schema appears correct for sync functionality.")
                    return None

    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        print(f"\n🛠️  Database connection issues detected.")
        print(f"   This may be why sync is failing.")
        print(f"   Please check:")
        print(f"   1. PostgreSQL is running")
        print(f"   2. Database exists and is accessible")
        print(f"   3. Connection settings in environment variables")
        return None

def generate_alter_table_sql(missing_columns):
    """Generate SQL to add missing columns."""

    print(f"\n6. 🛠️  GENERATED FIX:")
    print(f"   The following SQL will add the missing columns:")
    print(f"   ")

    sql_statements = []

    for col_name, col_def in missing_columns:
        sql = f"ALTER TABLE plaid_items ADD COLUMN {col_name} {col_def};"
        sql_statements.append(sql)
        print(f"   {sql}")

    # Add indexes for performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_plaid_items_sync_status ON plaid_items(status, last_sync_attempt);",
        "CREATE INDEX IF NOT EXISTS idx_plaid_items_cursor ON plaid_items(cursor) WHERE cursor IS NOT NULL;",
        "CREATE INDEX IF NOT EXISTS idx_plaid_items_reauth ON plaid_items(requires_reauth, is_active);"
    ]

    print(f"\n   -- Performance indexes:")
    for idx_sql in indexes:
        sql_statements.append(idx_sql)
        print(f"   {idx_sql}")

    # Add constraints
    constraints = [
        "ALTER TABLE plaid_items ADD CONSTRAINT ck_plaid_item_status CHECK (status IN ('active', 'error', 'expired', 'revoked', 'pending'));"
    ]

    print(f"\n   -- Constraints:")
    for constraint_sql in constraints:
        sql_statements.append(constraint_sql)
        print(f"   {constraint_sql}")

    return sql_statements

def generate_create_table_sql(expected_columns):
    """Generate SQL to create the entire table."""
    print(f"\n6. 🛠️  TABLE CREATION REQUIRED:")
    print(f"   plaid_items table does not exist. Full table creation needed.")
    print(f"   This indicates migrations have not been run.")
    return None

def main():
    """Main analysis function."""
    sql_fixes = analyze_schema_issues()

    if sql_fixes:
        print(f"\n7. 📝 INSTRUCTIONS TO FIX:")
        print(f"   1. Connect to your PostgreSQL database")
        print(f"   2. Run the SQL statements above")
        print(f"   3. Test the sync functionality")
        print(f"   ")
        print(f"   Or save to a file and run:")

        # Save SQL to file
        with open('fix_plaid_schema.sql', 'w') as f:
            f.write("-- Fix for Plaid sync schema issues\\n")
            f.write("-- Generated by fix_sync_schema.py\\n\\n")
            for sql in sql_fixes:
                f.write(sql + "\\n")

        print(f"   📁 SQL saved to: fix_plaid_schema.sql")
        print(f"   💾 Run: psql -d your_database < fix_plaid_schema.sql")

    print(f"\n8. 🔍 NEXT STEPS:")
    print(f"   After fixing schema:")
    print(f"   1. Test account linking via /exchange-public-token")
    print(f"   2. Check if fetch_initial_transactions is called")
    print(f"   3. Monitor logs for sync errors")
    print(f"   4. Verify transactions appear in database")

if __name__ == "__main__":
    main()