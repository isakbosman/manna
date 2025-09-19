"""
Pydantic schemas for API request/response validation.
"""

from .user import (
    UserBase, UserCreate, UserUpdate, UserInDB, User,
    UserLogin, Token, TokenData
)
from .account import (
    AccountBase, AccountCreate, AccountUpdate, Account,
    AccountWithInstitution, AccountList, AccountBalance, AccountSyncStatus
)
from .transaction import (
    TransactionBase, TransactionCreate, TransactionUpdate,
    Transaction, TransactionList, TransactionFilter,
    TransactionExport, TransactionCategorization
)
from .plaid import (
    PlaidLinkToken, PlaidPublicTokenExchange,
    PlaidWebhook, PlaidInstitution, PlaidError, PlaidItemStatus
)
from .common import (
    PaginationParams, PaginatedResponse, HealthCheck,
    ErrorResponse, SuccessResponse
)
from .tax_categorization import (
    TaxCategory, TaxCategoryCreate, TaxCategoryUpdate,
    ChartOfAccount, ChartOfAccountCreate, ChartOfAccountUpdate,
    BusinessExpenseTracking, BusinessExpenseTrackingCreate, BusinessExpenseTrackingUpdate,
    CategoryMapping, CategoryMappingCreate, CategoryMappingUpdate,
    TaxCategorizationRequest, TaxCategorizationResponse,
    BulkTaxCategorizationRequest, BulkTaxCategorizationResponse,
    TaxSummaryResponse, ScheduleCExportResponse,
    TrialBalanceResponse, FinancialStatementsResponse
)

__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserInDB", "User",
    "UserLogin", "Token", "TokenData",
    
    # Account schemas
    "AccountBase", "AccountCreate", "AccountUpdate", "Account",
    "AccountWithInstitution", "AccountList", "AccountBalance", "AccountSyncStatus",
    
    # Transaction schemas
    "TransactionBase", "TransactionCreate", "TransactionUpdate",
    "Transaction", "TransactionList", "TransactionFilter",
    "TransactionExport", "TransactionCategorization",
    
    # Plaid schemas
    "PlaidLinkToken", "PlaidPublicTokenExchange",
    "PlaidWebhook", "PlaidInstitution", "PlaidError", "PlaidItemStatus",
    
    # Common schemas
    "PaginationParams", "PaginatedResponse", "HealthCheck",
    "ErrorResponse", "SuccessResponse",

    # Tax categorization schemas
    "TaxCategory", "TaxCategoryCreate", "TaxCategoryUpdate",
    "ChartOfAccount", "ChartOfAccountCreate", "ChartOfAccountUpdate",
    "BusinessExpenseTracking", "BusinessExpenseTrackingCreate", "BusinessExpenseTrackingUpdate",
    "CategoryMapping", "CategoryMappingCreate", "CategoryMappingUpdate",
    "TaxCategorizationRequest", "TaxCategorizationResponse",
    "BulkTaxCategorizationRequest", "BulkTaxCategorizationResponse",
    "TaxSummaryResponse", "ScheduleCExportResponse",
    "TrialBalanceResponse", "FinancialStatementsResponse",
]