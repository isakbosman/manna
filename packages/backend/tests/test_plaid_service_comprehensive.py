"""
Comprehensive tests for Plaid service integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from plaid.exceptions import ApiException

from src.services.plaid_service import PlaidService


class TestPlaidService:
    """Comprehensive test suite for Plaid service."""
    
    @pytest.fixture
    def plaid_service(self):
        """Create a PlaidService instance for testing."""
        return PlaidService()
    
    @pytest.fixture
    def mock_api_client(self):
        """Mock Plaid API client."""
        with patch('src.services.plaid_service.plaid_api.PlaidApi') as mock_api:
            yield mock_api.return_value
    
    async def test_create_link_token_success(self, plaid_service, mock_api_client):
        """Test successful link token creation."""
        # Mock response
        mock_response = {
            'link_token': 'link-test-123',
            'expiration': '2024-12-31T23:59:59Z',
            'request_id': 'req-123'
        }
        mock_api_client.link_token_create.return_value = mock_response
        
        result = await plaid_service.create_link_token(
            user_id="user_123",
            user_name="Test User"
        )
        
        assert result['link_token'] == 'link-test-123'
        assert result['expiration'] == '2024-12-31T23:59:59Z'
        assert result['request_id'] == 'req-123'
        
        # Verify the API was called with correct parameters
        mock_api_client.link_token_create.assert_called_once()
        
    async def test_create_link_token_with_access_token(self, plaid_service, mock_api_client):
        """Test link token creation with existing access token (update mode)."""
        mock_response = {
            'link_token': 'link-update-123',
            'expiration': '2024-12-31T23:59:59Z',
            'request_id': 'req-123'
        }
        mock_api_client.link_token_create.return_value = mock_response
        
        result = await plaid_service.create_link_token(
            user_id="user_123",
            user_name="Test User",
            access_token="access-123"
        )
        
        assert result['link_token'] == 'link-update-123'
        mock_api_client.link_token_create.assert_called_once()
        
    async def test_create_link_token_api_exception(self, plaid_service, mock_api_client):
        """Test link token creation when API raises exception."""
        mock_api_client.link_token_create.side_effect = ApiException("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await plaid_service.create_link_token(
                user_id="user_123",
                user_name="Test User"
            )
        
        assert "Failed to create Plaid link token" in str(exc_info.value)
        
    async def test_exchange_public_token_success(self, plaid_service, mock_api_client):
        """Test successful public token exchange."""
        mock_response = {
            'access_token': 'access-test-123',
            'item_id': 'item-test-123'
        }
        mock_api_client.item_public_token_exchange.return_value = mock_response
        
        result = await plaid_service.exchange_public_token("public_token_123")
        
        assert result == 'access-test-123'
        mock_api_client.item_public_token_exchange.assert_called_once()
        
    async def test_exchange_public_token_api_exception(self, plaid_service, mock_api_client):
        """Test public token exchange when API raises exception."""
        mock_api_client.item_public_token_exchange.side_effect = ApiException("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await plaid_service.exchange_public_token("public_token_123")
        
        assert "Failed to exchange public token" in str(exc_info.value)
        
    async def test_get_accounts_success(self, plaid_service, mock_api_client):
        """Test successful account retrieval."""
        mock_response = {
            'accounts': [
                {
                    'account_id': 'acc_123',
                    'name': 'Checking',
                    'official_name': 'Test Checking Account',
                    'type': 'depository',
                    'subtype': 'checking',
                    'mask': '1234',
                    'balances': {
                        'current': 1000.00,
                        'available': 900.00,
                        'limit': None,
                        'iso_currency_code': 'USD'
                    }
                }
            ]
        }
        mock_api_client.accounts_get.return_value = mock_response
        
        result = await plaid_service.get_accounts("access_token_123")
        
        assert len(result) == 1
        account = result[0]
        assert account['account_id'] == 'acc_123'
        assert account['name'] == 'Checking'
        assert account['current_balance'] == 1000.00
        assert account['available_balance'] == 900.00
        assert account['iso_currency_code'] == 'USD'
        
    async def test_get_accounts_api_exception(self, plaid_service, mock_api_client):
        """Test account retrieval when API raises exception."""
        mock_api_client.accounts_get.side_effect = ApiException("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await plaid_service.get_accounts("access_token_123")
        
        assert "Failed to fetch accounts" in str(exc_info.value)
        
    async def test_get_transactions_success(self, plaid_service, mock_api_client):
        """Test successful transaction retrieval."""
        mock_response = {
            'transactions': [
                {
                    'transaction_id': 'txn_123',
                    'account_id': 'acc_123',
                    'amount': 25.50,
                    'iso_currency_code': 'USD',
                    'category': ['Food and Drink', 'Restaurants'],
                    'category_id': 'cat_123',
                    'date': '2024-01-01',
                    'authorized_date': '2024-01-01',
                    'name': 'Restaurant Purchase',
                    'merchant_name': 'Test Restaurant',
                    'payment_channel': 'in store',
                    'pending': False,
                    'location': {
                        'address': '123 Main St',
                        'city': 'San Francisco',
                        'region': 'CA',
                        'postal_code': '94102',
                        'country': 'US',
                        'lat': 37.7749,
                        'lon': -122.4194
                    }
                }
            ],
            'total_transactions': 1,
            'accounts': [],
            'request_id': 'req_123'
        }
        mock_api_client.transactions_get.return_value = mock_response
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = await plaid_service.get_transactions(
            "access_token_123",
            start_date,
            end_date
        )
        
        assert result['total_transactions'] == 1
        assert len(result['transactions']) == 1
        
        txn = result['transactions'][0]
        assert txn['transaction_id'] == 'txn_123'
        assert txn['amount'] == 25.50
        assert txn['name'] == 'Restaurant Purchase'
        assert txn['location']['city'] == 'San Francisco'
        
    async def test_get_transactions_with_filters(self, plaid_service, mock_api_client):
        """Test transaction retrieval with account ID filters."""
        mock_response = {
            'transactions': [],
            'total_transactions': 0,
            'accounts': [],
            'request_id': 'req_123'
        }
        mock_api_client.transactions_get.return_value = mock_response
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        account_ids = ['acc_123', 'acc_456']
        
        result = await plaid_service.get_transactions(
            "access_token_123",
            start_date,
            end_date,
            account_ids=account_ids,
            count=50,
            offset=10
        )
        
        assert result['total_transactions'] == 0
        mock_api_client.transactions_get.assert_called_once()
        
    async def test_sync_transactions_success(self, plaid_service, mock_api_client):
        """Test successful transaction sync."""
        mock_response = {
            'added': [
                {
                    'transaction_id': 'txn_new_123',
                    'account_id': 'acc_123',
                    'amount': 15.50,
                    'date': '2024-01-02',
                    'name': 'New Transaction'
                }
            ],
            'modified': [],
            'removed': [],
            'next_cursor': 'cursor_456',
            'has_more': False,
            'request_id': 'req_123'
        }
        mock_api_client.transactions_sync.return_value = mock_response
        
        result = await plaid_service.sync_transactions(
            "access_token_123",
            cursor="cursor_123"
        )
        
        assert len(result['added']) == 1
        assert len(result['modified']) == 0
        assert len(result['removed']) == 0
        assert result['next_cursor'] == 'cursor_456'
        assert result['has_more'] is False
        
    async def test_sync_transactions_without_cursor(self, plaid_service, mock_api_client):
        """Test transaction sync without initial cursor."""
        mock_response = {
            'added': [],
            'modified': [],
            'removed': [],
            'next_cursor': 'cursor_123',
            'has_more': True,
            'request_id': 'req_123'
        }
        mock_api_client.transactions_sync.return_value = mock_response
        
        result = await plaid_service.sync_transactions("access_token_123")
        
        assert result['next_cursor'] == 'cursor_123'
        assert result['has_more'] is True
        
    async def test_get_item_success(self, plaid_service, mock_api_client):
        """Test successful item retrieval."""
        mock_response = {
            'item': {
                'item_id': 'item_123',
                'institution_id': 'ins_123',
                'webhook': 'https://example.com/webhook',
                'error': None,
                'available_products': ['transactions'],
                'billed_products': ['transactions'],
                'consent_expiration_time': None,
                'update_type': 'background'
            }
        }
        mock_api_client.item_get.return_value = mock_response
        
        result = await plaid_service.get_item("access_token_123")
        
        assert result['item_id'] == 'item_123'
        assert result['institution_id'] == 'ins_123'
        assert result['webhook'] == 'https://example.com/webhook'
        assert 'transactions' in result['available_products']
        
    async def test_get_institution_success(self, plaid_service, mock_api_client):
        """Test successful institution retrieval."""
        mock_response = {
            'institution': {
                'institution_id': 'ins_123',
                'name': 'Test Bank',
                'products': ['transactions'],
                'country_codes': ['US'],
                'url': 'https://testbank.com',
                'primary_color': '#1f77b4',
                'logo': 'https://testbank.com/logo.png'
            }
        }
        mock_api_client.institutions_get_by_id.return_value = mock_response
        
        result = await plaid_service.get_institution("ins_123")
        
        assert result['institution_id'] == 'ins_123'
        assert result['name'] == 'Test Bank'
        assert result['url'] == 'https://testbank.com'
        assert result['primary_color'] == '#1f77b4'
        
    async def test_remove_item_success(self, plaid_service, mock_api_client):
        """Test successful item removal."""
        mock_response = {'request_id': 'req_123'}
        mock_api_client.item_remove.return_value = mock_response
        
        result = await plaid_service.remove_item("access_token_123")
        
        assert result is True
        mock_api_client.item_remove.assert_called_once()
        
    async def test_remove_item_api_exception(self, plaid_service, mock_api_client):
        """Test item removal when API raises exception."""
        mock_api_client.item_remove.side_effect = ApiException("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await plaid_service.remove_item("access_token_123")
        
        assert "Failed to remove item" in str(exc_info.value)
        
    async def test_verify_webhook_success(self, plaid_service, mock_api_client):
        """Test successful webhook verification."""
        mock_response = {'key': 'verification_key_data'}
        mock_api_client.webhook_verification_key_get.return_value = mock_response
        
        headers = {'plaid-verification-key-id': 'key_123'}
        result = await plaid_service.verify_webhook("webhook_body", headers)
        
        assert result is True
        
    async def test_verify_webhook_api_exception(self, plaid_service, mock_api_client):
        """Test webhook verification when API raises exception."""
        mock_api_client.webhook_verification_key_get.side_effect = ApiException("API Error")
        
        headers = {'plaid-verification-key-id': 'key_123'}
        result = await plaid_service.verify_webhook("webhook_body", headers)
        
        assert result is False
        
    async def test_handle_webhook_transactions_initial_update(self, plaid_service):
        """Test handling of TRANSACTIONS INITIAL_UPDATE webhook."""
        result = await plaid_service.handle_webhook(
            "TRANSACTIONS",
            "INITIAL_UPDATE",
            "item_123"
        )
        
        assert result['status'] == 'initial_update_received'
        assert result['action'] == 'fetch_transactions'
        
    async def test_handle_webhook_transactions_default_update(self, plaid_service):
        """Test handling of TRANSACTIONS DEFAULT_UPDATE webhook."""
        result = await plaid_service.handle_webhook(
            "TRANSACTIONS",
            "DEFAULT_UPDATE",
            "item_123"
        )
        
        assert result['status'] == 'default_update_received'
        assert result['action'] == 'sync_transactions'
        
    async def test_handle_webhook_transactions_historical_update(self, plaid_service):
        """Test handling of TRANSACTIONS HISTORICAL_UPDATE webhook."""
        result = await plaid_service.handle_webhook(
            "TRANSACTIONS",
            "HISTORICAL_UPDATE",
            "item_123"
        )
        
        assert result['status'] == 'historical_update_received'
        assert result['action'] == 'fetch_all_transactions'
        
    async def test_handle_webhook_transactions_removed(self, plaid_service):
        """Test handling of TRANSACTIONS TRANSACTIONS_REMOVED webhook."""
        result = await plaid_service.handle_webhook(
            "TRANSACTIONS",
            "TRANSACTIONS_REMOVED",
            "item_123"
        )
        
        assert result['status'] == 'transactions_removed'
        assert result['action'] == 'sync_transactions'
        
    async def test_handle_webhook_item_error(self, plaid_service):
        """Test handling of ITEM ERROR webhook."""
        error_data = {'error_type': 'INVALID_CREDENTIALS'}
        
        result = await plaid_service.handle_webhook(
            "ITEM",
            "ERROR",
            "item_123",
            error=error_data
        )
        
        assert result['status'] == 'item_error'
        assert result['action'] == 'notify_user'
        assert result['error'] == error_data
        
    async def test_handle_webhook_item_pending_expiration(self, plaid_service):
        """Test handling of ITEM PENDING_EXPIRATION webhook."""
        result = await plaid_service.handle_webhook(
            "ITEM",
            "PENDING_EXPIRATION",
            "item_123"
        )
        
        assert result['status'] == 'pending_expiration'
        assert result['action'] == 'notify_user_to_relink'
        
    async def test_handle_webhook_item_permission_revoked(self, plaid_service):
        """Test handling of ITEM USER_PERMISSION_REVOKED webhook."""
        result = await plaid_service.handle_webhook(
            "ITEM",
            "USER_PERMISSION_REVOKED",
            "item_123"
        )
        
        assert result['status'] == 'permission_revoked'
        assert result['action'] == 'remove_item'
        
    async def test_handle_webhook_item_webhook_acknowledged(self, plaid_service):
        """Test handling of ITEM WEBHOOK_UPDATE_ACKNOWLEDGED webhook."""
        result = await plaid_service.handle_webhook(
            "ITEM",
            "WEBHOOK_UPDATE_ACKNOWLEDGED",
            "item_123"
        )
        
        assert result['status'] == 'webhook_updated'
        assert result['action'] == 'none'
        
    async def test_handle_webhook_unknown(self, plaid_service):
        """Test handling of unknown webhook types."""
        result = await plaid_service.handle_webhook(
            "UNKNOWN_TYPE",
            "UNKNOWN_CODE",
            "item_123"
        )
        
        assert result['status'] == 'unknown_webhook'
        assert result['action'] == 'log'