#!/usr/bin/env python
"""Enhanced Plaid setup with clear account visibility and mapping."""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.plaid_manager import PlaidManager
from src.utils.database import init_database, get_session, Account

console = Console()

class PlaidSetupWizard:
    """Interactive wizard for setting up Plaid accounts with full visibility."""
    
    def __init__(self):
        self.plaid_manager = PlaidManager()
        self.session = get_session()
        self.target_accounts = {
            'business': {
                'checking': 2,
                'credit': 1
            },
            'personal': {
                'checking': 1,
                'credit': 7,  # 6-7 cards
                'investment': 1
            }
        }
    
    def run(self):
        """Run the interactive setup wizard."""
        console.clear()
        self._show_welcome()
        
        while True:
            choice = self._show_main_menu()
            
            if choice == '1':
                self._show_current_accounts()
            elif choice == '2':
                self._connect_new_account()
            elif choice == '3':
                self._verify_account_mapping()
            elif choice == '4':
                self._test_sandbox_mode()
            elif choice == '5':
                self._sync_all_transactions()
            elif choice == '6':
                self._remove_account()
            elif choice == '7':
                break
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")
    
    def _show_welcome(self):
        """Display welcome message."""
        welcome = Panel.fit(
            "[bold cyan]Plaid Account Setup Wizard[/bold cyan]\n\n"
            "This wizard will help you connect and manage your financial accounts.\n"
            "You need to connect:\n"
            "• 2 Business Bank Accounts\n"
            "• 1 Business Credit Card\n"
            "• 1 Personal Bank Account\n"
            "• 6-7 Personal Credit Cards\n"
            "• 1 Investment Account",
            title="Welcome",
            border_style="cyan"
        )
        console.print(welcome)
        console.print()
    
    def _show_main_menu(self) -> str:
        """Display main menu and get user choice."""
        console.print("\n[bold]Main Menu[/bold]")
        console.print("1. View Current Accounts")
        console.print("2. Connect New Account")
        console.print("3. Verify Account Mapping")
        console.print("4. Test with Sandbox Accounts")
        console.print("5. Sync All Transactions")
        console.print("6. Remove Account")
        console.print("7. Exit")
        
        return Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5", "6", "7"])
    
    def _show_current_accounts(self):
        """Display all currently connected accounts with details."""
        accounts = self.plaid_manager.list_connected_accounts()
        
        if not accounts:
            console.print("\n[yellow]No accounts connected yet.[/yellow]")
            return
        
        # Get summary
        summary = self.plaid_manager.get_account_summary()
        
        # Display summary
        console.print("\n[bold]Account Summary[/bold]")
        summary_table = Table(show_header=False, box=None)
        summary_table.add_row("Total Accounts:", f"[cyan]{summary['total_accounts']}[/cyan]")
        summary_table.add_row("Business Accounts:", f"[green]{summary['business_accounts']}[/green]")
        summary_table.add_row("Personal Accounts:", f"[blue]{summary['personal_accounts']}[/blue]")
        summary_table.add_row("Total Assets:", f"[green]${summary['total_assets']:,.2f}[/green]")
        summary_table.add_row("Total Liabilities:", f"[red]${summary['total_liabilities']:,.2f}[/red]")
        summary_table.add_row("Net Worth:", f"[bold]${summary['net_worth']:,.2f}[/bold]")
        console.print(summary_table)
        
        # Display accounts by institution
        console.print("\n[bold]Accounts by Institution[/bold]")
        
        for inst_name, inst_data in summary['by_institution'].items():
            console.print(f"\n[bold cyan]{inst_name}[/bold cyan] ({inst_data['count']} accounts)")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Account", style="cyan", width=30)
            table.add_column("Type", width=15)
            table.add_column("Mask", width=10)
            table.add_column("Balance", justify="right", width=15)
            
            for acc in inst_data['accounts']:
                balance_str = f"${acc['balance']:,.2f}"
                if acc['type'] == 'credit':
                    balance_str = f"[red]{balance_str}[/red]"
                else:
                    balance_str = f"[green]{balance_str}[/green]"
                
                table.add_row(
                    acc['name'],
                    acc['type'],
                    f"***{acc['mask']}" if acc['mask'] else "N/A",
                    balance_str
                )
            
            console.print(table)
        
        # Show categorized view
        categorized = self.plaid_manager.categorize_accounts()
        
        console.print("\n[bold]Account Categories[/bold]")
        
        for category in ['business', 'personal']:
            console.print(f"\n[bold]{category.title()} Accounts:[/bold]")
            
            for acc_type, accounts in categorized[category].items():
                if accounts:
                    console.print(f"  {acc_type.title()}: {len(accounts)} account(s)")
                    for acc in accounts:
                        console.print(f"    • {acc['institution_name']} - {acc['account_name']} (***{acc.get('mask', 'N/A')})")
    
    def _connect_new_account(self):
        """Connect a new account through Plaid Link."""
        console.print("\n[bold]Connect New Account[/bold]")
        
        # Check if we're in sandbox mode
        if os.getenv('PLAID_ENV', 'Sandbox').lower() == 'sandbox':
            console.print("[yellow]Running in Sandbox mode.[/yellow]")
            
            choice = Prompt.ask(
                "\nChoose connection method",
                choices=["1", "2", "3"],
                default="1"
            )
            
            if choice == "1":
                self._launch_plaid_link_server()
                return
            elif choice == "2":
                self._create_sandbox_accounts()
                return
            else:
                return
        else:
            # Production mode - launch web server
            self._launch_plaid_link_server()
            return
    
    def _launch_plaid_link_server(self):
        """Launch the Plaid Link web server."""
        console.print("\n[cyan]Launching Plaid Link Web Interface...[/cyan]")
        console.print("\nOptions:")
        console.print("1. Open web browser to connect accounts")
        console.print("2. Create test sandbox accounts")
        console.print("3. Cancel")
        
        import subprocess
        import time
        import webbrowser
        
        # Check if Flask is installed
        try:
            import flask
        except ImportError:
            console.print("[yellow]Installing Flask...[/yellow]")
            subprocess.run([sys.executable, "-m", "pip", "install", "flask", "flask-cors"], check=True)
        
        # Start the Flask server in background
        console.print("\n[green]Starting Plaid Link server...[/green]")
        server_process = subprocess.Popen(
            [sys.executable, "src/api/plaid_link_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(2)
        
        # Open browser
        url = "http://localhost:5000"
        console.print(f"\n[bold cyan]Opening browser to: {url}[/bold cyan]")
        console.print("\nUse the web interface to:")
        console.print("1. Click 'Connect Account' to launch Plaid Link")
        console.print("2. Select your bank and login")
        console.print("3. Choose accounts to connect")
        console.print("4. Select if it's a business or personal account")
        console.print("\nThe server will handle everything automatically!")
        
        webbrowser.open(url)
        
        console.print("\n[yellow]Press Enter when done connecting accounts...[/yellow]")
        input()
        
        # Stop server
        server_process.terminate()
        console.print("[green]Server stopped. Refreshing account list...[/green]")
        
        # Refresh accounts
        self.plaid_manager._load_accounts_data()
        self.plaid_manager.accounts_data = self.plaid_manager._load_accounts_data()
    
    def _create_sandbox_accounts(self):
        """Create sandbox test accounts."""
        console.print("\n[cyan]Creating sandbox accounts...[/cyan]")
        
        try:
            created = self.plaid_manager.create_sandbox_accounts()
            
            for inst_name, details in created.items():
                console.print(f"\n[green]Created {inst_name} accounts:[/green]")
                for acc in details['accounts']:
                    console.print(f"  • {acc['name']} - ${acc['balances']['current']:,.2f}")
            
            console.print("\n[green]Sandbox accounts created successfully![/green]")
            
        except Exception as e:
            console.print(f"[red]Error creating sandbox accounts: {e}[/red]")
    
    def _verify_account_mapping(self):
        """Verify and update account mappings."""
        accounts = self.plaid_manager.list_connected_accounts()
        
        if not accounts:
            console.print("\n[yellow]No accounts to verify.[/yellow]")
            return
        
        console.print("\n[bold]Verify Account Mappings[/bold]")
        console.print("Review each account and confirm its categorization:\n")
        
        for account in accounts:
            console.print(f"\n[cyan]{account['institution_name']} - {account['account_name']}[/cyan]")
            console.print(f"  Type: {account['type']}")
            console.print(f"  Mask: ***{account.get('mask', 'N/A')}")
            console.print(f"  Balance: ${account.get('current_balance', 0):,.2f}")
            console.print(f"  Currently marked as: [{'green' if account.get('is_business') else 'blue'}]"
                         f"{'Business' if account.get('is_business') else 'Personal'}[/{'green' if account.get('is_business') else 'blue'}]")
            
            if Confirm.ask("Is this categorization correct?", default=True):
                continue
            
            # Update categorization
            is_business = Confirm.ask("Should this be a business account?")
            account['is_business'] = is_business
            
            # Update in storage
            self.plaid_manager.accounts_data['accounts'][account['account_id']]['is_business'] = is_business
            self.plaid_manager._save_accounts_data()
            
            console.print("[green]Updated![/green]")
    
    def _sync_all_transactions(self):
        """Sync transactions for all accounts."""
        console.print("\n[bold]Syncing Transactions[/bold]")
        
        with console.status("[cyan]Syncing transactions from all accounts...") as status:
            transactions = self.plaid_manager.sync_all_transactions()
        
        console.print("\n[green]Sync complete![/green]")
        
        for account_id, txns in transactions.items():
            account = self.plaid_manager.get_account_by_id(account_id)
            if account:
                console.print(f"  • {account['institution_name']} - {account['account_name']}: "
                            f"{len(txns)} transactions")
    
    def _remove_account(self):
        """Remove a connected account."""
        accounts = self.plaid_manager.list_connected_accounts()
        
        if not accounts:
            console.print("\n[yellow]No accounts to remove.[/yellow]")
            return
        
        console.print("\n[bold]Remove Account[/bold]")
        
        # Display accounts with numbers
        for i, account in enumerate(accounts, 1):
            console.print(f"{i}. {account['institution_name']} - {account['account_name']} (***{account.get('mask', 'N/A')})")
        
        choice = Prompt.ask("\nSelect account to remove (number or 'cancel')")
        
        if choice.lower() == 'cancel':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(accounts):
                account = accounts[idx]
                
                if Confirm.ask(f"Remove {account['institution_name']} - {account['account_name']}?"):
                    # Remove from storage
                    del self.plaid_manager.accounts_data['accounts'][account['account_id']]
                    
                    # Remove item if no more accounts
                    item_id = account['item_id']
                    remaining = [a for a in self.plaid_manager.accounts_data['accounts'].values() 
                                if a['item_id'] == item_id]
                    if not remaining and item_id in self.plaid_manager.accounts_data['items']:
                        del self.plaid_manager.accounts_data['items'][item_id]
                    
                    self.plaid_manager._save_accounts_data()
                    
                    console.print("[green]Account removed successfully![/green]")
            else:
                console.print("[red]Invalid selection.[/red]")
        except ValueError:
            console.print("[red]Invalid input.[/red]")
    
    def _test_sandbox_mode(self):
        """Test connection with sandbox accounts."""
        console.print("\n[bold]Sandbox Mode Testing[/bold]")
        
        if os.getenv('PLAID_ENV', 'Sandbox').lower() != 'sandbox':
            console.print("[yellow]Not in sandbox mode. Switch PLAID_ENV to 'Sandbox' to use this feature.[/yellow]")
            return
        
        console.print("\nSandbox mode allows you to:")
        console.print("1. Create test accounts with sample data")
        console.print("2. Test transaction sync")
        console.print("3. Verify categorization logic")
        
        if Confirm.ask("\nCreate full set of test accounts?"):
            with console.status("[cyan]Creating test accounts...") as status:
                # This would create a full set of test accounts
                created = self.plaid_manager.create_sandbox_accounts()
            
            console.print("\n[green]Test accounts created![/green]")
            self._show_current_accounts()
    
    def _save_accounts_to_db(self, accounts: List[Dict], is_business: bool):
        """Save account information to database."""
        for acc in accounts:
            # Check if account already exists
            existing = self.session.query(Account).filter(
                Account.plaid_account_id == acc['account_id']
            ).first()
            
            if not existing:
                db_account = Account(
                    id=f"acc_{acc['account_id'][-8:]}",
                    plaid_account_id=acc['account_id'],
                    account_name=acc['name'],
                    account_type=acc['type'],
                    account_subtype=acc.get('subtype'),
                    is_business=is_business,
                    current_balance=acc['balances']['current'],
                    available_balance=acc['balances'].get('available')
                )
                self.session.add(db_account)
        
        self.session.commit()

def main():
    """Run the enhanced Plaid setup wizard."""
    # Check for required package
    try:
        from rich import print
    except ImportError:
        print("Installing required package: rich")
        os.system(f"{sys.executable} -m pip install rich")
        from rich import print
    
    # Initialize database
    init_database()
    
    # Run wizard
    wizard = PlaidSetupWizard()
    wizard.run()
    
    console.print("\n[bold green]Setup complete![/bold green]")

if __name__ == "__main__":
    main()