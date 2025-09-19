import { api } from '../api'

export interface Transaction {
  id: string
  account_id: string
  plaid_transaction_id?: string
  amount: number
  date: string
  description: string
  category?: string
  category_id?: string
  subcategory?: string
  merchant_name?: string
  account_owner?: string
  is_pending: boolean
  notes?: string
  created_at: string
  updated_at: string
}

export interface TransactionFilters {
  account_id?: string
  category?: string
  category_id?: string
  date_from?: string
  date_to?: string
  amount_min?: number
  amount_max?: number
  search?: string
  is_pending?: boolean
  is_reviewed?: boolean
  limit?: number
  offset?: number
}

export interface TransactionStats {
  total_income: number
  total_expenses: number
  net_income: number
  transaction_count: number
  avg_transaction_amount: number
}

export const transactionsApi = {
  // Get all transactions with optional filters
  getTransactions: async (filters?: TransactionFilters): Promise<{
    transactions: Transaction[]
    total: number
  }> => {
    const params = new URLSearchParams()

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString())
        }
      })
    }

    const response = await api.get<{
      items: Transaction[]
      total: number
      page: number
      per_page: number
      pages: number
    }>(`/api/v1/transactions?${params.toString()}`)

    // Transform the response to match expected format
    return {
      transactions: response.items || [],
      total: response.total || 0
    }
  },

  // Get a specific transaction by ID
  getTransaction: async (id: string): Promise<Transaction> => {
    return api.get(`/api/v1/transactions/${id}`)
  },

  // Update a transaction
  updateTransaction: async (id: string, updates: Partial<Transaction>): Promise<Transaction> => {
    return api.put(`/api/v1/transactions/${id}`, updates)
  },

  // Delete a transaction
  deleteTransaction: async (id: string): Promise<void> => {
    return api.delete(`/api/v1/transactions/${id}`)
  },

  // Bulk update transactions
  bulkUpdateTransactions: async (updates: {
    transaction_ids: string[]
    updates: Partial<Transaction>
  }): Promise<Transaction[]> => {
    return api.put('/api/v1/transactions/bulk', updates)
  },

  // Bulk delete transactions
  bulkDeleteTransactions: async (transactionIds: string[]): Promise<{
    deleted_count: number
    failed_ids: string[]
  }> => {
    return api.post('/api/v1/transactions/bulk-delete', {
      transaction_ids: transactionIds
    })
  },

  // Mark transactions as reviewed
  markAsReviewed: async (transactionIds: string[], reviewed: boolean = true): Promise<Transaction[]> => {
    return api.put('/api/v1/transactions/bulk', {
      transaction_ids: transactionIds,
      updates: { notes: reviewed ? 'reviewed' : undefined }
    })
  },

  // Get transaction statistics
  getTransactionStats: async (filters?: {
    date_from?: string
    date_to?: string
    account_id?: string
  }): Promise<TransactionStats> => {
    const params = new URLSearchParams()

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString())
        }
      })
    }

    return api.get(`/api/v1/transactions/stats?${params.toString()}`)
  },

  // Sync transactions from Plaid
  syncTransactions: async (accountId?: string): Promise<{
    synced_count: number
    new_transactions: number
    updated_transactions: number
  }> => {
    return api.post('/api/v1/plaid/sync-transactions', {
      account_ids: accountId ? [accountId] : undefined
    })
  },

  // Categorize transactions using ML
  categorizeTransactions: async (transactionIds: string[]): Promise<{
    categorized_count: number
    transactions: Transaction[]
  }> => {
    return api.post('/api/v1/transactions/categorize', {
      transaction_ids: transactionIds
    })
  },

  // Export transactions
  exportTransactions: async (filters?: TransactionFilters & { transaction_ids?: string[] }, format: 'csv' | 'xlsx' = 'csv'): Promise<void> => {
    const params = new URLSearchParams()
    params.append('format', format)

    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (key === 'transaction_ids' && Array.isArray(value)) {
            // Handle array of transaction IDs
            value.forEach(id => params.append('transaction_ids', id))
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }

    return api.download(`/api/v1/transactions/export?${params.toString()}`, `transactions.${format}`)
  },

  // Get transaction suggestions based on selected transactions
  getTransactionSuggestions: async (transactionIds: string[]): Promise<{
    similar_merchants: Array<{ merchant: string; count: number; transaction_ids: string[] }>
    similar_amounts: Array<{ amount: number; count: number; transaction_ids: string[] }>
    date_patterns: Array<{ pattern: string; count: number; transaction_ids: string[] }>
  }> => {
    return api.post('/api/v1/transactions/suggestions', {
      transaction_ids: transactionIds
    })
  }
}