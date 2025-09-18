#!/usr/bin/env python
"""Test sync by directly calling the function."""

import asyncio
import sys
from datetime import datetime
from src.database import SessionLocal
from src.database.models import User, PlaidItem, Account, Transaction
from src.routers.plaid import sync_all_transactions, SyncTransactionsRequest

async def test_direct_sync():
    """Test the sync function directly."""
    db = SessionLocal()

    print("Starting direct sync test...")
    sys.stdout.flush()

    try:
        # Get the default user
        user = db.query(User).filter(User.id == "00000000-0000-0000-0000-000000000001").first()

        if not user:
            print("❌ Default user not found")
            return

        print(f"✅ Found user: {user.email}")

        # Create request object
        request = SyncTransactionsRequest(account_ids=None)

        # Call the sync function directly
        print("📞 Calling sync_all_transactions...")
        result = await sync_all_transactions(
            request=request,
            current_user=user,
            db=db
        )

        print(f"✅ Result: {result}")

        # Check transaction count
        total = db.query(Transaction).count()
        print(f"📊 Total transactions in database: {total}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_direct_sync())