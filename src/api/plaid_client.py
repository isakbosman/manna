"""Plaid API client for fetching transactions from multiple accounts."""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from dotenv import load_dotenv
import json

load_dotenv()

class PlaidClient:
    """Manages Plaid API connections for multiple accounts."""
    
    def __init__(self):
        configuration = plaid.Configuration(
            host=getattr(plaid.Environment, os.getenv('PLAID_ENV', 'Development'), plaid.Environment.Development),
            api_key={
                'clientId': os.getenv('PLAID_CLIENT_ID'),
                'secret': os.getenv('PLAID_SECRET'),
            }
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        self.access_tokens = self._load_access_tokens()
    
    def _load_access_tokens(self) -> Dict[str, str]:
        """Load access tokens for all configured accounts."""
        tokens_file = 'config/plaid_tokens.json'
        if os.path.exists(tokens_file):
            with open(tokens_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_access_token(self, account_name: str, access_token: str):
        """Save access token for an account."""
        self.access_tokens[account_name] = access_token
        os.makedirs('config', exist_ok=True)
        with open('config/plaid_tokens.json', 'w') as f:
            json.dump(self.access_tokens, f)
    
    def get_accounts(self, account_name: str) -> List[Dict]:
        """Get all accounts for a given access token."""
        if account_name not in self.access_tokens:
            raise ValueError(f"No access token for account: {account_name}")
        
        request = AccountsGetRequest(
            access_token=self.access_tokens[account_name]
        )
        response = self.client.accounts_get(request)
        
        accounts = []
        for account in response['accounts']:
            accounts.append({
                'id': account['account_id'],
                'name': account['name'],
                'type': account['type'],
                'subtype': account['subtype'],
                'current_balance': account['balances']['current'],
                'available_balance': account['balances']['available'],
                'limit': account['balances'].get('limit'),
                'institution_id': response['item']['institution_id']
            })
        
        return accounts
    
    def sync_transactions(self, account_name: str, cursor: Optional[str] = None) -> Dict:
        """Sync transactions using Plaid's transactions/sync endpoint."""
        if account_name not in self.access_tokens:
            raise ValueError(f"No access token for account: {account_name}")
        
        request = TransactionsSyncRequest(
            access_token=self.access_tokens[account_name],
            cursor=cursor
        )
        response = self.client.transactions_sync(request)
        
        return {
            'added': response['added'],
            'modified': response['modified'],
            'removed': response['removed'],
            'next_cursor': response['next_cursor'],
            'has_more': response['has_more']
        }
    
    def get_transactions(self, account_name: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get transactions for a date range."""
        if account_name not in self.access_tokens:
            raise ValueError(f"No access token for account: {account_name}")
        
        request = TransactionsGetRequest(
            access_token=self.access_tokens[account_name],
            start_date=start_date.date(),
            end_date=end_date.date()
        )
        response = self.client.transactions_get(request)
        
        transactions = []
        for txn in response['transactions']:
            transactions.append({
                'id': txn['transaction_id'],
                'account_id': txn['account_id'],
                'amount': txn['amount'],
                'date': txn['date'],
                'name': txn['name'],
                'merchant_name': txn.get('merchant_name'),
                'category': txn['category'][0] if txn.get('category') else None,
                'subcategory': txn['category'][1] if txn.get('category') and len(txn['category']) > 1 else None,
                'pending': txn['pending'],
                'location': {
                    'city': txn['location'].get('city') if txn.get('location') else None,
                    'state': txn['location'].get('region') if txn.get('location') else None,
                },
                'payment_channel': txn.get('payment_channel')
            })
        
        return transactions
    
    def fetch_all_accounts_transactions(self, days_back: int = 30) -> Dict[str, List[Dict]]:
        """Fetch transactions from all configured accounts."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        all_transactions = {}
        for account_name in self.access_tokens.keys():
            try:
                transactions = self.get_transactions(account_name, start_date, end_date)
                all_transactions[account_name] = transactions
                print(f"Fetched {len(transactions)} transactions from {account_name}")
            except Exception as e:
                print(f"Error fetching from {account_name}: {e}")
                all_transactions[account_name] = []
        
        return all_transactions

# Account configuration for 11 accounts
ACCOUNT_CONFIG = {
    'business_checking_1': {
        'type': 'checking',
        'is_business': True,
        'institution': 'Bank 1'
    },
    'business_checking_2': {
        'type': 'checking', 
        'is_business': True,
        'institution': 'Bank 2'
    },
    'business_credit': {
        'type': 'credit',
        'is_business': True,
        'institution': 'Credit Card Company'
    },
    'personal_checking': {
        'type': 'checking',
        'is_business': False,
        'institution': 'Personal Bank'
    },
    'personal_credit_1': {
        'type': 'credit',
        'is_business': False,
        'institution': 'CC Company 1'
    },
    'personal_credit_2': {
        'type': 'credit',
        'is_business': False,
        'institution': 'CC Company 2'
    },
    'personal_credit_3': {
        'type': 'credit',
        'is_business': False,
        'institution': 'CC Company 3'
    },
    'personal_credit_4': {
        'type': 'credit',
        'is_business': False,
        'institution': 'CC Company 4'
    },
    'personal_credit_5': {
        'type': 'credit',
        'is_business': False,
        'institution': 'CC Company 5'
    },
    'personal_credit_6': {
        'type': 'credit',
        'is_business': False,
        'institution': 'CC Company 6'
    },
    'investment_account': {
        'type': 'investment',
        'is_business': False,
        'institution': 'Brokerage'
    }
}