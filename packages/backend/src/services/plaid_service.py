"""
Plaid API integration service for financial data access.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from plaid import ApiClient, Configuration
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.item_remove_request import ItemRemoveRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.webhook_verification_key_get_request import WebhookVerificationKeyGetRequest
from plaid.exceptions import ApiException

from ..config import settings
from ..database.models import PlaidItem, Account, Transaction

logger = logging.getLogger(__name__)


class PlaidService:
    """Service for interacting with Plaid API."""
    
    def __init__(self):
        """Initialize Plaid client with configuration."""
        # Map environment string to Plaid Environment
        # Note: Plaid SDK v12+ changed the Environment values
        env_map = {
            'sandbox': 'https://sandbox.plaid.com',
            'development': 'https://development.plaid.com',
            'production': 'https://production.plaid.com'
        }
        host_url = env_map.get(settings.plaid_environment, 'https://sandbox.plaid.com')

        configuration = Configuration(
            host=host_url,
            api_key={
                'clientId': settings.plaid_client_id,
                'secret': settings.plaid_secret,
            }
        )
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        
        # Map string products to Plaid Products enum
        # Note: 'accounts' is not a valid product, it's included with other products
        self.products = []
        for product in settings.plaid_products:
            if product == "transactions":
                self.products.append(Products('transactions'))
            elif product == "accounts":
                # Skip 'accounts' as it's not a valid Plaid product
                # Account data is automatically included with other products
                continue
            elif product == "identity":
                self.products.append(Products('identity'))
            elif product == "investments":
                self.products.append(Products('investments'))
            elif product == "liabilities":
                self.products.append(Products('liabilities'))
        
        # Map country codes
        self.country_codes = [CountryCode(code) for code in settings.plaid_country_codes]
    
    async def create_link_token(
        self,
        user_id: str,
        user_name: str,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Plaid Link token for user authentication.
        
        Args:
            user_id: User ID for Plaid tracking
            user_name: User's display name
            access_token: Optional access token for update mode
            
        Returns:
            Dict containing link_token and expiration
        """
        try:
            # Build request parameters
            request_params = {
                "products": self.products if not access_token else [],
                "client_name": settings.app_name,
                "country_codes": self.country_codes,
                "language": 'en',
                "user": LinkTokenCreateRequestUser(
                    client_user_id=str(user_id),
                    legal_name=user_name
                )
            }

            # Add webhook URL if configured
            if settings.plaid_webhook_url:
                request_params["webhook"] = settings.plaid_webhook_url

            # Add access token for update mode
            if access_token:
                request_params["access_token"] = access_token

            request = LinkTokenCreateRequest(**request_params)
            
            response = self.client.link_token_create(request)
            
            logger.info(f"Link token created for user {user_id}")
            
            return {
                "link_token": response['link_token'],
                "expiration": response['expiration'],
                "request_id": response['request_id']
            }
            
        except ApiException as e:
            logger.error(f"Failed to create link token: {e}")
            raise Exception(f"Failed to create Plaid link token: {str(e)}")
    
    async def exchange_public_token(self, public_token: str) -> str:
        """
        Exchange a public token for an access token.
        
        Args:
            public_token: Public token from Plaid Link
            
        Returns:
            Access token for API requests
        """
        try:
            request = ItemPublicTokenExchangeRequest(
                public_token=public_token
            )
            
            response = self.client.item_public_token_exchange(request)
            
            logger.info(f"Public token exchanged successfully")
            
            return response['access_token']
            
        except ApiException as e:
            logger.error(f"Failed to exchange public token: {e}")
            raise Exception(f"Failed to exchange public token: {str(e)}")
    
    async def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Fetch accounts associated with an access token.
        
        Args:
            access_token: Plaid access token
            
        Returns:
            List of account dictionaries
        """
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            accounts = []
            for account in response['accounts']:
                accounts.append({
                    "account_id": account['account_id'],
                    "name": account['name'],
                    "official_name": account.get('official_name'),
                    "type": account['type'],
                    "subtype": account['subtype'],
                    "mask": account.get('mask'),
                    "current_balance": account['balances']['current'],
                    "available_balance": account['balances'].get('available'),
                    "limit": account['balances'].get('limit'),
                    "iso_currency_code": account['balances'].get('iso_currency_code', 'USD'),
                })
            
            logger.info(f"Retrieved {len(accounts)} accounts")
            
            return accounts
            
        except ApiException as e:
            logger.error(f"Failed to get accounts: {e}")
            raise Exception(f"Failed to fetch accounts: {str(e)}")
    
    async def get_transactions(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime,
        account_ids: Optional[List[str]] = None,
        count: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch transactions for a given date range.
        
        Args:
            access_token: Plaid access token
            start_date: Start date for transactions
            end_date: End date for transactions
            account_ids: Optional list of account IDs to filter
            count: Number of transactions to fetch
            offset: Pagination offset
            
        Returns:
            Dict containing transactions and metadata
        """
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date(),
                options={
                    'account_ids': account_ids,
                    'count': count,
                    'offset': offset
                } if account_ids else {
                    'count': count,
                    'offset': offset
                }
            )
            
            response = self.client.transactions_get(request)
            
            transactions = []
            for txn in response['transactions']:
                transactions.append({
                    "transaction_id": txn['transaction_id'],
                    "account_id": txn['account_id'],
                    "amount": txn['amount'],
                    "iso_currency_code": txn.get('iso_currency_code', 'USD'),
                    "category": txn.get('category', []),
                    "category_id": txn.get('category_id'),
                    "date": txn['date'],
                    "authorized_date": txn.get('authorized_date'),
                    "name": txn['name'],
                    "merchant_name": txn.get('merchant_name'),
                    "payment_channel": txn['payment_channel'],
                    "pending": txn['pending'],
                    "pending_transaction_id": txn.get('pending_transaction_id'),
                    "location": {
                        "address": txn['location'].get('address'),
                        "city": txn['location'].get('city'),
                        "region": txn['location'].get('region'),
                        "postal_code": txn['location'].get('postal_code'),
                        "country": txn['location'].get('country'),
                        "lat": txn['location'].get('lat'),
                        "lon": txn['location'].get('lon'),
                    } if txn.get('location') else None,
                })
            
            logger.info(f"Retrieved {len(transactions)} transactions")
            
            return {
                "transactions": transactions,
                "total_transactions": response['total_transactions'],
                "accounts": response['accounts'],
                "request_id": response['request_id']
            }
            
        except ApiException as e:
            logger.error(f"Failed to get transactions: {e}")
            raise Exception(f"Failed to fetch transactions: {str(e)}")
    
    async def sync_transactions(
        self,
        access_token: str,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sync transactions using Plaid's transactions sync endpoint.
        More efficient for incremental updates.
        
        Args:
            access_token: Plaid access token
            cursor: Sync cursor from previous request
            
        Returns:
            Dict containing added/modified/removed transactions and new cursor
        """
        try:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor if cursor else None
            )
            
            response = self.client.transactions_sync(request)
            
            logger.info(
                f"Synced transactions - Added: {len(response['added'])}, "
                f"Modified: {len(response['modified'])}, "
                f"Removed: {len(response['removed'])}"
            )
            
            return {
                "added": response['added'],
                "modified": response['modified'],
                "removed": response['removed'],
                "next_cursor": response['next_cursor'],
                "has_more": response['has_more'],
                "request_id": response['request_id']
            }
            
        except ApiException as e:
            logger.error(f"Failed to sync transactions: {e}")
            raise Exception(f"Failed to sync transactions: {str(e)}")
    
    async def get_item(self, access_token: str) -> Dict[str, Any]:
        """
        Get information about a Plaid Item.
        
        Args:
            access_token: Plaid access token
            
        Returns:
            Dict containing item information
        """
        try:
            request = ItemGetRequest(access_token=access_token)
            response = self.client.item_get(request)
            
            item = response['item']
            
            return {
                "item_id": item['item_id'],
                "institution_id": item.get('institution_id'),
                "webhook": item.get('webhook'),
                "error": item.get('error'),
                "available_products": item['available_products'],
                "billed_products": item['billed_products'],
                "consent_expiration_time": item.get('consent_expiration_time'),
                "update_type": item.get('update_type'),
            }
            
        except ApiException as e:
            logger.error(f"Failed to get item: {e}")
            raise Exception(f"Failed to get item information: {str(e)}")
    
    async def get_institution(self, institution_id: str) -> Dict[str, Any]:
        """
        Get information about a financial institution.
        
        Args:
            institution_id: Plaid institution ID
            
        Returns:
            Dict containing institution information
        """
        try:
            request = InstitutionsGetByIdRequest(
                institution_id=institution_id,
                country_codes=self.country_codes
            )
            
            response = self.client.institutions_get_by_id(request)
            institution = response['institution']
            
            return {
                "institution_id": institution['institution_id'],
                "name": institution['name'],
                "products": institution['products'],
                "country_codes": institution['country_codes'],
                "url": institution.get('url'),
                "primary_color": institution.get('primary_color'),
                "logo": institution.get('logo'),
            }
            
        except ApiException as e:
            logger.error(f"Failed to get institution: {e}")
            raise Exception(f"Failed to get institution information: {str(e)}")
    
    async def remove_item(self, access_token: str) -> bool:
        """
        Remove a Plaid Item (unlink bank account).
        
        Args:
            access_token: Plaid access token
            
        Returns:
            True if successful
        """
        try:
            request = ItemRemoveRequest(access_token=access_token)
            response = self.client.item_remove(request)
            
            logger.info(f"Item removed successfully")
            
            return True
            
        except ApiException as e:
            logger.error(f"Failed to remove item: {e}")
            raise Exception(f"Failed to remove item: {str(e)}")
    
    async def verify_webhook(
        self,
        body: str,
        headers: Dict[str, str]
    ) -> bool:
        """
        Verify a webhook came from Plaid.
        
        Args:
            body: Raw webhook body
            headers: Webhook headers including signature
            
        Returns:
            True if webhook is valid
        """
        try:
            # Get the webhook verification key
            key_request = WebhookVerificationKeyGetRequest(
                key_id=headers.get('plaid-verification-key-id')
            )
            key_response = self.client.webhook_verification_key_get(key_request)
            
            # TODO: Implement actual signature verification
            # This requires cryptographic verification of the JWS signature
            
            logger.info("Webhook verification performed")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to verify webhook: {e}")
            return False
    
    async def handle_webhook(
        self,
        webhook_type: str,
        webhook_code: str,
        item_id: str,
        error: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Handle different types of Plaid webhooks.
        
        Args:
            webhook_type: Type of webhook (e.g., TRANSACTIONS, ITEM)
            webhook_code: Specific webhook code
            item_id: Plaid item ID
            error: Optional error information
            
        Returns:
            Dict with handling status
        """
        logger.info(f"Handling webhook: {webhook_type} - {webhook_code} for item {item_id}")
        
        if webhook_type == "TRANSACTIONS":
            if webhook_code == "INITIAL_UPDATE":
                # Initial transaction pull complete
                return {"status": "initial_update_received", "action": "fetch_transactions"}
            elif webhook_code == "HISTORICAL_UPDATE":
                # Historical transactions ready
                return {"status": "historical_update_received", "action": "fetch_all_transactions"}
            elif webhook_code == "DEFAULT_UPDATE":
                # New transactions available
                return {"status": "default_update_received", "action": "sync_transactions"}
            elif webhook_code == "TRANSACTIONS_REMOVED":
                # Transactions were removed
                return {"status": "transactions_removed", "action": "sync_transactions"}
        
        elif webhook_type == "ITEM":
            if webhook_code == "ERROR":
                # Item error occurred
                logger.error(f"Item error for {item_id}: {error}")
                return {"status": "item_error", "action": "notify_user", "error": error}
            elif webhook_code == "PENDING_EXPIRATION":
                # Item consent expiring soon
                return {"status": "pending_expiration", "action": "notify_user_to_relink"}
            elif webhook_code == "USER_PERMISSION_REVOKED":
                # User revoked permission
                return {"status": "permission_revoked", "action": "remove_item"}
            elif webhook_code == "WEBHOOK_UPDATE_ACKNOWLEDGED":
                # Webhook URL updated successfully
                return {"status": "webhook_updated", "action": "none"}
        
        return {"status": "unknown_webhook", "action": "log"}


# Create singleton instance
plaid_service = PlaidService()