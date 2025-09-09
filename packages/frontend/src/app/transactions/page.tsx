'use client'

import React from 'react'
import {
  RefreshCwIcon,
  PlusIcon,
  SettingsIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  DollarSignIcon,
  CalendarIcon
} from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loading } from '@/components/ui/loading'
import { TransactionsTable } from '@/components/transactions/transactions-table'
import { TransactionFilters } from '@/components/transactions/transaction-filters'
import { TransactionDetailModal } from '@/components/transactions/transaction-detail-modal'
import { BulkActions } from '@/components/transactions/bulk-actions'
import { ImportExport } from '@/components/transactions/import-export'
import {
  Transaction,
  Account,
  Category,
  TransactionFilters as ITransactionFilters,
  transactionsApi,
  accountsApi,
  categoriesApi
} from '@/lib/api'
import { ProtectedRoute } from '@/components/auth/protected-route'
import { cn } from '@/lib/utils'
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns'

const DEFAULT_FILTERS: ITransactionFilters = {
  limit: 25,
  offset: 0,
  date_from: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
  date_to: format(endOfMonth(new Date()), 'yyyy-MM-dd')
}

export default function TransactionsPage() {
  const queryClient = useQueryClient()
  
  // State
  const [filters, setFilters] = React.useState<ITransactionFilters>(DEFAULT_FILTERS)
  const [selectedTransaction, setSelectedTransaction] = React.useState<Transaction | null>(null)
  const [selectedTransactions, setSelectedTransactions] = React.useState<Transaction[]>([])
  const [showDetailModal, setShowDetailModal] = React.useState(false)
  const [isRefreshing, setIsRefreshing] = React.useState(false)

  // Queries
  const {
    data: transactionsData,
    isLoading: transactionsLoading,
    error: transactionsError
  } = useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => transactionsApi.getTransactions(filters),
    staleTime: 30000 // 30 seconds
  })

  const {
    data: accounts = [],
    isLoading: accountsLoading
  } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountsApi.getAccounts()
  })

  const {
    data: categories = [],
    isLoading: categoriesLoading
  } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getCategories()
  })

  const {
    data: transactionStats,
    isLoading: statsLoading
  } = useQuery({
    queryKey: ['transaction-stats', filters],
    queryFn: () => transactionsApi.getTransactionStats({
      date_from: filters.date_from,
      date_to: filters.date_to,
      account_id: filters.account_id
    })
  })

  const transactions = transactionsData?.transactions || []
  const totalTransactions = transactionsData?.total || 0

  // Handlers
  const handleTransactionSelect = (transaction: Transaction) => {
    setSelectedTransaction(transaction)
    setShowDetailModal(true)
  }

  const handleTransactionUpdate = (updatedTransaction: Transaction) => {
    queryClient.setQueryData(['transactions', filters], (old: any) => {
      if (!old) return old
      return {
        ...old,
        transactions: old.transactions.map((t: Transaction) =>
          t.id === updatedTransaction.id ? updatedTransaction : t
        )
      }
    })
    
    // Also update stats
    queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
  }

  const handleTransactionDelete = (transactionId: string) => {
    queryClient.setQueryData(['transactions', filters], (old: any) => {
      if (!old) return old
      return {
        ...old,
        transactions: old.transactions.filter((t: Transaction) => t.id !== transactionId),
        total: old.total - 1
      }
    })
    
    // Clear selection if deleted transaction was selected
    if (selectedTransaction?.id === transactionId) {
      setSelectedTransaction(null)
      setShowDetailModal(false)
    }
    
    // Remove from bulk selection
    setSelectedTransactions(prev => prev.filter(t => t.id !== transactionId))
    
    // Update stats
    queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
  }

  const handleBulkUpdate = (updatedTransactions: Transaction[]) => {
    queryClient.setQueryData(['transactions', filters], (old: any) => {
      if (!old) return old
      
      const updatedMap = new Map(updatedTransactions.map(t => [t.id, t]))
      
      return {
        ...old,
        transactions: old.transactions.map((t: Transaction) => 
          updatedMap.has(t.id) ? updatedMap.get(t.id) : t
        )
      }
    })
    
    // Update stats
    queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
  }

  const handleBulkDelete = (transactionIds: string[]) => {
    queryClient.setQueryData(['transactions', filters], (old: any) => {
      if (!old) return old
      return {
        ...old,
        transactions: old.transactions.filter((t: Transaction) => 
          !transactionIds.includes(t.id)
        ),
        total: old.total - transactionIds.length
      }
    })
    
    // Clear selections
    setSelectedTransactions([])
    
    // Update stats
    queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    try {
      // Sync transactions from all accounts
      await transactionsApi.syncTransactions()
      
      // Refresh all queries
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['transactions'] }),
        queryClient.invalidateQueries({ queryKey: ['transaction-stats'] }),
        queryClient.invalidateQueries({ queryKey: ['accounts'] })
      ])
    } catch (error) {
      console.error('Failed to refresh transactions:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleFiltersReset = () => {
    setFilters(DEFAULT_FILTERS)
  }

  const handleImported = () => {
    queryClient.invalidateQueries({ queryKey: ['transactions'] })
    queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
  }

  // Calculated values
  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const loading = transactionsLoading || accountsLoading || categoriesLoading

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="container mx-auto px-4 py-8">
          <Loading />
        </div>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-neutral-900">Transactions</h1>
            <p className="text-neutral-600 mt-1">
              Manage and categorize your financial transactions
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <ImportExport
              filters={filters}
              selectedTransactionIds={selectedTransactions.map(t => t.id)}
              onTransactionsImported={handleImported}
            />
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              loading={isRefreshing}
            >
              <RefreshCwIcon className="h-4 w-4 mr-1" />
              Sync
            </Button>
            
            <Button size="sm">
              <PlusIcon className="h-4 w-4 mr-1" />
              Add Transaction
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        {transactionStats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-600">Total Income</p>
                  <p className="text-2xl font-bold text-success-600">
                    {formatAmount(transactionStats.total_income)}
                  </p>
                </div>
                <TrendingUpIcon className="h-8 w-8 text-success-500" />
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-600">Total Expenses</p>
                  <p className="text-2xl font-bold text-error-600">
                    {formatAmount(Math.abs(transactionStats.total_expenses))}
                  </p>
                </div>
                <TrendingDownIcon className="h-8 w-8 text-error-500" />
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-600">Net Income</p>
                  <p className={cn(
                    "text-2xl font-bold",
                    transactionStats.net_income >= 0 ? "text-success-600" : "text-error-600"
                  )}>
                    {formatAmount(transactionStats.net_income)}
                  </p>
                </div>
                <DollarSignIcon className="h-8 w-8 text-primary-500" />
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-600">Transactions</p>
                  <p className="text-2xl font-bold text-neutral-900">
                    {transactionStats.transaction_count.toLocaleString()}
                  </p>
                  <p className="text-xs text-neutral-500">
                    Avg: {formatAmount(transactionStats.avg_transaction_amount)}
                  </p>
                </div>
                <CalendarIcon className="h-8 w-8 text-neutral-500" />
              </div>
            </Card>
          </div>
        )}

        {/* Filters */}
        <Card className="p-4">
          <TransactionFilters
            filters={filters}
            onFiltersChange={setFilters}
            accounts={accounts}
            categories={categories}
            onReset={handleFiltersReset}
          />
        </Card>

        {/* Bulk Actions */}
        {selectedTransactions.length > 0 && (
          <BulkActions
            selectedTransactions={selectedTransactions}
            onTransactionsUpdated={handleBulkUpdate}
            onTransactionsDeleted={handleBulkDelete}
            onSelectionClear={() => setSelectedTransactions([])}
          />
        )}

        {/* Transactions Table */}
        <Card className="overflow-hidden">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-neutral-900">Transactions</h2>
                <Badge variant="outline">
                  {totalTransactions.toLocaleString()} total
                </Badge>
              </div>
              
              <Button variant="ghost" size="sm">
                <SettingsIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          <TransactionsTable
            transactions={transactions}
            accounts={accounts}
            categories={categories}
            isLoading={transactionsLoading || isRefreshing}
            onTransactionSelect={handleTransactionSelect}
            onTransactionUpdate={handleTransactionUpdate}
            onTransactionDelete={handleTransactionDelete}
            onRowSelectionChange={setSelectedTransactions}
          />
        </Card>

        {/* Transaction Detail Modal */}
        <TransactionDetailModal
          transaction={selectedTransaction}
          isOpen={showDetailModal}
          onClose={() => {
            setShowDetailModal(false)
            setSelectedTransaction(null)
          }}
          onTransactionUpdated={handleTransactionUpdate}
          onTransactionDeleted={handleTransactionDelete}
          accounts={accounts}
        />

        {/* Error Display */}
        {transactionsError && (
          <Card className="p-4 bg-error-50 border-error-200">
            <p className="text-error-700">
              Failed to load transactions. Please try refreshing the page.
            </p>
          </Card>
        )}
      </div>
    </ProtectedRoute>
  )
}