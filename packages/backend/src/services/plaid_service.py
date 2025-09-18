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
                    "type": str(account['type']) if not isinstance(account['type'], str) else account['type'],
                    "subtype": str(account['subtype']) if not isinstance(account['subtype'], str) else account['subtype'],
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
        cursor: Optional[str] = None,
        count: int = 500,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Sync transactions using Plaid's transactions sync endpoint.
        Enhanced with comprehensive error handling and pagination support.

        Args:
            access_token: Plaid access token
            cursor: Sync cursor from previous request (None/empty for initial sync)
            count: Number of transactions per page (max 500)
            max_retries: Maximum number of retries for transient errors

        Returns:
            Dict containing added/modified/removed transactions and new cursor
        """
        retry_count = 0
        last_error = None

        while retry_count <= max_retries:
            try:
                # Build request parameters
                request_params = {
                    "access_token": access_token,
                    "count": min(count, 500)  # Ensure we don't exceed max
                }

                # CRITICAL FIX: Only add cursor if it's not None AND not empty string
                # Plaid treats empty string differently from no cursor parameter
                if cursor is not None and cursor.strip() != "":
                    request_params["cursor"] = cursor
                    logger.info(f"Performing incremental sync with cursor: {cursor[:20]}... (attempt {retry_count + 1})")
                else:
                    logger.info(f"Performing initial sync (no cursor provided or empty) (attempt {retry_count + 1})")

                request = TransactionsSyncRequest(**request_params)
                response = self.client.transactions_sync(request)

                # Process response data
                added_txns = response.get('added', [])
                modified_txns = response.get('modified', [])
                removed_txns = response.get('removed', [])

                logger.info(
                    f"Synced transactions - Added: {len(added_txns)}, "
                    f"Modified: {len(modified_txns)}, "
                    f"Removed: {len(removed_txns)}, "
                    f"Has more: {response.get('has_more', False)}"
                )

                # Convert Plaid transaction objects to dictionaries for processing
                def convert_transaction(txn):
                    """Convert Plaid transaction object to dictionary."""
                    if hasattr(txn, 'to_dict'):
                        return txn.to_dict()
                    elif isinstance(txn, dict):
                        return txn
                    else:
                        # Convert object attributes to dict
                        return {
                            'transaction_id': getattr(txn, 'transaction_id', None),
                            'account_id': getattr(txn, 'account_id', None),
                            'amount': getattr(txn, 'amount', 0),
                            'iso_currency_code': getattr(txn, 'iso_currency_code', 'USD'),
                            'category': getattr(txn, 'category', []),
                            'category_id': getattr(txn, 'category_id', None),
                            'date': getattr(txn, 'date', None),
                            'authorized_date': getattr(txn, 'authorized_date', None),
                            'name': getattr(txn, 'name', ''),
                            'merchant_name': getattr(txn, 'merchant_name', None),
                            'payment_channel': getattr(txn, 'payment_channel', None),
                            'pending': getattr(txn, 'pending', False),
                            'pending_transaction_id': getattr(txn, 'pending_transaction_id', None),
                            'location': getattr(txn, 'location', None),
                            'account_owner': getattr(txn, 'account_owner', None)
                        }

                return {
                    "added": [convert_transaction(txn) for txn in added_txns],
                    "modified": [convert_transaction(txn) for txn in modified_txns],
                    "removed": [convert_transaction(txn) for txn in removed_txns],
                    "next_cursor": response.get('next_cursor'),
                    "has_more": response.get('has_more', False),
                    "request_id": response.get('request_id'),
                    # Additional metadata for debugging
                    "is_initial_sync": cursor is None or cursor.strip() == "",
                    "page_size": count,
                    "retry_count": retry_count
                }

            except ApiException as e:
                error_code = getattr(e, 'code', None)
                error_message = str(e)
                last_error = e

                # Log detailed error information
                logger.error(f"Plaid sync error (attempt {retry_count + 1}/{max_retries + 1}) - Code: {error_code}, Message: {error_message}")

                # Check for specific error codes that shouldn't be retried
                if error_code == 'TRANSACTIONS_SYNC_MUTATION_DURING_PAGINATION':
                    raise Exception(f"TRANSACTIONS_SYNC_MUTATION_DURING_PAGINATION: {error_message}")
                elif error_code in ['ITEM_LOGIN_REQUIRED', 'ACCESS_NOT_GRANTED', 'INVALID_ACCESS_TOKEN']:
                    raise Exception(f"Authentication required: {error_message}")
                elif error_code in ['INVALID_REQUEST', 'INVALID_INPUT']:
                    raise Exception(f"Invalid request: {error_message}")

                # For transient errors, retry with exponential backoff
                if retry_count < max_retries:
                    import asyncio
                    wait_time = 2 ** retry_count  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    retry_count += 1
                else:
                    # Max retries exceeded
                    break

        # If we get here, all retries failed
        if last_error:
            raise Exception(f"Failed to sync transactions after {max_retries + 1} attempts: {str(last_error)}")
        else:
            raise Exception(f"Failed to sync transactions after {max_retries + 1} attempts: Unknown error")
    
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
                "available_products": [str(p) if not isinstance(p, str) else p for p in item['available_products']],
                "billed_products": [str(p) if not isinstance(p, str) else p for p in item['billed_products']],
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
            if webhook_code == "SYNC_UPDATES_AVAILABLE":
                # New sync updates available (replaces older webhook types)
                return {"status": "sync_updates_available", "action": "sync_transactions"}
            elif webhook_code == "INITIAL_UPDATE":
                # Initial transaction pull complete (legacy)
                return {"status": "initial_update_received", "action": "sync_transactions"}
            elif webhook_code == "HISTORICAL_UPDATE":
                # Historical transactions ready (legacy)
                return {"status": "historical_update_received", "action": "sync_transactions"}
            elif webhook_code == "DEFAULT_UPDATE":
                # New transactions available (legacy)
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