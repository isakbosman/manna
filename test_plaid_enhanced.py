#!/usr/bin/env python
"""Test the enhanced Plaid integration."""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.plaid_manager import PlaidManager
from src.utils.database import init_database
import json

def test_plaid_manager():
    """Test the enhanced Plaid Manager functionality."""
    print("=" * 50)
    print("Testing Enhanced Plaid Integration")
    print("=" * 50)
    
    # Initialize
    print("\n1. Initializing PlaidManager...")
    try:
        manager = PlaidManager()
        print("✅ PlaidManager initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test account listing
    print("\n2. Listing connected accounts...")
    accounts = manager.list_connected_accounts()
    if accounts:
        print(f"✅ Found {len(accounts)} connected accounts:")
        for acc in accounts:
            print(f"   • {acc['institution_name']} - {acc['account_name']} (***{acc.get('mask', 'N/A')})")
    else:
        print("ℹ️ No accounts connected yet")
    
    # Test account categorization
    print("\n3. Testing account categorization...")
    categorized = manager.categorize_accounts()
    
    business_count = sum(len(accs) for accs in categorized['business'].values())
    personal_count = sum(len(accs) for accs in categorized['personal'].values())
    
    print(f"✅ Categorization complete:")
    print(f"   • Business accounts: {business_count}")
    print(f"   • Personal accounts: {personal_count}")
    
    # Test account summary
    if accounts:
        print("\n4. Getting account summary...")
        summary = manager.get_account_summary()
        
        print("✅ Summary generated:")
        print(f"   • Total accounts: {summary['total_accounts']}")
        print(f"   • Total assets: ${summary['total_assets']:,.2f}")
        print(f"   • Total liabilities: ${summary['total_liabilities']:,.2f}")
        print(f"   • Net worth: ${summary['net_worth']:,.2f}")
        
        print("\n   By Institution:")
        for inst, data in summary['by_institution'].items():
            print(f"     • {inst}: {data['count']} accounts, ${data['balance']:,.2f}")
    
    # Test sandbox mode
    if os.getenv('PLAID_ENV', 'Sandbox').lower() == 'sandbox':
        print("\n5. Testing sandbox mode...")
        print("ℹ️ Running in sandbox mode")
        
        # Try creating a link token
        try:
            link_token = manager.create_link_token()
            if link_token:
                print(f"✅ Link token created: {link_token[:20]}...")
            else:
                print("❌ Failed to create link token")
        except Exception as e:
            print(f"⚠️ Link token creation failed (expected if no credentials): {e}")
    
    # Show what's needed
    print("\n" + "=" * 50)
    print("Account Requirements Status")
    print("=" * 50)
    
    requirements = [
        ("Business Checking", 2, len(categorized['business']['checking'])),
        ("Business Credit", 1, len(categorized['business']['credit'])),
        ("Personal Checking", 1, len(categorized['personal']['checking'])),
        ("Personal Credit", 6, len(categorized['personal']['credit'])),
        ("Investment", 1, len(categorized['personal']['investment']))
    ]
    
    all_met = True
    for name, required, current in requirements:
        if current >= required:
            print(f"✅ {name}: {current}/{required}")
        else:
            print(f"⚠️ {name}: {current}/{required} - Need {required - current} more")
            all_met = False
    
    if all_met:
        print("\n🎉 All account requirements met!")
    else:
        print("\n📋 Run './start.sh' and choose option 3 to connect missing accounts")
    
    print("\n" + "=" * 50)
    print("Test Complete")
    print("=" * 50)

if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Run tests
    test_plaid_manager()