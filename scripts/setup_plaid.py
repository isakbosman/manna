#!/usr/bin/env python
"""Setup script for connecting Plaid accounts."""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.plaid_client import PlaidClient, ACCOUNT_CONFIG
from src.utils.database import init_database, get_session, Account
import getpass

def setup_plaid_accounts():
    """Interactive setup for Plaid account connections."""
    print("=" * 50)
    print("PLAID ACCOUNT SETUP")
    print("=" * 50)
    
    # Initialize database
    engine = init_database()
    session = get_session()
    
    # Initialize Plaid client
    client = PlaidClient()
    
    print("\nYou need to connect 11 accounts:")
    print("- 2 Business Bank Accounts")
    print("- 1 Business Credit Card")
    print("- 1 Personal Bank Account")
    print("- 6-7 Personal Credit Cards")
    print("- 1 Investment Account")
    print()
    
    for account_key, config in ACCOUNT_CONFIG.items():
        print(f"\n[{account_key}]")
        print(f"Type: {config['type']}")
        print(f"Business: {'Yes' if config['is_business'] else 'No'}")
        print(f"Institution: {config['institution']}")
        
        # Check if already connected
        existing = session.query(Account).filter(
            Account.account_name == account_key
        ).first()
        
        if existing:
            print("✅ Already connected")
            continue
        
        connect = input("Connect this account? (y/n): ").lower()
        if connect == 'y':
            # In production, this would launch Plaid Link
            # For now, we'll simulate with a placeholder
            print("Please use Plaid Link to get access token...")
            access_token = getpass.getpass("Enter Plaid access token: ")
            
            if access_token:
                # Save token
                client.save_access_token(account_key, access_token)
                
                # Create account record
                account = Account(
                    id=f"acc_{account_key}",
                    account_name=account_key,
                    account_type=config['type'],
                    institution_name=config['institution'],
                    is_business=config['is_business'],
                    is_active=True
                )
                session.add(account)
                session.commit()
                
                print("✅ Account connected successfully")
            else:
                print("⏭️  Skipped")
    
    print("\n" + "=" * 50)
    print("SETUP COMPLETE")
    print("=" * 50)
    
    # Show summary
    connected_accounts = session.query(Account).all()
    print(f"\nConnected Accounts: {len(connected_accounts)}/11")
    
    for acc in connected_accounts:
        print(f"  - {acc.account_name} ({acc.account_type})")
    
    if len(connected_accounts) < 11:
        print("\n⚠️  Not all accounts connected. You can add more later.")
    else:
        print("\n✅ All accounts connected! Ready to start syncing.")

if __name__ == "__main__":
    setup_plaid_accounts()