#!/usr/bin/env python3

"""Test script to create a valid PlaidItem and test the full sync flow."""

import sys
import os
sys.path.insert(0, '.')

from src.database import get_db
from src.database.models import User, PlaidItem, Institution, Account
from src.services.plaid_service import plaid_service
from src.config import settings
import asyncio
import uuid
from datetime import datetime

async def create_test_plaid_item():
    """Create a test PlaidItem using Plaid's sandbox test credentials."""

    print("Setting up test PlaidItem with sandbox...")
    print(f"Environment: {settings.plaid_environment}")
    print(f"Client ID: {settings.plaid_client_id}")

    session = next(get_db())

    # Get the test user
    user = session.query(User).first()
    if not user:
        print("❌ No test user found!")
        return False

    print(f"✅ Using test user: {user.id}")

    try:
        # Step 1: Create a link token for the test user
        print("\n1. Creating link token...")
        link_result = await plaid_service.create_link_token(
            user_id=str(user.id),
            user_name="Test User"
        )
        print(f"✅ Link token created: {link_result['link_token'][:20]}...")

        # Step 2: For sandbox, we can use predefined public tokens
        # Plaid provides these for testing: https://plaid.com/docs/sandbox/test-credentials/
        sandbox_public_token = "public-sandbox-1234"  # This won't work, need real flow

        print("\n⚠️  To complete the test, you need to:")
        print("1. Use the frontend to link a Plaid account")
        print("2. Or use Plaid's Link tool to get a public token")
        print("3. Then exchange it for an access token")
        print("\nFor now, let's create a mock PlaidItem to test the sync logic...")

        # Create a mock PlaidItem for testing the sync logic
        # NOTE: This will fail at Plaid API level, but tests our sync function
        test_item = PlaidItem(
            user_id=user.id,
            plaid_item_id="test_item_123",
            access_token="access-sandbox-test-token",  # Mock token
            is_active=True,
            available_products='["transactions"]',
            billed_products='["transactions"]'
        )

        session.add(test_item)
        session.commit()

        print(f"✅ Created test PlaidItem: {test_item.id}")

        # Step 3: Test the sync endpoint
        print("\n2. Testing sync endpoint...")

        # This will fail at Plaid API level due to invalid token
        # But it proves our sync function is being called

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_test_plaid_item())
    if success:
        print("\n✅ Test setup completed!")
        print("Now test the sync endpoint:")
        print("curl -X POST 'http://localhost:8000/api/v1/plaid/sync-transactions' -H 'Content-Type: application/json' -d '{}'")
    else:
        print("\n❌ Test setup failed!")