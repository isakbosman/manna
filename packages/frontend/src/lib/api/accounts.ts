import { api } from '../api'
import axios from 'axios'

export interface Account {
  id: string
  user_id: string
  plaid_account_id?: string
  name: string
  type: 'checking' | 'savings' | 'credit' | 'investment' | 'loan' | 'other'
  subtype?: string
  mask?: string
  balance_current: number
  balance_available?: number
  balance_limit?: number
  currency_code: string
  institution_name?: string
  institution_id?: string
  is_active: boolean
  last_synced_at?: string
  created_at: string
  updated_at: string
}

export interface PlaidLinkResult {
  public_token: string
  metadata: {
    institution: {
      name: string
      institution_id: string
    }
    accounts: Array<{
      id: string
      name: string
      type: string
      subtype: string
      mask: string
    }>
  }
}

export interface Institution {
  institution_id: string
  name: string
  country_codes: string[]
  products: string[]
  logo?: string
  primary_color?: string
  url?: string
}

export const accountsApi = {
  // Get all user accounts
  getAccounts: async (): Promise<Account[]> => {
    const response = await api.get('/api/v1/accounts')
    // Handle paginated response
    if (response && typeof response === 'object' && 'accounts' in response) {
      return response.accounts
    }
    // Fallback for direct array response
    return Array.isArray(response) ? response : []
  },

  // Get a specific account by ID
  getAccount: async (id: string): Promise<Account> => {
    return api.get(`/api/v1/accounts/${id}`)
  },

  // Create a new account (manual)
  createAccount: async (account: {
    name: string
    type: Account['type']
    subtype?: string
    balance_current: number
    currency_code?: string
  }): Promise<Account> => {
    return api.post('/api/v1/accounts', account)
  },

  // Update an account
  updateAccount: async (id: string, updates: Partial<Account>): Promise<Account> => {
    return api.put(`/api/v1/accounts/${id}`, updates)
  },

  // Delete an account
  deleteAccount: async (id: string): Promise<void> => {
    return api.delete(`/api/v1/accounts/${id}`)
  },

  // Get Plaid link token for connecting new accounts
  getPlaidLinkToken: async (): Promise<{
    link_token: string
    expiration: string
  }> => {
    return api.post('/api/v1/plaid/create-link-token')
  },

  // Exchange Plaid public token for access token and fetch accounts
  exchangePublicToken: async (publicToken: string, metadata: any): Promise<{
    accounts: Account[]
    institution_name: string
  }> => {
    return api.post('/api/v1/plaid/exchange-public-token', {
      public_token: publicToken,
      metadata
    })
  },

  // Sync transactions for accounts
  syncTransactions: async (accountIds?: string[]): Promise<{
    synced_count: number
    new_transactions: number
  }> => {
    return api.post('/api/v1/plaid/sync-transactions', {
      account_ids: accountIds
    })
  },

  // Fetch historical transactions for accounts
  fetchHistoricalTransactions: async (
    accountIds?: string[],
    startDate?: string,
    endDate?: string
  ): Promise<{
    success: boolean
    total_fetched: number
    new_transactions: number
    duplicates_skipped: number
    message: string
    date_range: string
    accounts_processed: number
    errors?: string[]
  }> => {
    // Create a custom axios instance with longer timeout for historical fetches
    // Historical fetches can take several minutes for accounts with many transactions
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const historicalClient = axios.create({
      baseURL: API_BASE_URL,
      timeout: 300000, // 5 minutes timeout for historical fetches
      headers: {
        'Content-Type': 'application/json',
      }
    })

    const response = await historicalClient.post('/api/v1/plaid/fetch-historical-transactions', {
      account_ids: accountIds,
      start_date: startDate,
      end_date: endDate
    })

    return response.data
  },

  // Get institution details
  getInstitution: async (institutionId: string): Promise<Institution> => {
    return api.get(`/api/v1/plaid/institutions/${institutionId}`)
  },

  // Get account transaction summary
  getAccountSummary: async (accountId: string, options?: {
    date_from?: string
    date_to?: string
  }): Promise<{
    account: Account
    transaction_count: number
    total_income: number
    total_expenses: number
    net_change: number
    balance_history: Array<{
      date: string
      balance: number
    }>
  }> => {
    const params = new URLSearchParams()
    
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString())
        }
      })
    }
    
    return api.get(`/api/v1/accounts/${accountId}/summary?${params.toString()}`)
  }
}