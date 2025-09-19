#!/usr/bin/env python
"""
Test Plaid transaction sync functionality.
"""

import asyncio
import sys
sys.path.insert(0, '.')

from src.database import SessionLocal
from src.database.models import PlaidItem, Account, Transaction
from src.services.plaid_service import plaid_service
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sync():
    """Test the Plaid sync functionality."""
    db = SessionLocal()

    try:
        # Get the first PlaidItem
        plaid_item = db.query(PlaidItem).first()
        if not plaid_item:
            print("❌ No PlaidItem found in database")
            return

        print(f"Testing sync for PlaidItem {plaid_item.id}")
        print(f"  Current cursor: {repr(plaid_item.cursor)}")
        print(f"  Last successful sync: {plaid_item.last_successful_sync}")

        # Get the access token (it should be encrypted in the database)
        # For now, use it directly since encryption may not be set up yet
        access_token = plaid_item.access_token

        print("\n1. Testing transaction sync...")
        try:
            # Try sync with current cursor (should be initial sync if cursor is None/empty)
            result = await plaid_service.sync_transactions(
                access_token=access_token,
                cursor=plaid_item.cursor,
                count=100
            )

            print(f"✓ Sync successful!")
            print(f"  - Added: {len(result.get('added', []))}")
            print(f"  - Modified: {len(result.get('modified', []))}")
            print(f"  - Removed: {len(result.get('removed', []))}")
            print(f"  - Has more: {result.get('has_more', False)}")
            print(f"  - Next cursor: {result.get('next_cursor', 'None')[:50]}...")

            # Process and save transactions
            if result.get('added'):
                print("\n2. Processing transactions...")
                added_count = 0

                for txn_data in result['added']:
                    # Find the account
                    account = db.query(Account).filter(
                        Account.plaid_account_id == txn_data['account_id']
                    ).first()

                    if account:
                        # Check if transaction already exists
                        existing = db.query(Transaction).filter(
                            Transaction.plaid_transaction_id == txn_data['transaction_id']
                        ).first()

                        if not existing:
                            # Convert amount to cents (Plaid returns amount in dollars)
                            amount_cents = int(txn_data['amount'] * 100)

                            transaction = Transaction(
                                account_id=account.id,
                                plaid_transaction_id=txn_data['transaction_id'],
                                amount_cents=amount_cents,
                                iso_currency_code=txn_data.get('iso_currency_code', 'USD'),
                                category=txn_data.get('category', []),  # Store as JSON
                                category_id=txn_data.get('category_id'),
                                date=txn_data['date'],
                                authorized_date=txn_data.get('authorized_date'),
                                name=txn_data['name'],
                                merchant_name=txn_data.get('merchant_name'),
                                payment_channel=txn_data.get('payment_channel'),
                                pending=txn_data.get('pending', False),
                                pending_transaction_id=txn_data.get('pending_transaction_id')
                            )
                            db.add(transaction)
                            added_count += 1

                # Update PlaidItem with new cursor and sync time
                if result.get('next_cursor'):
                    plaid_item.cursor = result['next_cursor']
                plaid_item.last_successful_sync = datetime.utcnow()
                plaid_item.last_sync_attempt = datetime.utcnow()

                db.commit()
                print(f"✓ Added {added_count} new transactions to database")

            else:
                print("\n2. No new transactions to add")
                # Still update sync timestamps
                plaid_item.last_sync_attempt = datetime.utcnow()
                if result.get('next_cursor'):
                    plaid_item.cursor = result['next_cursor']
                    plaid_item.last_successful_sync = datetime.utcnow()
                db.commit()

            # Verify transaction count
            total_txns = 0
            accounts = db.query(Account).filter(Account.plaid_item_id == plaid_item.id).all()
            for acc in accounts:
                txn_count = db.query(Transaction).filter(Transaction.account_id == acc.id).count()
                total_txns += txn_count
                if txn_count > 0:
                    print(f"  Account {acc.name}: {txn_count} transactions")

            print(f"\n✓ Total transactions in database: {total_txns}")

        except Exception as e:
            print(f"❌ Sync failed: {e}")
            import traceback
            traceback.print_exc()

            # Update error status
            plaid_item.last_sync_attempt = datetime.utcnow()
            plaid_item.error_code = "SYNC_ERROR"
            plaid_item.error_message = str(e)
            db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_sync())