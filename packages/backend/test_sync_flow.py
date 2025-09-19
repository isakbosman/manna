#!/usr/bin/env python3
"""
Test the actual sync flow to identify where it's failing
"""

import sys
import os
sys.path.insert(0, '.')

import asyncio
from src.database import SessionLocal
from src.database.models import PlaidItem, Account, Transaction
from src.services.plaid_service import plaid_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sync_flow():
    """Test the sync flow to identify issues."""
    print("=== Testing Plaid Sync Flow ===\n")

    db = SessionLocal()
    try:
        # 1. Check if there are any PlaidItems in the database
        plaid_items = db.query(PlaidItem).filter(PlaidItem.is_active == True).all()
        print(f"1. Found {len(plaid_items)} active PlaidItems in database")

        if not plaid_items:
            print("   No active PlaidItems found. Accounts need to be linked first.")
            return

        for i, item in enumerate(plaid_items, 1):
            print(f"\n2. Testing PlaidItem {i}:")
            print(f"   ID: {item.id}")
            print(f"   Plaid Item ID: {item.plaid_item_id}")
            print(f"   Status: {item.status}")
            print(f"   Has cursor: {bool(item.cursor)}")
            print(f"   Last sync attempt: {item.last_sync_attempt}")
            print(f"   Last successful sync: {item.last_successful_sync}")
            print(f"   Error: {item.error_code} - {item.error_message}")

            # Check accounts
            accounts = db.query(Account).filter(Account.plaid_item_id == item.id).all()
            print(f"   Linked accounts: {len(accounts)}")

            # Check transactions
            if accounts:
                account_ids = [acc.id for acc in accounts]
                txn_count = db.query(Transaction).filter(Transaction.account_id.in_(account_ids)).count()
                print(f"   Total transactions: {txn_count}")

            # Test access token decryption
            try:
                access_token = item.get_decrypted_access_token()
                print(f"   Access token available: {bool(access_token)}")
                if access_token:
                    print(f"   Access token (masked): {access_token[:20]}...{access_token[-10:]}")
            except Exception as e:
                print(f"   Access token error: {e}")

            # Test sync
            if item.status == 'active' and hasattr(item, 'get_decrypted_access_token'):
                print(f"\n3. Testing sync for PlaidItem {item.id}...")
                try:
                    # Use the secure sync method
                    result = await plaid_service.sync_transactions_secure(
                        session=db,
                        plaid_item=item,
                        count=10  # Small count for testing
                    )
                    print(f"   Sync successful!")
                    print(f"   Added: {len(result.get('added', []))}")
                    print(f"   Modified: {len(result.get('modified', []))}")
                    print(f"   Removed: {len(result.get('removed', []))}")
                    print(f"   Has more: {result.get('has_more', False)}")

                except Exception as e:
                    print(f"   Sync failed: {e}")
                    logger.error(f"Sync error details: {e}", exc_info=True)

    except Exception as e:
        print(f"Database error: {e}")
        logger.error(f"Database error details: {e}", exc_info=True)

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_sync_flow())