#!/usr/bin/env python
"""
Test Plaid sync directly.
"""

import asyncio
import sys
sys.path.insert(0, '.')

from src.database import SessionLocal
from src.database.models import PlaidItem, Account, Transaction
from src.routers.plaid import sync_plaid_item_transactions

async def test_sync():
    db = SessionLocal()

    try:
        # Get PlaidItem
        plaid_item = db.query(PlaidItem).first()
        if not plaid_item:
            print("No PlaidItem found")
            return

        print(f"Testing sync for PlaidItem {plaid_item.id}")
        print(f"  Current cursor: {repr(plaid_item.cursor)}")
        print(f"  Access token present: {bool(plaid_item.access_token)}")

        # Call the sync function directly
        result = await sync_plaid_item_transactions(
            plaid_item=plaid_item,
            db=db,
            user_id=str(plaid_item.user_id)
        )

        print("\nSync result:")
        print(f"  Synced count: {result['synced_count']}")
        print(f"  New transactions: {result['new_transactions']}")
        print(f"  Modified: {result['modified_transactions']}")
        print(f"  Removed: {result['removed_transactions']}")

        # Commit changes
        db.commit()

        # Check actual transaction count
        accounts = db.query(Account).filter(Account.plaid_item_id == plaid_item.id).all()
        total_txns = 0
        for acc in accounts:
            txn_count = db.query(Transaction).filter(Transaction.account_id == acc.id).count()
            total_txns += txn_count

        print(f"\nTotal transactions in database: {total_txns}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_sync())
