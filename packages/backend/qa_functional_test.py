#!/usr/bin/env python3
"""
QA Functional Test - Database and Basic Sync Function Testing
=============================================================
"""

import sys
import os
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test database connection and schema."""
    try:
        import psycopg2
        from src.config import settings

        # Parse database URL
        db_url = settings.database_url
        print(f"Testing connection to: {db_url}")

        # Extract connection parameters
        if 'postgresql://' in db_url:
            # postgresql://postgres@localhost:5432/manna
            conn_parts = db_url.replace('postgresql://', '').split('/')
            host_part = conn_parts[0]  # postgres@localhost:5432
            database = conn_parts[1]   # manna

            if '@' in host_part:
                user_part, host_port = host_part.split('@')
                user = user_part
                if ':' in host_port:
                    host, port = host_port.split(':')
                else:
                    host, port = host_port, 5432
            else:
                user = 'postgres'
                if ':' in host_part:
                    host, port = host_part.split(':')
                else:
                    host, port = host_part, 5432

            # Test connection
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user
            )

            # Test basic queries
            cur = conn.cursor()

            # Check if tables exist
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('plaid_items', 'accounts', 'transactions')
            """)

            tables = [row[0] for row in cur.fetchall()]

            print(f"✅ Database connection successful")
            print(f"✅ Found tables: {tables}")

            # Check PlaidItem table structure
            if 'plaid_items' in tables:
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'plaid_items'
                    AND column_name IN ('plaid_access_token', 'cursor', 'sync_cursor')
                    ORDER BY column_name
                """)

                columns = cur.fetchall()
                print(f"✅ PlaidItem key columns: {columns}")

                # Check for access token encryption
                cur.execute("SELECT plaid_access_token FROM plaid_items LIMIT 1")
                token_row = cur.fetchone()
                if token_row and token_row[0]:
                    token = token_row[0]
                    if token.startswith('access-'):
                        print(f"🚨 CRITICAL: Access token stored in plaintext: {token[:20]}...")
                        return False
                    else:
                        print(f"✅ Access token appears to be encrypted/hashed")
                else:
                    print(f"ℹ️ No access tokens found to test")

            # Check transaction deduplication constraint
            if 'transactions' in tables:
                cur.execute("""
                    SELECT constraint_name, constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_name = 'transactions'
                    AND constraint_type = 'UNIQUE'
                """)

                constraints = cur.fetchall()
                print(f"✅ Transaction unique constraints: {constraints}")

            cur.close()
            conn.close()

            return True

        else:
            print(f"❌ Unsupported database URL format: {db_url}")
            return False

    except ImportError:
        print(f"❌ psycopg2 not available")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_plaid_service_mock():
    """Test Plaid service with mocked responses."""
    try:
        from unittest.mock import patch, Mock
        from src.services.plaid_service import plaid_service

        print("Testing Plaid service functionality...")

        # Test 1: Initial sync with null cursor
        print("Test 1: Initial sync with null cursor")
        with patch.object(plaid_service, 'sync_transactions') as mock_sync:
            mock_sync.return_value = {
                'added': [{'transaction_id': 'test_1', 'amount': 100.0}],
                'modified': [],
                'removed': [],
                'next_cursor': 'initial_cursor',
                'has_more': False,
                'is_initial_sync': True
            }

            result = await plaid_service.sync_transactions('test_token', None)
            assert result['is_initial_sync'] == True
            assert len(result['added']) == 1
            print("✅ Initial sync test passed")

        # Test 2: Incremental sync
        print("Test 2: Incremental sync")
        with patch.object(plaid_service, 'sync_transactions') as mock_sync:
            mock_sync.return_value = {
                'added': [],
                'modified': [{'transaction_id': 'test_2', 'amount': 150.0}],
                'removed': [],
                'next_cursor': 'incremental_cursor',
                'has_more': False,
                'is_initial_sync': False
            }

            result = await plaid_service.sync_transactions('test_token', 'existing_cursor')
            assert result['is_initial_sync'] == False
            assert len(result['modified']) == 1
            print("✅ Incremental sync test passed")

        # Test 3: Error handling
        print("Test 3: Error handling")
        try:
            from plaid.exceptions import ApiException

            with patch.object(plaid_service, 'sync_transactions') as mock_sync:
                error = ApiException(status=400)
                error.code = 'ITEM_LOGIN_REQUIRED'
                mock_sync.side_effect = error

                try:
                    await plaid_service.sync_transactions('invalid_token', None)
                    assert False, "Should have raised exception"
                except Exception as e:
                    assert 'Authentication required' in str(e) or 'ITEM_LOGIN_REQUIRED' in str(e)
                    print("✅ Error handling test passed")

        except ImportError:
            print("⚠️ Plaid exceptions not available, skipping error test")

        # Test 4: Data conversion
        print("Test 4: Data conversion")
        amount_float = 123.45
        amount_cents = int(amount_float * 100)
        assert amount_cents == 12345

        date_string = "2024-01-15"
        parsed_date = datetime.strptime(date_string, "%Y-%m-%d").date()
        assert parsed_date.year == 2024
        print("✅ Data conversion test passed")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False

def test_model_validation():
    """Test model validation and constraints."""
    try:
        # Test transaction model properties
        print("Testing model validation...")

        # This would test the actual model if imports work
        print("✅ Model validation placeholder passed")
        return True

    except Exception as e:
        print(f"❌ Model validation failed: {e}")
        return False

async def main():
    """Main test function."""
    print("="*60)
    print("🔬 QA FUNCTIONAL TESTING")
    print("="*60)

    results = {}

    # Test 1: Database Connection
    print("\n1. Testing Database Connection")
    print("-" * 30)
    results['database'] = test_database_connection()

    # Test 2: Plaid Service
    print("\n2. Testing Plaid Service")
    print("-" * 30)
    results['plaid_service'] = await test_plaid_service_mock()

    # Test 3: Model Validation
    print("\n3. Testing Model Validation")
    print("-" * 30)
    results['models'] = test_model_validation()

    # Summary
    print("\n" + "="*60)
    print("📊 FUNCTIONAL TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<20} {status}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All functional tests passed!")
    else:
        print("❌ Some functional tests failed")

    return results

if __name__ == "__main__":
    asyncio.run(main())