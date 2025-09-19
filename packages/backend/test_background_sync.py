#!/usr/bin/env python3
"""
Test the background sync functionality that's triggered after account linking.

This script simulates what happens when fetch_initial_transactions is called
as a background task after exchange_public_token.
"""

import sys
import os
sys.path.insert(0, '.')

import asyncio
from src.database import SessionLocal
from src.database.models import PlaidItem, Account, Transaction
from src.routers.plaid import fetch_initial_transactions
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_background_sync():
    """Test the background sync that should happen after account linking."""

    print("=== Testing Background Sync Process ===\n")

    db = SessionLocal()
    try:
        # 1. Find a PlaidItem to test with
        plaid_items = db.query(PlaidItem).filter(PlaidItem.is_active == True).all()

        if not plaid_items:
            print("❌ No active PlaidItems found!")
            print("   Please link accounts first using the frontend")
            return

        item = plaid_items[0]
        print(f"1. Testing with PlaidItem:")
        print(f"   ID: {item.id}")
        print(f"   Plaid Item ID: {item.plaid_item_id}")
        print(f"   Status: {getattr(item, 'status', 'NOT SET')}")

        # Get accounts for this item
        accounts = db.query(Account).filter(Account.plaid_item_id == item.id).all()
        print(f"   Linked accounts: {len(accounts)}")

        if not accounts:
            print("❌ No accounts found for this item!")
            return

        # Check current transaction count
        account_ids = [acc.id for acc in accounts]
        current_txn_count = db.query(Transaction).filter(Transaction.account_id.in_(account_ids)).count()
        print(f"   Current transactions: {current_txn_count}")

        # 2. Get user_id for the item
        user_id = str(item.user_id)
        print(f"\n2. Simulating fetch_initial_transactions background task...")
        print(f"   User ID: {user_id}")

        # Get access token
        try:
            access_token = item.get_decrypted_access_token()
            print(f"   Access token available: {bool(access_token)}")
        except Exception as e:
            print(f"   ❌ Failed to get access token: {e}")
            return

        # 3. Call the background task function
        try:
            print(f"   🔄 Running fetch_initial_transactions...")
            await fetch_initial_transactions(
                plaid_item_id=str(item.id),
                access_token=access_token,
                user_id=user_id
            )
            print(f"   ✅ fetch_initial_transactions completed!")

        except Exception as e:
            print(f"   ❌ fetch_initial_transactions failed: {e}")
            logger.error(f"Background task error: {e}", exc_info=True)
            return

        # 4. Check results
        print(f"\n3. Checking results...")

        # Refresh the item
        db.refresh(item)
        print(f"   Status: {getattr(item, 'status', 'NOT SET')}")
        print(f"   Last sync: {getattr(item, 'last_successful_sync', 'NOT SET')}")
        print(f"   Last attempt: {getattr(item, 'last_sync_attempt', 'NOT SET')}")
        print(f"   Error: {getattr(item, 'error_code', None)} - {getattr(item, 'error_message', None)}")

        # Check new transaction count
        new_txn_count = db.query(Transaction).filter(Transaction.account_id.in_(account_ids)).count()
        added_txns = new_txn_count - current_txn_count
        print(f"   Transactions after sync: {new_txn_count}")
        print(f"   Newly added transactions: {added_txns}")

        if added_txns > 0:
            print(f"   ✅ Background sync is working! {added_txns} transactions added")

            # Show some sample transactions
            recent_txns = db.query(Transaction).filter(
                Transaction.account_id.in_(account_ids)
            ).order_by(Transaction.created_at.desc()).limit(5).all()

            print(f"\n   📊 Sample recent transactions:")
            for txn in recent_txns:
                amount = txn.amount_cents / 100 if txn.amount_cents else 0
                print(f"      ${amount:>8.2f} - {txn.name[:50]}")
                print(f"                 {txn.date} - {txn.primary_category or 'Uncategorized'}")

        elif getattr(item, 'error_code', None):
            print(f"   ⚠️  Sync completed but with errors")
            print(f"   Check error details above for troubleshooting")
        else:
            print(f"   ℹ️  No new transactions found (might be expected)")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test error: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_background_sync())