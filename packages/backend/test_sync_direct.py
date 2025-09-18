#!/usr/bin/env python
"""Direct test of transaction sync functionality."""

import asyncio
from src.database import SessionLocal
from src.database.models import User, PlaidItem, Account, Transaction
from src.services.plaid_service import plaid_service
from datetime import datetime

async def test_sync_direct():
    """Test syncing transactions directly."""
    db = SessionLocal()

    try:
        # Get the user
        user = db.query(User).filter(User.id == "00000000-0000-0000-0000-000000000001").first()
        if not user:
            print("❌ Default user not found")
            return

        print(f"✅ Found user: {user.email}")

        # Get plaid items for this user
        plaid_items = db.query(PlaidItem).filter(
            PlaidItem.user_id == user.id,
            PlaidItem.is_active == True
        ).all()

        print(f"✅ Found {len(plaid_items)} active Plaid items")

        for plaid_item in plaid_items:
            print(f"\n🔄 Testing sync for Plaid item: {plaid_item.id}")
            print(f"   Access token: {plaid_item.access_token[:20]}...")
            print(f"   Cursor: {plaid_item.cursor}")

            try:
                # Call the Plaid service directly
                sync_result = await plaid_service.sync_transactions(
                    plaid_item.access_token,
                    plaid_item.cursor
                )

                print(f"   ✅ Plaid API call successful!")
                print(f"   Added: {len(sync_result.get('added', []))}")
                print(f"   Modified: {len(sync_result.get('modified', []))}")
                print(f"   Removed: {len(sync_result.get('removed', []))}")
                print(f"   Has more: {sync_result.get('has_more', False)}")
                print(f"   Next cursor: {sync_result.get('next_cursor', 'None')}")

                # Show first few transactions
                added = sync_result.get('added', [])
                if added:
                    print(f"\n   First few transactions:")
                    for i, txn in enumerate(added[:3]):
                        print(f"     {i+1}. {txn['name']}: ${txn['amount']} on {txn['date']}")
                else:
                    print("   ❌ No transactions returned from Plaid API")

            except Exception as e:
                print(f"   ❌ Plaid API error: {e}")

        # Check current transaction count
        total_transactions = db.query(Transaction).count()
        print(f"\n📊 Current transactions in database: {total_transactions}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_sync_direct())