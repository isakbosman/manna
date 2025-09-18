#!/usr/bin/env python
"""Debug script to check accounts and plaid items in the database."""

from src.database import SessionLocal
from src.database.models import User, PlaidItem, Account, Transaction

def debug_accounts():
    """Check the current state of users, plaid items, and accounts."""
    db = SessionLocal()

    try:
        # Check users
        users = db.query(User).all()
        print(f"Total users: {len(users)}")
        for user in users:
            print(f"  - User: {user.email} (ID: {user.id})")

        # Check plaid items
        plaid_items = db.query(PlaidItem).all()
        print(f"\nTotal Plaid items: {len(plaid_items)}")
        for item in plaid_items:
            print(f"  - PlaidItem: {item.id}")
            print(f"    User ID: {item.user_id}")
            print(f"    Institution ID: {item.institution_id}")
            print(f"    Active: {item.is_active}")
            print(f"    Cursor: {item.cursor}")
            print(f"    Last sync: {item.last_successful_sync}")

        # Check accounts
        accounts = db.query(Account).all()
        print(f"\nTotal accounts: {len(accounts)}")
        for account in accounts:
            print(f"  - Account: {account.name} (ID: {account.id})")
            print(f"    User ID: {account.user_id}")
            print(f"    PlaidItem ID: {account.plaid_item_id}")
            print(f"    Plaid Account ID: {account.plaid_account_id}")
            print(f"    Type: {account.type}/{account.subtype}")
            print(f"    Active: {account.is_active}")

        # Check transactions
        transactions = db.query(Transaction).count()
        print(f"\nTotal transactions: {transactions}")

        if len(plaid_items) == 0:
            print("\n❌ No Plaid items found - user needs to link bank accounts first")
        elif len(accounts) == 0:
            print("\n❌ No accounts found - accounts not created during linking")
        else:
            print("\n✅ Accounts exist - sync should work")

    finally:
        db.close()

if __name__ == "__main__":
    debug_accounts()