"""Enhanced Plaid integration with better account management and visibility."""

import os
import json
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.sandbox_public_token_create_request_options import SandboxPublicTokenCreateRequestOptions
from dotenv import load_dotenv

load_dotenv()

class PlaidManager:
    """Advanced Plaid account management with detailed visibility."""
    
    def __init__(self):
        """Initialize Plaid client with configuration."""
        # Determine environment
        env_name = os.getenv('PLAID_ENV', 'Sandbox')
        if env_name.lower() == 'sandbox':
            host = plaid.Environment.Sandbox
        elif env_name.lower() == 'development':
            host = plaid.Environment.Development
        elif env_name.lower() == 'production':
            host = plaid.Environment.Production
        else:
            host = plaid.Environment.Sandbox
            
        configuration = plaid.Configuration(
            host=host,
            api_key={
                'clientId': os.getenv('PLAID_CLIENT_ID'),
                'secret': os.getenv('PLAID_SECRET'),
            }
        )
        
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        self.tokens_file = 'config/plaid_accounts.json'
        self.accounts_data = self._load_accounts_data()
    
    def _load_accounts_data(self) -> Dict:
        """Load stored account data including tokens and metadata."""
        if os.path.exists(self.tokens_file):
            with open(self.tokens_file, 'r') as f:
                return json.load(f)
        return {
            'accounts': {},
            'items': {},
            'last_sync': {}
        }
    
    def _save_accounts_data(self):
        """Save account data to file."""
        os.makedirs('config', exist_ok=True)
        with open(self.tokens_file, 'w') as f:
            json.dump(self.accounts_data, f, indent=2, default=str)
    
    def create_link_token(self, user_id: str = "user_1") -> str:
        """Create a Link token for connecting new accounts."""
        request = LinkTokenCreateRequest(
            products=[Products('transactions')],
            client_name="Financial Management System",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id=user_id)
        )
        
        response = self.client.link_token_create(request)
        return response['link_token']
    
    def exchange_public_token(self, public_token: str, metadata: Dict) -> Tuple[str, Dict]:
        """
        Exchange public token for access token and store account details.
        Returns (access_token, account_details)
        """
        # Exchange token
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        access_token = response['access_token']
        item_id = response['item_id']
        
        # Get account details
        accounts = self.get_accounts_details(access_token)
        
        # Get institution info
        institution_info = self.get_institution_info(access_token)
        
        # Store the data
        for account in accounts:
            account_key = f"{institution_info['name']}_{account['mask']}"
            
            self.accounts_data['accounts'][account['account_id']] = {
                'account_id': account['account_id'],
                'item_id': item_id,
                'access_token': access_token,
                'institution_name': institution_info['name'],
                'institution_id': institution_info['institution_id'],
                'account_name': account['name'],
                'official_name': account['official_name'],
                'type': account['type'],
                'subtype': account['subtype'],
                'mask': account['mask'],
                'current_balance': account['balances']['current'],
                'available_balance': account['balances']['available'],
                'limit': account['balances'].get('limit'),
                'currency': account['balances'].get('iso_currency_code', 'USD'),
                'connected_at': datetime.now().isoformat(),
                'friendly_name': account_key,
                'is_business': self._detect_business_account(account, institution_info),
                'metadata': metadata
            }
        
        self.accounts_data['items'][item_id] = {
            'access_token': access_token,
            'institution_name': institution_info['name'],
            'accounts': [acc['account_id'] for acc in accounts]
        }
        
        self._save_accounts_data()
        
        return access_token, {
            'institution': institution_info['name'],
            'accounts': accounts
        }
    
    def get_accounts_details(self, access_token: str) -> List[Dict]:
        """Get detailed information about all accounts for an access token."""
        request = AccountsGetRequest(access_token=access_token)
        response = self.client.accounts_get(request)
        
        accounts = []
        for account in response['accounts']:
            accounts.append({
                'account_id': account['account_id'],
                'name': account['name'],
                'official_name': account.get('official_name'),
                'type': account['type'],
                'subtype': account.get('subtype'),
                'mask': account.get('mask'),
                'balances': {
                    'current': account['balances']['current'],
                    'available': account['balances'].get('available'),
                    'limit': account['balances'].get('limit'),
                    'iso_currency_code': account['balances'].get('iso_currency_code', 'USD')
                }
            })
        
        return accounts
    
    def get_institution_info(self, access_token: str) -> Dict:
        """Get institution information for an access token."""
        # First get the item to get institution_id
        item_request = ItemGetRequest(access_token=access_token)
        item_response = self.client.item_get(item_request)
        institution_id = item_response['item']['institution_id']
        
        # Get institution details
        inst_request = InstitutionsGetByIdRequest(
            institution_id=institution_id,
            country_codes=[CountryCode('US')]
        )
        inst_response = self.client.institutions_get_by_id(inst_request)
        institution = inst_response['institution']
        
        return {
            'institution_id': institution_id,
            'name': institution['name'],
            'url': institution.get('url'),
            'primary_color': institution.get('primary_color'),
            'logo': institution.get('logo')
        }
    
    def _detect_business_account(self, account: Dict, institution: Dict) -> bool:
        """Detect if an account is likely a business account."""
        business_indicators = [
            'business', 'corp', 'company', 'llc', 'inc', 
            'commercial', 'merchant', 'biz'
        ]
        
        # Check account name
        account_name = (account.get('name', '') + ' ' + 
                       account.get('official_name', '')).lower()
        
        for indicator in business_indicators:
            if indicator in account_name:
                return True
        
        # Check subtype
        business_subtypes = ['commercial', 'business', 'merchant']
        if account.get('subtype', '').lower() in business_subtypes:
            return True
        
        return False
    
    def list_connected_accounts(self) -> List[Dict]:
        """List all connected accounts with full details."""
        accounts = []
        for account_id, account_data in self.accounts_data['accounts'].items():
            # Update balance if possible
            try:
                current_accounts = self.get_accounts_details(account_data['access_token'])
                for curr_acc in current_accounts:
                    if curr_acc['account_id'] == account_id:
                        account_data['current_balance'] = curr_acc['balances']['current']
                        account_data['available_balance'] = curr_acc['balances']['available']
                        break
            except:
                pass  # Keep stored balance if update fails
            
            accounts.append(account_data)
        
        return sorted(accounts, key=lambda x: (not x.get('is_business', False), x['institution_name']))
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """Get a specific account by ID."""
        return self.accounts_data['accounts'].get(account_id)
    
    def sync_transactions(self, account_id: str, cursor: Optional[str] = None) -> Dict:
        """Sync transactions for a specific account."""
        account = self.accounts_data['accounts'].get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Get cursor from last sync if not provided
        if not cursor:
            cursor = self.accounts_data['last_sync'].get(account_id)
        
        request = TransactionsSyncRequest(
            access_token=account['access_token'],
            cursor=cursor
        )
        
        response = self.client.transactions_sync(request)
        
        # Update last sync cursor
        self.accounts_data['last_sync'][account_id] = response['next_cursor']
        self._save_accounts_data()
        
        return {
            'added': response['added'],
            'modified': response['modified'],
            'removed': response['removed'],
            'has_more': response['has_more'],
            'next_cursor': response['next_cursor']
        }
    
    def sync_all_transactions(self) -> Dict[str, List]:
        """Sync transactions for all connected accounts."""
        all_transactions = {}
        
        for account_id in self.accounts_data['accounts'].keys():
            try:
                result = self.sync_transactions(account_id)
                all_transactions[account_id] = result['added']
                
                # Continue syncing if there's more
                while result['has_more']:
                    result = self.sync_transactions(account_id, result['next_cursor'])
                    all_transactions[account_id].extend(result['added'])
                    
            except Exception as e:
                print(f"Error syncing {account_id}: {e}")
                all_transactions[account_id] = []
        
        return all_transactions
    
    def categorize_accounts(self) -> Dict:
        """Categorize all accounts by type and purpose."""
        categories = {
            'business': {
                'checking': [],
                'savings': [],
                'credit': [],
                'other': []
            },
            'personal': {
                'checking': [],
                'savings': [],
                'credit': [],
                'investment': [],
                'other': []
            }
        }
        
        for account in self.list_connected_accounts():
            category = 'business' if account.get('is_business') else 'personal'
            
            if account['type'] == 'depository':
                if account.get('subtype') == 'savings':
                    categories[category]['savings'].append(account)
                else:
                    categories[category]['checking'].append(account)
            elif account['type'] == 'credit':
                categories[category]['credit'].append(account)
            elif account['type'] == 'investment':
                categories[category]['investment'].append(account)
            else:
                categories[category]['other'].append(account)
        
        return categories
    
    def get_account_summary(self) -> Dict:
        """Get a summary of all connected accounts."""
        accounts = self.list_connected_accounts()
        categorized = self.categorize_accounts()
        
        summary = {
            'total_accounts': len(accounts),
            'business_accounts': sum(len(accs) for accs in categorized['business'].values()),
            'personal_accounts': sum(len(accs) for accs in categorized['personal'].values()),
            'total_assets': 0,
            'total_liabilities': 0,
            'net_worth': 0,
            'by_institution': {},
            'by_type': {
                'checking': 0,
                'savings': 0,
                'credit_cards': 0,
                'investments': 0
            }
        }
        
        for account in accounts:
            balance = account.get('current_balance', 0) or 0
            
            # Group by institution
            inst_name = account['institution_name']
            if inst_name not in summary['by_institution']:
                summary['by_institution'][inst_name] = {
                    'count': 0,
                    'balance': 0,
                    'accounts': []
                }
            
            summary['by_institution'][inst_name]['count'] += 1
            summary['by_institution'][inst_name]['balance'] += balance
            summary['by_institution'][inst_name]['accounts'].append({
                'name': account['account_name'],
                'mask': account['mask'],
                'type': account['type'],
                'balance': balance
            })
            
            # Calculate totals
            if account['type'] in ['depository', 'investment']:
                summary['total_assets'] += balance
                if account.get('subtype') == 'savings':
                    summary['by_type']['savings'] += balance
                elif account['type'] == 'investment':
                    summary['by_type']['investments'] += balance
                else:
                    summary['by_type']['checking'] += balance
            elif account['type'] == 'credit':
                # Credit cards show negative balance
                summary['total_liabilities'] += abs(balance)
                summary['by_type']['credit_cards'] += abs(balance)
        
        summary['net_worth'] = summary['total_assets'] - summary['total_liabilities']
        
        return summary
    
    def create_sandbox_accounts(self) -> Dict:
        """Create sandbox accounts for testing (only works in Sandbox mode)."""
        # This creates test accounts with sample data
        institutions = [
            ('ins_109508', 'Chase'),  # Chase
            ('ins_109509', 'Bank of America'),  # BoA
            ('ins_109510', 'Wells Fargo'),  # Wells Fargo
            ('ins_109511', 'Citi'),  # Citi
            ('ins_109512', 'US Bank'),  # US Bank
        ]
        
        created_accounts = {}
        
        for inst_id, inst_name in institutions[:3]:  # Create 3 test institutions
            try:
                # Create sandbox public token
                options = SandboxPublicTokenCreateRequestOptions(
                    override_username='user_good',
                    override_password='pass_good'
                )
                
                request = SandboxPublicTokenCreateRequest(
                    institution_id=inst_id,
                    initial_products=[Products('transactions')],
                    options=options
                )
                
                response = self.client.sandbox_public_token_create(request)
                public_token = response['public_token']
                
                # Exchange for access token
                access_token, details = self.exchange_public_token(
                    public_token, 
                    {'source': 'sandbox', 'institution': inst_name}
                )
                
                created_accounts[inst_name] = details
                
            except Exception as e:
                print(f"Error creating sandbox account for {inst_name}: {e}")
        
        return created_accounts