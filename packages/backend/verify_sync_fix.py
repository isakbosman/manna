#!/usr/bin/env python3
"""
Verify that the Plaid sync fix is working correctly.

This script:
1. Checks that all required columns exist
2. Tests the sync flow with actual accounts
3. Provides detailed diagnostics
"""

import sys
import os
sys.path.insert(0, '.')

import asyncio
from src.database import SessionLocal
from src.database.models import PlaidItem, Account, Transaction
from src.services.plaid_service import plaid_service
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_sync_fix():
    """Verify that the sync fix is working."""

    print("=== Verifying Plaid Sync Fix ===\n")

    db = SessionLocal()
    try:
        # 1. Verify schema is correct
        print("1. Checking database schema...")

        # Check critical columns exist
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'plaid_items'
            AND column_name IN ('last_sync_attempt', 'status', 'error_code', 'error_message', 'requires_reauth')
            ORDER BY column_name
        """))

        schema_columns = {}
        for row in result:
            schema_columns[row[0]] = {
                'type': row[1],
                'nullable': row[2],
                'default': row[3]
            }

        required_columns = ['last_sync_attempt', 'status', 'error_code', 'error_message', 'requires_reauth']
        missing_columns = [col for col in required_columns if col not in schema_columns]

        if missing_columns:
            print(f"   ❌ Missing columns: {missing_columns}")
            print(f"   🛠️  Please run the SQL fix first!")
            return False
        else:
            print(f"   ✅ All required columns exist")
            for col in required_columns:
                details = schema_columns[col]
                print(f"      {col}: {details['type']} (nullable: {details['nullable']})")

        # 2. Check for existing PlaidItems
        print(f"\n2. Checking existing PlaidItems...")
        plaid_items = db.query(PlaidItem).all()
        print(f"   Found {len(plaid_items)} PlaidItems in database")

        if not plaid_items:
            print(f"   ℹ️  No PlaidItems found. Accounts need to be linked first.")
            print(f"   🔗 Use the frontend to link accounts via Plaid Link")
            return True

        # 3. Test sync functionality for each item
        success_count = 0
        for i, item in enumerate(plaid_items, 1):
            print(f"\n3.{i} Testing PlaidItem {item.id}:")
            print(f"      Plaid Item ID: {item.plaid_item_id}")
            print(f"      Status: {getattr(item, 'status', 'NOT SET')}")
            print(f"      Last sync attempt: {getattr(item, 'last_sync_attempt', 'NOT SET')}")
            print(f"      Has cursor: {bool(getattr(item, 'cursor', None))}")
            print(f"      Is active: {item.is_active}")
            print(f"      Requires reauth: {getattr(item, 'requires_reauth', 'NOT SET')}")

            # Check accounts
            accounts = db.query(Account).filter(Account.plaid_item_id == item.id).all()
            print(f"      Linked accounts: {len(accounts)}")

            # Check transactions
            if accounts:
                account_ids = [acc.id for acc in accounts]
                txn_count = db.query(Transaction).filter(Transaction.account_id.in_(account_ids)).count()
                print(f"      Existing transactions: {txn_count}")

            # Test sync
            if item.is_active:
                try:
                    print(f"      🔄 Testing sync...")

                    # Use the secure sync method with a small count for testing
                    result = await plaid_service.sync_transactions_secure(
                        session=db,
                        plaid_item=item,
                        count=10
                    )

                    print(f"      ✅ Sync successful!")
                    print(f"         Added: {len(result.get('added', []))}")
                    print(f"         Modified: {len(result.get('modified', []))}")
                    print(f"         Removed: {len(result.get('removed', []))}")
                    print(f"         Has more: {result.get('has_more', False)}")

                    success_count += 1

                    # Refresh item to see updated state
                    db.refresh(item)
                    print(f"      📊 Updated state:")
                    print(f"         Status: {getattr(item, 'status', 'NOT SET')}")
                    print(f"         Last sync attempt: {getattr(item, 'last_sync_attempt', 'NOT SET')}")
                    print(f"         Error: {getattr(item, 'error_code', None)} - {getattr(item, 'error_message', None)}")

                except Exception as e:
                    print(f"      ❌ Sync failed: {e}")
                    logger.error(f"Sync error for item {item.id}: {e}", exc_info=True)

                    # Check if the item was updated with error info
                    db.refresh(item)
                    print(f"      📊 Error state:")
                    print(f"         Status: {getattr(item, 'status', 'NOT SET')}")
                    print(f"         Error: {getattr(item, 'error_code', None)} - {getattr(item, 'error_message', None)}")
            else:
                print(f"      ⏸️  Item is inactive, skipping sync test")

        # 4. Summary
        print(f"\n4. Summary:")
        if missing_columns:
            print(f"   ❌ Schema issues found - apply SQL fix first")
            return False
        elif not plaid_items:
            print(f"   ✅ Schema is correct")
            print(f"   ℹ️  No accounts linked yet - use frontend to link accounts")
            return True
        else:
            print(f"   ✅ Schema is correct")
            print(f"   📊 Tested {len(plaid_items)} PlaidItems")
            print(f"   ✅ {success_count} items synced successfully")
            if success_count < len(plaid_items):
                print(f"   ⚠️  {len(plaid_items) - success_count} items had sync issues")
            return success_count == len(plaid_items)

    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        logger.error(f"Verification error: {e}", exc_info=True)
        return False
    finally:
        db.close()

async def main():
    """Main verification function."""
    success = await verify_sync_fix()

    print(f"\n=== Verification Result ===")
    if success:
        print(f"✅ Plaid sync fix verification PASSED")
        print(f"🎉 Transaction sync should now work correctly!")
        print(f"\nNext steps:")
        print(f"1. Link accounts using the frontend")
        print(f"2. Check that transactions are being fetched")
        print(f"3. Monitor the sync logs for any issues")
    else:
        print(f"❌ Plaid sync fix verification FAILED")
        print(f"🛠️  Please check the issues above and apply fixes")
        print(f"\nTroubleshooting:")
        print(f"1. Run the SQL fix: fix_plaid_schema_clean.sql")
        print(f"2. Check database connectivity")
        print(f"3. Verify Plaid API credentials")

if __name__ == "__main__":
    asyncio.run(main())