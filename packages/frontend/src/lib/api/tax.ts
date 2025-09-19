import { api, API_ENDPOINTS } from '../api-client'

// Tax category types based on Schedule C lines
export interface TaxCategory {
  id: string
  name: string
  schedule_c_line: string
  description: string
  is_deductible: boolean
  requires_receipt: boolean
  has_business_use_percentage: boolean
  is_meals_50_percent: boolean
  is_vehicle_expense: boolean
  created_at: string
  updated_at: string
}

export interface ChartOfAccount {
  id: string
  name: string
  account_type: 'asset' | 'liability' | 'equity' | 'income' | 'expense'
  parent_id?: string
  balance: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TaxCategorization {
  id: string
  transaction_id: string
  tax_category_id: string
  business_use_percentage: number
  business_purpose?: string
  receipt_url?: string
  mileage?: number
  created_at: string
  updated_at: string
}

export interface TaxSummary {
  tax_year: number
  total_deductions: number
  categories: Array<{
    tax_category_id: string
    category_name: string
    schedule_c_line: string
    total_amount: number
    transaction_count: number
    documentation_status: 'complete' | 'partial' | 'missing'
  }>
  documentation_status: {
    total_transactions: number
    with_receipts: number
    missing_receipts: number
    complete_business_purpose: number
    missing_business_purpose: number
  }
}

export interface CategorizeSingleRequest {
  tax_category_id: string
  business_use_percentage: number
  business_purpose?: string
  receipt_url?: string
  mileage?: number
}

export interface CategorizeBulkRequest {
  transaction_ids: string[]
  tax_category_id: string
  business_use_percentage: number
  business_purpose?: string
  receipt_url?: string
  mileage?: number
}

export interface ScheduleCExport {
  tax_year: number
  lines: Array<{
    line_number: string
    description: string
    amount: number
  }>
  total_deductions: number
  generated_at: string
}

// Tax API functions
export const taxApi = {
  // Categorize single transaction
  categorizeSingle: async (
    transactionId: string,
    data: CategorizeSingleRequest
  ): Promise<TaxCategorization> => {
    return api.post(API_ENDPOINTS.tax.categorize, {
      transaction_id: transactionId,
      ...data,
    })
  },

  // Bulk categorize transactions
  categorizeBulk: async (data: CategorizeBulkRequest): Promise<TaxCategorization[]> => {
    return api.post(API_ENDPOINTS.tax.bulkCategorize, data)
  },

  // Get tax summary for a year or date range
  getTaxSummary: async (params: {
    tax_year?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<TaxSummary> => {
    return api.get(API_ENDPOINTS.tax.summary, params)
  },

  // Get available tax categories
  getTaxCategories: async (): Promise<TaxCategory[]> => {
    return api.get(API_ENDPOINTS.tax.categories)
  },

  // Get chart of accounts
  getChartOfAccounts: async (): Promise<ChartOfAccount[]> => {
    return api.get(API_ENDPOINTS.chartOfAccounts.list)
  },

  // Export Schedule C data
  exportScheduleC: async (taxYear: number): Promise<ScheduleCExport> => {
    return api.get(`${API_ENDPOINTS.tax.summary}/schedule-c/${taxYear}`)
  },

  // Download Schedule C as CSV
  downloadScheduleC: async (taxYear: number, format: 'csv' | 'pdf' = 'csv'): Promise<void> => {
    return api.download(
      `${API_ENDPOINTS.tax.summary}/schedule-c/${taxYear}?format=${format}`,
      `schedule-c-${taxYear}.${format}`
    )
  },

  // Update tax categorization
  updateCategorization: async (
    categorizationId: string,
    data: Partial<CategorizeSingleRequest>
  ): Promise<TaxCategorization> => {
    return api.patch(API_ENDPOINTS.tax.categorization(categorizationId), data)
  },

  // Delete tax categorization
  deleteCategorization: async (categorizationId: string): Promise<void> => {
    return api.delete(API_ENDPOINTS.tax.categorization(categorizationId))
  },

  // Create new tax category (for admin users)
  createTaxCategory: async (data: {
    name: string
    schedule_c_line: string
    description: string
    is_deductible: boolean
    requires_receipt: boolean
    has_business_use_percentage: boolean
    is_meals_50_percent: boolean
    is_vehicle_expense: boolean
  }): Promise<TaxCategory> => {
    return api.post(API_ENDPOINTS.tax.categories, data)
  },

  // Update tax category
  updateTaxCategory: async (
    categoryId: string,
    data: Partial<TaxCategory>
  ): Promise<TaxCategory> => {
    return api.patch(`${API_ENDPOINTS.tax.categories}/${categoryId}`, data)
  },

  // Chart of Accounts operations
  createChartOfAccount: async (data: {
    name: string
    account_type: 'asset' | 'liability' | 'equity' | 'income' | 'expense'
    parent_id?: string
    balance?: number
  }): Promise<ChartOfAccount> => {
    return api.post(API_ENDPOINTS.chartOfAccounts.create, {
      ...data,
      balance: data.balance || 0,
      is_active: true,
    })
  },

  updateChartOfAccount: async (
    accountId: string,
    data: Partial<ChartOfAccount>
  ): Promise<ChartOfAccount> => {
    return api.patch(API_ENDPOINTS.chartOfAccounts.update(accountId), data)
  },

  deleteChartOfAccount: async (accountId: string): Promise<void> => {
    return api.delete(API_ENDPOINTS.chartOfAccounts.delete(accountId))
  },
}