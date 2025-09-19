# Tax Categorization API Service

This document provides comprehensive documentation for the tax categorization API service implementation.

## Overview

The tax categorization system provides frontend API integration for managing business expense categorization for tax purposes, particularly Schedule C business tax filing. It includes services for:

- Transaction tax categorization (single and bulk)
- Tax category management
- Tax summary and reporting
- Chart of accounts management

## API Services

### taxCategorizationApi

Main service for tax categorization operations.

#### Methods

##### getTaxCategories()
Get all available tax categories.

```typescript
const categories = await taxCategorizationApi.getTaxCategories();
```

**Returns:** `TaxCategory[]`

##### categorizeTransaction(transactionId, data)
Categorize a single transaction.

```typescript
await taxCategorizationApi.categorizeTransaction('txn_123', {
  tax_category_id: 'cat_456',
  business_use_percentage: 100,
  business_purpose: 'Client meeting lunch',
  receipt_url: 'https://example.com/receipt.pdf'
});
```

**Parameters:**
- `transactionId: string` - ID of the transaction to categorize
- `data: CategorizeSingleRequest` - Categorization data

**Returns:** `TaxCategorization`

##### bulkCategorizeTransactions(data)
Categorize multiple transactions at once.

```typescript
await taxCategorizationApi.bulkCategorizeTransactions({
  transaction_ids: ['txn_123', 'txn_456'],
  tax_category_id: 'cat_789',
  business_use_percentage: 100,
  business_purpose: 'Office supplies'
});
```

**Parameters:**
- `data: CategorizeBulkRequest` - Bulk categorization data

**Returns:** `TaxCategorization[]`

##### getTaxSummary(params)
Get tax summary for a date range or tax year.

```typescript
const summary = await taxCategorizationApi.getTaxSummary({
  tax_year: 2024
});

// Or by date range
const summary = await taxCategorizationApi.getTaxSummary({
  start_date: '2024-01-01',
  end_date: '2024-12-31'
});
```

**Parameters:**
- `params.tax_year?: number` - Tax year to get summary for
- `params.start_date?: string` - Start date (YYYY-MM-DD)
- `params.end_date?: string` - End date (YYYY-MM-DD)

**Returns:** `TaxSummary`

##### updateCategorization(categorizationId, data)
Update an existing tax categorization.

```typescript
await taxCategorizationApi.updateCategorization('cat_123', {
  business_use_percentage: 75,
  business_purpose: 'Updated purpose'
});
```

**Parameters:**
- `categorizationId: string` - ID of the categorization to update
- `data: Partial<CategorizeSingleRequest>` - Updated data

**Returns:** `TaxCategorization`

##### deleteCategorization(categorizationId)
Delete a tax categorization.

```typescript
await taxCategorizationApi.deleteCategorization('cat_123');
```

**Parameters:**
- `categorizationId: string` - ID of the categorization to delete

**Returns:** `void`

### chartOfAccountsApi

Service for managing chart of accounts.

#### Methods

##### getChartOfAccounts()
Get all chart of accounts.

```typescript
const accounts = await chartOfAccountsApi.getChartOfAccounts();
```

**Returns:** `ChartOfAccount[]`

##### createAccount(data)
Create a new account.

```typescript
await chartOfAccountsApi.createAccount({
  name: 'Office Supplies',
  account_type: 'expense',
  parent_id: 'parent_123'
});
```

**Parameters:**
- `data.name: string` - Account name
- `data.account_type: 'asset' | 'liability' | 'equity' | 'income' | 'expense'` - Account type
- `data.parent_id?: string` - Parent account ID
- `data.balance?: number` - Initial balance

**Returns:** `ChartOfAccount`

##### updateAccount(accountId, data)
Update an existing account.

```typescript
await chartOfAccountsApi.updateAccount('acc_123', {
  name: 'Updated Name',
  is_active: false
});
```

