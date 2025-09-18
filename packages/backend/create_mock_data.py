#!/usr/bin/env python3

"""Create mock data to demonstrate the sync endpoint functionality."""

import sys
import os
sys.path.insert(0, '.')

from src.database import get_db
from src.database.models import User, PlaidItem, Institution, Account
import uuid
from datetime import datetime

def create_mock_plaid_item():
    """Create a mock PlaidItem to demonstrate sync functionality."""

    session = next(get_db())

    # Get the test user
    user = session.query(User).first()
    if not user:
        print("❌ No test user found!")
        return False

    print(f"✅ Using test user: {user.id}")

    # Create a mock institution
    institution = Institution(
        plaid_institution_id="ins_sandbox_test",
        name="Sandbox Test Bank",
        url="https://sandbox.test.bank",
        primary_color="#0066cc",
        logo_url="https://example.com/logo.png"
    )
    session.add(institution)
    session.flush()

    # Create a mock PlaidItem with a valid-looking but fake access token
    # This will still fail at Plaid API level, but demonstrates the sync logic
    test_item = PlaidItem(
        user_id=user.id,
        institution_id=institution.id,
        plaid_item_id="test_item_sandbox_123",
        access_token="access-sandbox-demo-12345678-1234-1234-1234-123456789abc",
        is_active=True,
        available_products='["transactions"]',
        billed_products='["transactions"]'
    )

    session.add(test_item)
    session.flush()

    # Create mock accounts
    checking_account = Account(
        user_id=user.id,
        plaid_item_id=test_item.id,
        plaid_account_id="demo_checking_123",
        name="Demo Checking Account",
        type="depository",
        subtype="checking",
        mask="1234",
        current_balance_cents=125000,  # $1,250.00
        available_balance_cents=125000,
        iso_currency_code="USD",
        is_active=True
    )

    session.add(checking_account)
    session.commit()

    print(f"✅ Created mock PlaidItem: {test_item.id}")
    print(f"✅ Created mock Account: {checking_account.id}")
    print("\nMock data created successfully!")
    print("The sync endpoint will:")
    print("1. ✅ Find the PlaidItem")
    print("2. ✅ Call the sync function")
    print("3. ❌ Fail at Plaid API (expected - demo credentials)")
    print("4. ✅ Handle the error gracefully")

    return True

if __name__ == "__main__":
    success = create_mock_plaid_item()
    if success:
        print("\n🧪 Now test the sync endpoint:")
        print("curl -X POST 'http://localhost:8000/api/v1/plaid/sync-transactions' -H 'Content-Type: application/json' -d '{}'")
        print("\nExpected result: Error from Plaid API but proves our endpoint works!")
    else:
        print("\n❌ Mock data creation failed!")