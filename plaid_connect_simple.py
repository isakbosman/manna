#!/usr/bin/env python
"""Simple Plaid connection without localhost issues."""

import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.api.plaid_manager import PlaidManager
from src.utils.database import init_database, get_session, Account

def main():
    print("""
╔══════════════════════════════════════════════════════╗
║         Connect Your Bank Accounts                   ║
╚══════════════════════════════════════════════════════╝
""")
    
    # Initialize
    init_database()
    plaid_manager = PlaidManager()
    
    # Check environment
    env = os.getenv('PLAID_ENV', 'Sandbox')
    print(f"Environment: {env}")
    
    if env.lower() == 'sandbox':
        print("\n🧪 SANDBOX MODE - Test Credentials:")
        print("Username: user_good")
        print("Password: pass_good")
        print("PIN (if asked): 1234")
    
    print("\nOptions:")
    print("1. Generate Link token and connect manually")
    print("2. Create test sandbox accounts")
    print("3. Enter existing public token")
    print("4. View connected accounts")
    print("5. Exit")
    
    choice = input("\nSelect option (1-5): ")
    
    if choice == "1":
        try:
            print("\nGenerating Link token...")
            link_token = plaid_manager.create_link_token()
            
            print("\n" + "="*50)
            print("LINK TOKEN GENERATED")
            print("="*50)
            print("\nYour Link token (valid for 30 minutes):")
            print(f"\n{link_token}\n")
            
            print("To connect your accounts:")
            print("1. Go to: https://cdn.plaid.com/link/v2/stable/link.html")
            print("2. Open browser console (F12 → Console)")
            print("3. Run this code:")
            print(f"""
Plaid.create({{
    token: '{link_token}',
    onSuccess: (public_token, metadata) => {{
        console.log('SUCCESS! Copy this token:');
        console.log(public_token);
        document.body.innerHTML = '<h1>Token: ' + public_token + '</h1>';
    }}
}}).open();
""")
            print("\n4. Copy the public token that appears")
            print("5. Come back here and paste it")
            
            public_token = input("\nPaste public token (or 'skip'): ")
            
            if public_token and public_token != 'skip':
                is_business = input("Is this a business account? (y/n): ").lower() == 'y'
                
                metadata = {
                    'is_business': is_business,
                    'added_at': datetime.now().isoformat()
                }
                
                try:
                    access_token, details = plaid_manager.exchange_public_token(public_token, metadata)
                    print(f"\n✅ Successfully connected {details['institution']}!")
                    
                    for acc in details['accounts']:
                        print(f"  • {acc['name']} - ${acc['balances']['current']:,.2f}")
                    
                    # Save to database
                    session = get_session()
                    for acc in details['accounts']:
                        existing = session.query(Account).filter(
                            Account.plaid_account_id == acc['account_id']
                        ).first()
                        
                        if not existing:
                            db_account = Account(
                                id=f"acc_{acc['account_id'][-8:]}",
                                plaid_account_id=acc['account_id'],
                                institution_name=details['institution'],
                                account_name=acc['name'],
                                account_type=acc['type'],
                                account_subtype=acc.get('subtype'),
                                is_business=is_business,
                                current_balance=acc['balances']['current'],
                                available_balance=acc['balances'].get('available')
                            )
                            session.add(db_account)
                    
                    session.commit()
                    print("\n✅ Accounts saved to database!")
                    
                except Exception as e:
                    print(f"\n❌ Error: {e}")
            
        except Exception as e:
            print(f"\n❌ Error generating token: {e}")
            print("\nMake sure your Plaid credentials are set in .env:")
            print("PLAID_CLIENT_ID=your_client_id")
            print("PLAID_SECRET=your_secret")
    
    elif choice == "2":
        if env.lower() != 'sandbox':
            print("\n❌ Sandbox accounts only work in Sandbox mode")
            print("Set PLAID_ENV=Sandbox in .env")
        else:
            try:
                print("\nCreating sandbox accounts...")
                created = plaid_manager.create_sandbox_accounts()
                
                for inst_name, details in created.items():
                    print(f"\n✅ Created {inst_name} accounts:")
                    for acc in details['accounts']:
                        print(f"  • {acc['name']} - ${acc['balances']['current']:,.2f}")
                
                print("\n✅ Sandbox accounts created!")
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    elif choice == "3":
        public_token = input("Enter public token: ")
        if public_token:
            # Same as option 1 exchange logic
            pass
    
    elif choice == "4":
        accounts = plaid_manager.list_connected_accounts()
        if accounts:
            summary = plaid_manager.get_account_summary()
            
            print(f"\nTotal accounts: {summary['total_accounts']}")
            print(f"Total assets: ${summary['total_assets']:,.2f}")
            print(f"Total liabilities: ${summary['total_liabilities']:,.2f}")
            print(f"Net worth: ${summary['net_worth']:,.2f}")
            
            print("\nAccounts by institution:")
            for inst_name, inst_data in summary['by_institution'].items():
                print(f"\n{inst_name} ({inst_data['count']} accounts):")
                for acc in inst_data['accounts']:
                    print(f"  • {acc['name']} (***{acc['mask']}): ${acc['balance']:,.2f}")
        else:
            print("\nNo accounts connected yet")

if __name__ == "__main__":
    main()