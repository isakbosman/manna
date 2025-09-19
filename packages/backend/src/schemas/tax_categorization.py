"""Pydantic schemas for tax categorization system."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID


# Base schemas
class TaxCategoryBase(BaseModel):
    """Base schema for tax categories."""
    category_code: str = Field(..., max_length=20)
    category_name: str = Field(..., max_length=255)
    tax_form: str = Field(..., max_length=50)
    tax_line: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    deduction_type: Optional[str] = Field(None, max_length=50)
    percentage_limit: Optional[Decimal] = Field(None, ge=0, le=100)
    dollar_limit: Optional[Decimal] = Field(None, ge=0)
    carryover_allowed: bool = False
    documentation_required: bool = False
    is_business_expense: bool = True
    is_active: bool = True
    effective_date: date
    expiration_date: Optional[date] = None
    irs_reference: Optional[str] = Field(None, max_length=100)
    keywords: List[str] = Field(default_factory=list)
    exclusions: List[str] = Field(default_factory=list)
    special_rules: Dict[str, Any] = Field(default_factory=dict)

    @validator('tax_form')
    def validate_tax_form(cls, v):
        allowed_forms = ['Schedule C', 'Schedule E', 'Form 8829', 'Form 4562', 'Schedule A']
        if v not in allowed_forms:
            raise ValueError(f'tax_form must be one of: {allowed_forms}')
        return v

    @validator('deduction_type')
    def validate_deduction_type(cls, v):
        if v is not None:
            allowed_types = ['ordinary', 'capital', 'itemized', 'above_line', 'business']
            if v not in allowed_types:
                raise ValueError(f'deduction_type must be one of: {allowed_types}')
        return v


class TaxCategoryCreate(TaxCategoryBase):
    """Schema for creating tax categories."""
    pass


class TaxCategoryUpdate(BaseModel):
    """Schema for updating tax categories."""
    category_name: Optional[str] = Field(None, max_length=255)
    tax_line: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    deduction_type: Optional[str] = Field(None, max_length=50)
    percentage_limit: Optional[Decimal] = Field(None, ge=0, le=100)
    dollar_limit: Optional[Decimal] = Field(None, ge=0)
    carryover_allowed: Optional[bool] = None
    documentation_required: Optional[bool] = None
    is_active: Optional[bool] = None
    expiration_date: Optional[date] = None
    keywords: Optional[List[str]] = None
    exclusions: Optional[List[str]] = None
    special_rules: Optional[Dict[str, Any]] = None


class TaxCategory(TaxCategoryBase):
    """Schema for tax category responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Chart of Accounts schemas
class ChartOfAccountBase(BaseModel):
    """Base schema for chart of accounts."""
    account_code: str = Field(..., max_length=20)
    account_name: str = Field(..., max_length=255)
    account_type: str = Field(..., max_length=50)
    parent_account_id: Optional[UUID] = None
    description: Optional[str] = None
    normal_balance: str = Field(..., max_length=10)
    is_active: bool = True
    tax_category: Optional[str] = Field(None, max_length=100)
    tax_line_mapping: Optional[str] = Field(None, max_length=100)
    requires_1099: bool = False
    account_metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('account_type')
    def validate_account_type(cls, v):
        allowed_types = ['asset', 'liability', 'equity', 'revenue', 'expense', 'contra_asset', 'contra_liability', 'contra_equity']
        if v not in allowed_types:
            raise ValueError(f'account_type must be one of: {allowed_types}')
        return v

    @validator('normal_balance')
    def validate_normal_balance(cls, v):
        if v not in ['debit', 'credit']:
            raise ValueError('normal_balance must be either "debit" or "credit"')
        return v


class ChartOfAccountCreate(ChartOfAccountBase):
    """Schema for creating chart of accounts."""
    pass


class ChartOfAccountUpdate(BaseModel):
    """Schema for updating chart of accounts."""
    account_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    tax_category: Optional[str] = Field(None, max_length=100)
    tax_line_mapping: Optional[str] = Field(None, max_length=100)
    requires_1099: Optional[bool] = None
    account_metadata: Optional[Dict[str, Any]] = None


class ChartOfAccount(ChartOfAccountBase):
    """Schema for chart of account responses."""
    id: UUID
    user_id: UUID
    is_system_account: bool
    current_balance: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Business Expense Tracking schemas
class BusinessExpenseTrackingBase(BaseModel):
    """Base schema for business expense tracking."""
    business_purpose: Optional[str] = None
    business_percentage: Decimal = Field(default=Decimal("100.00"), ge=0, le=100)
    receipt_required: bool = False
    receipt_attached: bool = False
    receipt_url: Optional[str] = Field(None, max_length=500)
    mileage_start_location: Optional[str] = Field(None, max_length=255)
    mileage_end_location: Optional[str] = Field(None, max_length=255)
    miles_driven: Optional[Decimal] = Field(None, ge=0)
    vehicle_info: Dict[str, Any] = Field(default_factory=dict)
    depreciation_method: Optional[str] = Field(None, max_length=50)
    depreciation_years: Optional[int] = Field(None, gt=0)
    section_179_eligible: bool = False
    substantiation_notes: Optional[str] = None


