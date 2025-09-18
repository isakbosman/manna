#!/usr/bin/env python3

"""Debug script to test Plaid API integration directly."""

import sys
import os
sys.path.insert(0, '.')

from src.services.plaid_service import plaid_service
from src.config import settings
import asyncio

async def test_plaid_sync():
    """Test Plaid sync directly."""

    # Test access token from database
    access_token = "access-sandbox-5f5dae9b-0c1a-416c-a22b-d663105062c4"

    print(f"Testing Plaid sync with:")
    print(f"  Environment: {settings.plaid_environment}")
    print(f"  Client ID: {settings.plaid_client_id}")
    print(f"  Secret: {settings.plaid_secret[:10]}..." if settings.plaid_secret else "None")
    print(f"  Access Token: {access_token}")

    try:
        # Test sync without cursor first
        print("\n1. Testing sync without cursor (initial sync)...")
        result = await plaid_service.sync_transactions(access_token, cursor=None)
        print(f"Success! Added: {len(result['added'])}, Modified: {len(result['modified'])}, Removed: {len(result['removed'])}")

        # Test with cursor if available
        if result.get('next_cursor'):
            print(f"\n2. Testing sync with cursor: {result['next_cursor'][:20]}...")
            result2 = await plaid_service.sync_transactions(access_token, cursor=result['next_cursor'])
            print(f"Success! Added: {len(result2['added'])}, Modified: {len(result2['modified'])}, Removed: {len(result2['removed'])}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_plaid_sync())