'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { accountsApi, Account } from '../lib/api/accounts'
import { useState, useCallback } from 'react'

export interface UseAccountsReturn {
  // Data
  accounts: Account[]
  totalBalance: number
  activeAccounts: Account[]
  institutionCount: number
  
  // Loading states
  isLoading: boolean
  isSyncing: boolean
  error: Error | null
  
  // Actions
  refetch: () => void
  syncAll: () => Promise<void>
  syncAccount: (accountId: string) => Promise<void>
  removeAccount: (accountId: string) => Promise<void>
  linkPlaidAccount: (publicToken: string, metadata: any) => Promise<void>
  
  // Utility functions
  getAccountsByType: (type: Account['type']) => Account[]
  getAccountBalance: (accountId: string) => number
  formatAccountName: (account: Account) => string
}

export function useAccounts(): UseAccountsReturn {
  const queryClient = useQueryClient()
  const [syncingAccounts, setSyncingAccounts] = useState<Set<string>>(new Set())

  // Main accounts query
  const {
    data: accounts = [],
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.getAccounts,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  // Sync all accounts mutation
  const syncAllMutation = useMutation({
    mutationFn: () => accountsApi.syncTransactions(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    },
    onError: (error) => {
      console.error('Sync all accounts failed:', error)
    }
  })

  // Sync single account mutation
  const syncAccountMutation = useMutation({
    mutationFn: (accountId: string) => accountsApi.syncTransactions([accountId]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    },
    onError: (error) => {
      console.error('Sync account failed:', error)
    }
  })

  // Remove account mutation
  const removeAccountMutation = useMutation({
    mutationFn: accountsApi.deleteAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    },
    onError: (error) => {
      console.error('Remove account failed:', error)
    }
  })

  // Link Plaid account mutation
  const linkPlaidMutation = useMutation({
    mutationFn: ({ publicToken, metadata }: { publicToken: string, metadata: any }) =>
      accountsApi.exchangePublicToken(publicToken, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['institutions'] })
    },
    onError: (error) => {
      console.error('Link Plaid account failed:', error)
    }
  })

  // Computed values
  const activeAccounts = accounts.filter(account => account.is_active)
  
  const totalBalance = accounts.reduce((sum, account) => {
    if (account.type === 'credit') {
      // Credit accounts show negative balances as positive debt
      return sum - Math.abs(account.balance_current)
    }
    return sum + account.balance_current
  }, 0)

  const institutionIds = [...new Set(
    accounts
      .filter(account => account.institution_id)
      .map(account => account.institution_id!)
  )]
  
  const institutionCount = institutionIds.length

  // Action handlers
  const syncAll = useCallback(async () => {
    try {
      await syncAllMutation.mutateAsync()
    } catch (error) {
      throw error
    }
  }, [syncAllMutation])

  const syncAccount = useCallback(async (accountId: string) => {
    setSyncingAccounts(prev => new Set(prev).add(accountId))
    
    try {
      await syncAccountMutation.mutateAsync(accountId)
    } catch (error) {
      throw error
    } finally {
      setSyncingAccounts(prev => {
        const next = new Set(prev)
        next.delete(accountId)
        return next
      })
    }
  }, [syncAccountMutation])

  const removeAccount = useCallback(async (accountId: string) => {
    try {
      await removeAccountMutation.mutateAsync(accountId)
    } catch (error) {
      throw error
    }
  }, [removeAccountMutation])

  const linkPlaidAccount = useCallback(async (publicToken: string, metadata: any) => {
    try {
      await linkPlaidMutation.mutateAsync({ publicToken, metadata })
    } catch (error) {
      throw error
    }
  }, [linkPlaidMutation])

  // Utility functions
  const getAccountsByType = useCallback((type: Account['type']) => {
    return accounts.filter(account => account.type === type)
  }, [accounts])

  const getAccountBalance = useCallback((accountId: string) => {
    const account = accounts.find(acc => acc.id === accountId)
    return account?.balance_current || 0
  }, [accounts])

  const formatAccountName = useCallback((account: Account) => {
    if (account.mask) {
      return `${account.name} ••••${account.mask}`
    }
    return account.name
  }, [])

  return {
    // Data
    accounts,
    totalBalance,
    activeAccounts,
    institutionCount,
    
    // Loading states
    isLoading,
    isSyncing: syncAllMutation.isPending || syncAccountMutation.isPending || syncingAccounts.size > 0,
    error: error as Error | null,
    
    // Actions
    refetch,
    syncAll,
    syncAccount,
    removeAccount,
    linkPlaidAccount,
    
    // Utility functions
    getAccountsByType,
    getAccountBalance,
    formatAccountName
  }
}

export default useAccounts