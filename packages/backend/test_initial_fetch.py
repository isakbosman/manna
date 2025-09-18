#!/usr/bin/env python
"""Test initial transaction fetch for Plaid items."""

import asyncio
from src.database import SessionLocal
from src.database.models import User, PlaidItem, Account, Transaction
from src.services.plaid_service import plaid_service
from datetime import datetime, timedelta

async def test_initial_fetch():
    """Test fetching initial transactions."""
    db = SessionLocal()

    try:
        # Get the valid plaid item
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.id == "49a6fc1f-2f24-43b6-8afe-53c733732af4"
        ).first()

        if not plaid_item:
            print("❌ Plaid item not found")
            return

        print(f"✅ Testing with Plaid item: {plaid_item.id}")
        print(f"   Access token: {plaid_item.access_token[:20]}...")

        # Try to get transactions using the regular get_transactions method (not sync)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days

        try:
            result = await plaid_service.get_transactions(
                access_token=plaid_item.access_token,
                start_date=start_date,
                end_date=end_date,
                count=100,
                offset=0
            )

            print(f"✅ get_transactions API call successful!")
            print(f"   Total transactions available: {result.get('total_transactions', 0)}")
            print(f"   Transactions returned: {len(result.get('transactions', []))}")

            transactions = result.get('transactions', [])
            if transactions:
                print(f"\n   Sample transactions:")
                for i, txn in enumerate(transactions[:5]):
                    print(f"     {i+1}. {txn['name']}: ${txn['amount']} on {txn['date']}")
            else:
                print("   ❌ No transactions in date range")

        except Exception as e:
            print(f"   ❌ get_transactions error: {e}")

        # Also try without cursor (start fresh sync)
        try:
            print(f"\n🔄 Testing sync without cursor (fresh start)")
            sync_result = await plaid_service.sync_transactions(
                plaid_item.access_token,
                cursor=None  # Start fresh
            )

            print(f"   ✅ Sync API call successful!")
            print(f"   Added: {len(sync_result.get('added', []))}")
            print(f"   Modified: {len(sync_result.get('modified', []))}")
            print(f"   Removed: {len(sync_result.get('removed', []))}")

            added = sync_result.get('added', [])
            if added:
                print(f"\n   Sample fresh transactions:")
                for i, txn in enumerate(added[:5]):
                    print(f"     {i+1}. {txn['name']}: ${txn['amount']} on {txn['date']}")

        except Exception as e:
            print(f"   ❌ Fresh sync error: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_initial_fetch())