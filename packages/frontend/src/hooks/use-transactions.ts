import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { transactionsApi, type Transaction, type TransactionFilters } from '@/lib/api/transactions'
import { toast } from '@/hooks/use-toast'

// Query keys for consistent cache management
export const transactionKeys = {
  all: ['transactions'] as const,
  lists: () => [...transactionKeys.all, 'list'] as const,
  list: (filters?: TransactionFilters) => [...transactionKeys.lists(), filters] as const,
  details: () => [...transactionKeys.all, 'detail'] as const,
  detail: (id: string) => [...transactionKeys.details(), id] as const,
  stats: (filters?: any) => [...transactionKeys.all, 'stats', filters] as const,
}

// Hook for fetching transactions with filters
export function useTransactions(filters?: TransactionFilters) {
  return useQuery({
    queryKey: transactionKeys.list(filters),
    queryFn: () => transactionsApi.getTransactions(filters),
    staleTime: 1000 * 60 * 2, // 2 minutes
  })
}

// Hook for fetching a single transaction
export function useTransaction(id: string) {
  return useQuery({
    queryKey: transactionKeys.detail(id),
    queryFn: () => transactionsApi.getTransaction(id),
    enabled: !!id,
  })
}

// Hook for fetching transaction statistics
export function useTransactionStats(filters?: {
  date_from?: string
  date_to?: string
  account_id?: string
}) {
  return useQuery({
    queryKey: transactionKeys.stats(filters),
    queryFn: () => transactionsApi.getTransactionStats(filters),
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Hook for updating a transaction
export function useUpdateTransaction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<Transaction> }) =>
      transactionsApi.updateTransaction(id, updates),
    onSuccess: (updatedTransaction) => {
      // Update the specific transaction in cache
      queryClient.setQueryData(
        transactionKeys.detail(updatedTransaction.id),
        updatedTransaction
      )

      // Invalidate transaction lists to refetch
      queryClient.invalidateQueries({
        queryKey: transactionKeys.lists(),
      })

      // Invalidate stats
      queryClient.invalidateQueries({
        queryKey: transactionKeys.stats(),
      })

      toast({
        title: 'Transaction updated',
        description: 'The transaction has been successfully updated.',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Update failed',
        description: error.message || 'Failed to update transaction.',
        variant: 'destructive',
      })
    },
  })
}

// Hook for bulk updating transactions
export function useBulkUpdateTransactions() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: transactionsApi.bulkUpdateTransactions,
    onSuccess: (updatedTransactions) => {
      // Invalidate all transaction-related queries
      queryClient.invalidateQueries({
        queryKey: transactionKeys.all,
      })

      toast({
        title: 'Transactions updated',
        description: `${updatedTransactions.length} transactions have been updated.`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Bulk update failed',
        description: error.message || 'Failed to update transactions.',
        variant: 'destructive',
      })
    },
  })
}

// Hook for syncing transactions from Plaid
export function useSyncTransactions() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: transactionsApi.syncTransactions,
    onSuccess: (result) => {
      // Invalidate all transaction queries to show fresh data
      queryClient.invalidateQueries({
        queryKey: transactionKeys.all,
      })

      toast({
        title: 'Sync completed',
        description: `Synced ${result.synced_count} transactions. ${result.new_transactions} new, ${result.updated_transactions} updated.`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Sync failed',
        description: error.message || 'Failed to sync transactions.',
        variant: 'destructive',
      })
    },
  })
}

// Hook for categorizing transactions
export function useCategorizeTransactions() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: transactionsApi.categorizeTransactions,
    onSuccess: (result) => {
      // Invalidate transaction queries
      queryClient.invalidateQueries({
        queryKey: transactionKeys.all,
      })

      toast({
        title: 'Categorization completed',
        description: `Categorized ${result.categorized_count} transactions.`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Categorization failed',
        description: error.message || 'Failed to categorize transactions.',
        variant: 'destructive',
      })
    },
  })
}

// Hook for deleting a transaction
export function useDeleteTransaction() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: transactionsApi.deleteTransaction,
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({
        queryKey: transactionKeys.detail(deletedId),
      })

      // Invalidate lists
      queryClient.invalidateQueries({
        queryKey: transactionKeys.lists(),
      })

      toast({
        title: 'Transaction deleted',
        description: 'The transaction has been successfully deleted.',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Delete failed',
        description: error.message || 'Failed to delete transaction.',
        variant: 'destructive',
      })
    },
  })
}