class BusinessExpenseTrackingCreate(BusinessExpenseTrackingBase):
    """Schema for creating business expense tracking."""
    transaction_id: UUID


class BusinessExpenseTrackingUpdate(BusinessExpenseTrackingBase):
    """Schema for updating business expense tracking."""
    pass


class BusinessExpenseTracking(BusinessExpenseTrackingBase):
    """Schema for business expense tracking responses."""
    id: UUID
    transaction_id: UUID
    user_id: UUID
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Category Mapping schemas
class CategoryMappingBase(BaseModel):
    """Base schema for category mappings."""
    source_category_id: UUID
    chart_account_id: UUID
    tax_category_id: UUID
    confidence_score: Decimal = Field(default=Decimal("1.0000"), ge=0, le=1)
    is_user_defined: bool = True
    is_active: bool = True
    effective_date: date
    expiration_date: Optional[date] = None
    business_percentage_default: Decimal = Field(default=Decimal("100.00"), ge=0, le=100)
    always_require_receipt: bool = False
    auto_substantiation_rules: Dict[str, Any] = Field(default_factory=dict)
    mapping_notes: Optional[str] = None


class CategoryMappingCreate(CategoryMappingBase):
    """Schema for creating category mappings."""
    pass


class CategoryMappingUpdate(BaseModel):
    """Schema for updating category mappings."""
    chart_account_id: Optional[UUID] = None
    tax_category_id: Optional[UUID] = None
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None
    expiration_date: Optional[date] = None
    business_percentage_default: Optional[Decimal] = Field(None, ge=0, le=100)
    always_require_receipt: Optional[bool] = None
    auto_substantiation_rules: Optional[Dict[str, Any]] = None
    mapping_notes: Optional[str] = None


class CategoryMapping(CategoryMappingBase):
    """Schema for category mapping responses."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Tax Categorization Request/Response schemas
class TaxCategorizationRequest(BaseModel):
    """Schema for tax categorization requests."""
    tax_category_id: Optional[UUID] = None
    chart_account_id: Optional[UUID] = None
    business_percentage: Decimal = Field(default=Decimal("100.00"), ge=0, le=100)
    business_purpose: Optional[str] = None
    override_automated: bool = False


class TaxCategorizationResponse(BaseModel):
    """Schema for tax categorization responses."""
    success: bool
    transaction_id: UUID
    tax_category: Optional[str] = None
    chart_account: Optional[str] = None
    deductible_amount: float = 0
    requires_substantiation: bool = False


class BulkTaxCategorizationRequest(BaseModel):
    """Schema for bulk tax categorization requests."""
    transaction_ids: List[UUID]
    tax_category_id: Optional[UUID] = None
    chart_account_id: Optional[UUID] = None
    business_percentage: Decimal = Field(default=Decimal("100.00"), ge=0, le=100)


class BulkTaxCategorizationResponse(BaseModel):
    """Schema for bulk tax categorization responses."""
    success_count: int
    error_count: int
    results: List[TaxCategorizationResponse]
    errors: List[Dict[str, Any]]


# Tax Summary schemas
class TaxCategorySummary(BaseModel):
    """Schema for tax category summary."""
    category_name: str
    tax_form: str
    tax_line: Optional[str]
    total_amount: float
    transaction_count: int
    requires_substantiation: int


class TaxSummaryResponse(BaseModel):
    """Schema for tax summary responses."""
    tax_year: int
    total_deductions: float
    categories: Dict[str, TaxCategorySummary]
    transaction_count: int


class ScheduleCLineItem(BaseModel):
    """Schema for Schedule C line items."""
    line_description: str
    amount: float
    transaction_count: int


class ScheduleCExportResponse(BaseModel):
    """Schema for Schedule C export responses."""
    tax_year: int
    schedule_c_lines: Dict[str, ScheduleCLineItem]
    total_expenses: float


# Trial Balance schemas
class TrialBalanceAccount(BaseModel):
    """Schema for trial balance account."""
    account_code: str
    account_name: str
    account_type: str
    normal_balance: str
    balance: float
    debit_balance: float
    credit_balance: float


class TrialBalanceResponse(BaseModel):
    """Schema for trial balance responses."""
    accounts: List[TrialBalanceAccount]
    total_debits: float
    total_credits: float
    as_of_date: Optional[str]
    is_balanced: bool


# Financial Statements schemas
class FinancialStatementSection(BaseModel):
    """Schema for financial statement sections."""
    accounts: List[TrialBalanceAccount]
    total: float


class BalanceSheetResponse(BaseModel):
    """Schema for balance sheet responses."""
    assets: FinancialStatementSection
    liabilities: FinancialStatementSection
    equity: FinancialStatementSection
    total_liabilities_and_equity: float


class IncomeStatementResponse(BaseModel):
    """Schema for income statement responses."""
    revenue: FinancialStatementSection
    expenses: FinancialStatementSection
    net_income: float


class FinancialStatementsResponse(BaseModel):
    """Schema for financial statements responses."""
    balance_sheet: BalanceSheetResponse
    income_statement: IncomeStatementResponse
    as_of_date: Optional[str]