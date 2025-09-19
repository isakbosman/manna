/**
 * Tax Categorization API Service
 * Provides typed API methods for tax categorization endpoints
 */

import { api, API_ENDPOINTS } from '@/lib/api-client';

// Tax-related types
export interface TaxCategory {
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

export interface ChartOfAccount {
  id: string;
  name: string;
  account_type: 'asset' | 'liability' | 'equity' | 'income' | 'expense';
  parent_id?: string;
  balance: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaxCategorization {
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

export interface TaxSummary {
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

export interface CategorizeSingleRequest {
  tax_category_id: string;
  business_use_percentage: number;
  business_purpose?: string;
  receipt_url?: string;
  mileage?: number;
}

export interface CategorizeBulkRequest {
  transaction_ids: string[];
  tax_category_id: string;
  business_use_percentage: number;
  business_purpose?: string;
  receipt_url?: string;
  mileage?: number;
}

export interface ScheduleCExport {
  tax_year: number;
  lines: Array<{
    line_number: string;
    description: string;
    amount: number;
  }>;
  total_deductions: number;
  generated_at: string;
}

// Tax Categorization API Service
export const taxCategorizationApi = {
  // Get all tax categories
  async getTaxCategories(): Promise<TaxCategory[]> {
    return api.get<TaxCategory[]>(API_ENDPOINTS.tax.categories);
  },

  // Categorize a single transaction
  async categorizeTransaction(
    transactionId: string,
    data: CategorizeSingleRequest
  ): Promise<TaxCategorization> {
    return api.post<TaxCategorization>(API_ENDPOINTS.tax.categorize, {
      transaction_id: transactionId,
      ...data,
    });
  },

  // Bulk categorize multiple transactions
  async bulkCategorizeTransactions(
    data: CategorizeBulkRequest
  ): Promise<TaxCategorization[]> {
    return api.post<TaxCategorization[]>(API_ENDPOINTS.tax.bulkCategorize, data);
  },

  // Get tax summary for a date range or tax year
  async getTaxSummary(params: {
    start_date?: string;
    end_date?: string;
    tax_year?: number;
  }): Promise<TaxSummary> {
    return api.get<TaxSummary>(API_ENDPOINTS.tax.summary, params);
  },

  // Update an existing tax categorization
  async updateCategorization(
    categorizationId: string,
    data: Partial<CategorizeSingleRequest>
  ): Promise<TaxCategorization> {
    return api.patch<TaxCategorization>(
      API_ENDPOINTS.tax.categorization(categorizationId),
      data
    );
  },

  // Delete a tax categorization
  async deleteCategorization(categorizationId: string): Promise<void> {
    return api.delete(API_ENDPOINTS.tax.categorization(categorizationId));
  },

  // Create a new tax category (admin only)
  async createTaxCategory(data: {
    name: string;
    schedule_c_line: string;
    description: string;
    is_deductible: boolean;
    requires_receipt: boolean;
    has_business_use_percentage: boolean;
    is_meals_50_percent: boolean;
    is_vehicle_expense: boolean;
  }): Promise<TaxCategory> {
    return api.post<TaxCategory>(API_ENDPOINTS.tax.categories, data);
  },

  // Update an existing tax category
  async updateTaxCategory(
    categoryId: string,
    data: Partial<TaxCategory>
  ): Promise<TaxCategory> {
    return api.patch<TaxCategory>(
      `${API_ENDPOINTS.tax.categories}/${categoryId}`,
      data
    );
  },

  // Delete a tax category
  async deleteTaxCategory(categoryId: string): Promise<void> {
    return api.delete(`${API_ENDPOINTS.tax.categories}/${categoryId}`);
  },

  // Export Schedule C data
  async exportScheduleC(taxYear: number): Promise<ScheduleCExport> {
    return api.get<ScheduleCExport>(
      `${API_ENDPOINTS.tax.summary}/schedule-c/${taxYear}`
    );
  },

  // Download Schedule C as file
  async downloadScheduleC(
    taxYear: number,
    format: 'csv' | 'pdf' = 'csv'
  ): Promise<void> {
    const response = await api.get(
      `${API_ENDPOINTS.tax.summary}/schedule-c/${taxYear}?format=${format}`,
      { responseType: 'blob' }
    );

    // Create download link
    const blob = new Blob([response], {
      type: format === 'pdf' ? 'application/pdf' : 'text/csv'
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `schedule-c-${taxYear}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};

// Chart of Accounts API Service
export const chartOfAccountsApi = {
  // Get all chart of accounts
  async getChartOfAccounts(): Promise<ChartOfAccount[]> {
    return api.get<ChartOfAccount[]>(API_ENDPOINTS.chartOfAccounts.list);
  },

  // Get a specific account
  async getAccount(accountId: string): Promise<ChartOfAccount> {
    return api.get<ChartOfAccount>(API_ENDPOINTS.chartOfAccounts.get(accountId));
  },

  // Create a new account
  async createAccount(data: {
    name: string;
    account_type: 'asset' | 'liability' | 'equity' | 'income' | 'expense';
    parent_id?: string;
    balance?: number;
  }): Promise<ChartOfAccount> {
    return api.post<ChartOfAccount>(API_ENDPOINTS.chartOfAccounts.create, {
      ...data,
      balance: data.balance || 0,
      is_active: true,
    });
  },

  // Update an existing account
  async updateAccount(
    accountId: string,
    data: Partial<ChartOfAccount>
  ): Promise<ChartOfAccount> {
    return api.patch<ChartOfAccount>(
      API_ENDPOINTS.chartOfAccounts.update(accountId),
      data
    );
  },

  // Delete an account
  async deleteAccount(accountId: string): Promise<void> {
    return api.delete(API_ENDPOINTS.chartOfAccounts.delete(accountId));
  },

  // Toggle account active status
  async toggleAccountStatus(
    accountId: string,
    isActive: boolean
  ): Promise<ChartOfAccount> {
    return api.patch<ChartOfAccount>(
      API_ENDPOINTS.chartOfAccounts.update(accountId),
      { is_active: isActive }
    );
  },
};

// Export both APIs as a single object for convenience
export const taxApis = {
  tax: taxCategorizationApi,
  chartOfAccounts: chartOfAccountsApi,
};

export default taxCategorizationApi;