**Parameters:**
- `accountId: string` - Account ID to update
- `data: Partial<ChartOfAccount>` - Updated data

**Returns:** `ChartOfAccount`

##### deleteAccount(accountId)
Delete an account.

```typescript
await chartOfAccountsApi.deleteAccount('acc_123');
```

**Parameters:**
- `accountId: string` - Account ID to delete

**Returns:** `void`

## Type Definitions

### TaxCategory
```typescript
interface TaxCategory {
  id: string;
  name: string;
  schedule_c_line: string;
  description: string;
  is_deductible: boolean;
  requires_receipt: boolean;
  has_business_use_percentage: boolean;
  is_meals_50_percent: boolean;
  is_vehicle_expense: boolean;
  created_at: string;
  updated_at: string;
}
```

### TaxCategorization
```typescript
interface TaxCategorization {
  id: string;
  transaction_id: string;
  tax_category_id: string;
  business_use_percentage: number;
  business_purpose?: string;
  receipt_url?: string;
  mileage?: number;
  created_at: string;
  updated_at: string;
}
```

### CategorizeSingleRequest
```typescript
interface CategorizeSingleRequest {
  tax_category_id: string;
  business_use_percentage: number;
  business_purpose?: string;
  receipt_url?: string;
  mileage?: number;
}
```

### CategorizeBulkRequest
```typescript
interface CategorizeBulkRequest {
  transaction_ids: string[];
  tax_category_id: string;
  business_use_percentage: number;
  business_purpose?: string;
  receipt_url?: string;
  mileage?: number;
}
```

### TaxSummary
```typescript
interface TaxSummary {
  tax_year: number;
  total_deductions: number;
  categories: Array<{
    tax_category_id: string;
    category_name: string;
    schedule_c_line: string;
    total_amount: number;
    transaction_count: number;
    documentation_status: 'complete' | 'partial' | 'missing';
  }>;
  documentation_status: {
    total_transactions: number;
    with_receipts: number;
    missing_receipts: number;
    complete_business_purpose: number;
    missing_business_purpose: number;
  };
}
```

### ChartOfAccount
```typescript
interface ChartOfAccount {
  id: string;
  name: string;
  account_type: 'asset' | 'liability' | 'equity' | 'income' | 'expense';
  parent_id?: string;
  balance: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

## Usage with React Query

The API service is designed to work seamlessly with React Query for state management:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { taxCategorizationApi } from '@/services/taxCategorizationApi';

// Load tax categories
const { data: categories, isLoading } = useQuery({
  queryKey: ['tax-categories'],
  queryFn: taxCategorizationApi.getTaxCategories,
});

// Categorize transaction mutation
const queryClient = useQueryClient();
const categorizeMutation = useMutation({
  mutationFn: ({ transactionId, data }) =>
    taxCategorizationApi.categorizeTransaction(transactionId, data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['transactions'] });
    queryClient.invalidateQueries({ queryKey: ['tax-summary'] });
  },
});
```

## Error Handling

All API methods return promises and can throw errors. Implement proper error handling:

```typescript
try {
  const result = await taxCategorizationApi.categorizeTransaction(id, data);
  // Handle success
} catch (error) {
  // Handle error
  console.error('Failed to categorize transaction:', error);
}
```

## Backend API Integration

This service integrates with the following backend endpoints:

- `GET /api/v1/tax/categories` - Get tax categories
- `POST /api/v1/tax/categorize` - Categorize transaction
- `POST /api/v1/tax/bulk-categorize` - Bulk categorize transactions
- `GET /api/v1/tax/summary` - Get tax summary
- `GET /api/v1/chart-of-accounts` - Get chart of accounts
- `POST /api/v1/chart-of-accounts` - Create account
- `PUT /api/v1/chart-of-accounts/{id}` - Update account
- `DELETE /api/v1/chart-of-accounts/{id}` - Delete account

Make sure the backend API is running and accessible at the configured `NEXT_PUBLIC_API_URL`.