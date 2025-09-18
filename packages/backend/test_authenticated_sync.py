#!/usr/bin/env python
"""Test sync with authentication by directly calling the function."""

import asyncio
from datetime import datetime
from src.database import SessionLocal
from src.database.models import User, PlaidItem, Account, Transaction
from src.routers.plaid import sync_all_transactions
from pydantic import BaseModel

class MockRequest(BaseModel):
    account_ids: None = None

async def test_authenticated_sync():
    """Test the sync endpoint with proper authentication."""
    db = SessionLocal()

    try:
        # Get the default user
        user = db.query(User).filter(User.id == "00000000-0000-0000-0000-000000000001").first()

        if not user:
            print("❌ Default user not found")
            return

        print(f"✅ Found user: {user.email}")

        # Check plaid items
        plaid_items = db.query(PlaidItem).filter(
            PlaidItem.user_id == user.id,
            PlaidItem.is_active == True
        ).all()

        print(f"✅ Found {len(plaid_items)} active Plaid items")
        for item in plaid_items:
            print(f"   - Item {item.id}: cursor = {item.cursor}")

        # Create request object
        request = MockRequest()

        # Call the sync function directly with authenticated user
        print("\n🔄 Calling sync_all_transactions...")
        result = await sync_all_transactions(
            request=request,
            current_user=user,
            db=db
        )

        print(f"\n✅ Sync result: {result}")

        # Check transaction count
        total_transactions = db.query(Transaction).count()
        print(f"📊 Total transactions in database: {total_transactions}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_authenticated_sync())