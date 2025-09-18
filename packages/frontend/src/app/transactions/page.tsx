'use client'

import React, { useState, useMemo, useCallback } from 'react'
import { DashboardLayout } from '../../components/layout/dashboard-layout'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '../../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Badge } from '../../components/ui/badge'
import { Loading } from '../../components/ui/loading'
import { DataTable } from '../../components/transactions/data-table'
import { AdvancedFilters, type TransactionFilters } from '../../components/transactions/advanced-filters'
import { getTransactionColumns } from '../../components/transactions/transaction-columns'
import { CategorizationModal } from '../../components/transactions/categorization-modal'
import { CategoryManagement } from '../../components/transactions/category-management'
import { BulkActions } from '../../components/transactions/bulk-actions'
import { useSuccessToast, useErrorToast } from '../../components/ui/toast'
import {
  RefreshCw,
  Download,
  Upload,
  Plus,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  AlertCircle,
  FileText,
  Package,
  SettingsIcon
} from 'lucide-react'
import { format, startOfMonth, endOfMonth } from 'date-fns'
import { formatCurrency } from '../../lib/utils'
import {
  transactionsApi,
  type Transaction,
  type TransactionStats
} from '../../lib/api/transactions'
import { accountsApi, type Account } from '../../lib/api/accounts'
import { categoriesApi, type Category } from '../../lib/api/categories'

// Empty state component
function EmptyState({
  icon: Icon,
  title,
  description,
  actionText,
  onAction
}: {
  icon: any
  title: string
  description: string
  actionText?: string
  onAction?: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Icon className="h-12 w-12 text-gray-400 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 mb-4 max-w-sm">{description}</p>
      {actionText && onAction && (
        <Button onClick={onAction}>
          {actionText}
        </Button>
      )}
    </div>
  )
}

// Stats Card Component
function StatsCard({
  title,
  value,
  icon: Icon,
  trend,
  color = 'default',
  isLoading = false
}: {
  title: string
  value: string | number
  icon: any
  trend?: 'up' | 'down'
  color?: 'default' | 'success' | 'error' | 'warning'
  isLoading?: boolean
}) {
  const colorClasses = {
    default: 'text-neutral-600',
    success: 'text-success-600',
    error: 'text-error-600',
    warning: 'text-warning-600'
  }

  const iconColorClasses = {
    default: 'text-neutral-500',
    success: 'text-success-500',
    error: 'text-error-500',
    warning: 'text-warning-500'
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm font-medium text-neutral-600">{title}</p>
            {isLoading ? (
              <div className="h-8 w-24 bg-neutral-200 animate-pulse rounded" />
            ) : (
              <p className={`text-2xl font-bold ${colorClasses[color]}`}>
                {value}
              </p>
            )}
          </div>
          <div className={`p-3 rounded-full bg-neutral-50 ${iconColorClasses[color]}`}>
            <Icon className="h-6 w-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

const DEFAULT_FILTERS: TransactionFilters = {
  date_from: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
  date_to: format(endOfMonth(new Date()), 'yyyy-MM-dd')
}

export default function TransactionsPage() {
  const queryClient = useQueryClient()
  const successToast = useSuccessToast()
  const errorToast = useErrorToast()


  // State
  const [filters, setFilters] = useState<TransactionFilters>(DEFAULT_FILTERS)
  const [selectedTransactions, setSelectedTransactions] = useState<Transaction[]>([])
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [categorizationModalOpen, setCategorizationModalOpen] = useState(false)
  const [transactionsToCategrize, setTransactionsToCategrize] = useState<Transaction[]>([])
  const [categoryManagementOpen, setCategoryManagementOpen] = useState(false)
  const [showFloatingActions, setShowFloatingActions] = useState(false)

  // Queries
  const {
    data: transactionsData,
    isLoading: transactionsLoading,
    error: transactionsError
  } = useQuery({
    queryKey: ['transactions', filters],
    queryFn: () => transactionsApi.getTransactions(filters)
  })

  const {
    data: accounts = [],
    isLoading: accountsLoading
  } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.getAccounts
  })

  const {
    data: categories = [],
    isLoading: categoriesLoading
  } = useQuery({
    queryKey: ['categories'],
    queryFn: categoriesApi.getCategories
  })

  const {
    data: stats,
    isLoading: statsLoading
  } = useQuery({
    queryKey: ['transaction-stats', filters],
    queryFn: () => transactionsApi.getTransactionStats({
      date_from: filters.date_from,
      date_to: filters.date_to,
      account_id: filters.account_id
    })
  })

  // Mutations
  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<Transaction> }) =>
      transactionsApi.updateTransaction(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
      successToast('Transaction Updated', 'The transaction has been updated successfully')
    },
    onError: (error: any) => {
      errorToast('Update Failed', error.message || 'Failed to update transaction')
    }
  })

  const deleteMutation = useMutation({
    mutationFn: transactionsApi.deleteTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
      successToast('Transaction Deleted', 'The transaction has been deleted successfully')
    },
    onError: (error: any) => {
      errorToast('Delete Failed', error.message || 'Failed to delete transaction')
    }
  })

  const categorizeMutation = useMutation({
    mutationFn: (transactionIds: string[]) => transactionsApi.categorizeTransactions(transactionIds),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
      successToast(
        'Categorization Complete',
        `Successfully categorized ${result.categorized_count} transactions`
      )
    },
    onError: (error: any) => {
      errorToast('Categorization Failed', error.message || 'Failed to categorize transactions')
    }
  })

  // Handlers
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true)
    try {
      await transactionsApi.syncTransactions()
      await queryClient.invalidateQueries({ queryKey: ['transactions'] })
      await queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
      successToast('Sync Complete', 'Transactions have been synced successfully')
    } catch (error: any) {
      errorToast('Sync Failed', error.message || 'Failed to sync transactions')
    } finally {
      setIsRefreshing(false)
    }
  }, [queryClient, successToast, errorToast])

  const handleExport = useCallback(async (format: 'csv' | 'xlsx') => {
    try {
      await transactionsApi.exportTransactions(filters, format)
      successToast('Export Complete', `Transactions exported as ${format.toUpperCase()}`)
    } catch (error: any) {
      errorToast('Export Failed', error.message || 'Failed to export transactions')
    }
  }, [filters, successToast, errorToast])

  const handleTransactionEdit = useCallback((transaction: Transaction) => {
    // This would open an edit modal - to be implemented in Phase 3
    console.log('Edit transaction:', transaction)
  }, [])

  const handleTransactionDelete = useCallback((transaction: Transaction) => {
    if (confirm('Are you sure you want to delete this transaction?')) {
      deleteMutation.mutate(transaction.id)
    }
  }, [deleteMutation])

  const handleTransactionCategorize = useCallback((transaction: Transaction) => {
    setTransactionsToCategrize([transaction])
    setCategorizationModalOpen(true)
  }, [])

  const handleBulkCategorize = useCallback(() => {
    if (selectedTransactions.length === 0) {
      errorToast('No Selection', 'Please select transactions to categorize')
      return
    }
    setTransactionsToCategrize(selectedTransactions)
    setCategorizationModalOpen(true)
  }, [selectedTransactions, errorToast])

  const handleClearSelection = useCallback(() => {
    setSelectedTransactions([])
    setShowFloatingActions(false)
  }, [])

  const handleSelectionChange = useCallback((transactions: Transaction[]) => {
    setSelectedTransactions(transactions)
    setShowFloatingActions(transactions.length > 0)
  }, [])

  const handleFiltersReset = useCallback(() => {
    setFilters(DEFAULT_FILTERS)
  }, [])

  const handleCategorizationModalClose = useCallback(() => {
    setCategorizationModalOpen(false)
    setTransactionsToCategrize([])
    // Don't clear selection here - let user decide
  }, [])

  const handleTransactionsUpdated = useCallback((updatedTransactions: Transaction[]) => {
    queryClient.invalidateQueries({ queryKey: ['transactions'] })
    queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
  }, [queryClient])

  // Memoized values
  const transactions = useMemo(() => transactionsData?.transactions || [], [transactionsData])
  const totalTransactions = useMemo(() => transactionsData?.total || 0, [transactionsData])

  // Keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + A: Select all visible transactions
      if ((e.metaKey || e.ctrlKey) && e.key === 'a') {
        e.preventDefault()
        if (transactions && transactions.length > 0) {
          setSelectedTransactions(transactions)
          setShowFloatingActions(true)
          successToast('All Visible Transactions Selected', `Selected ${transactions.length} transactions`)
        }
      }

      // Escape: Clear selection
      if (e.key === 'Escape') {
        if (selectedTransactions.length > 0) {
          handleClearSelection()
          successToast('Selection Cleared', 'All transactions deselected')
        }
      }

      // Cmd/Ctrl + Shift + C: Open categorization modal
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'C') {
        e.preventDefault()
        if (selectedTransactions.length > 0) {
          handleBulkCategorize()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [transactions, selectedTransactions, handleClearSelection, handleBulkCategorize, successToast])

  const columns = useMemo(
    () => getTransactionColumns({
      accounts,
      categories,
      onEdit: handleTransactionEdit,
      onDelete: handleTransactionDelete,
      onCategorize: handleTransactionCategorize
    }),
    [accounts, categories, handleTransactionEdit, handleTransactionDelete, handleTransactionCategorize]
  )

  // Loading state
  const isLoading = transactionsLoading || accountsLoading || categoriesLoading

  // Check if we have any data
  const hasNoData = !isLoading && transactions.length === 0 && !transactionsError

  return (
    <DashboardLayout
      title="Transactions"
      description="View and manage all your financial transactions across all accounts"
    >
      <div className="space-y-6 relative">
        {/* Header Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">All Transactions</h1>
            <p className="text-sm text-neutral-600 mt-1">
              {totalTransactions.toLocaleString()} total transactions
              {filters.date_from && filters.date_to && (
                <span className="ml-1">
                  from {format(new Date(filters.date_from), 'MMM d')} to {format(new Date(filters.date_to), 'MMM d, yyyy')}
                </span>
              )}
              {selectedTransactions.length > 0 && (
                <span className="ml-2 text-primary-600 font-medium">
                  • {selectedTransactions.length} selected
                </span>
              )}
            </p>
            {selectedTransactions.length > 0 && (
              <div className="text-xs text-neutral-500 mt-1">
                Keyboard shortcuts: <kbd className="px-1 py-0.5 bg-neutral-100 rounded text-xs">Cmd+A</kbd> select all,
                <kbd className="px-1 py-0.5 bg-neutral-100 rounded text-xs">Esc</kbd> clear,
                <kbd className="px-1 py-0.5 bg-neutral-100 rounded text-xs">Cmd+Shift+C</kbd> categorize
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('csv')}
              disabled={transactions.length === 0}
            >
              <Download className="h-4 w-4 mr-1" />
              Export
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCategoryManagementOpen(true)}
            >
              <SettingsIcon className="h-4 w-4 mr-1" />
              Manage Categories
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              {isRefreshing ? (
                <Loading size="sm" className="mr-1" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-1" />
              )}
              Sync
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-1" />
              Add Transaction
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard
              title="Total Income"
              value={formatCurrency(stats.total_income)}
              icon={TrendingUp}
              color="success"
              isLoading={statsLoading}
            />
            <StatsCard
              title="Total Expenses"
              value={formatCurrency(Math.abs(stats.total_expenses))}
              icon={TrendingDown}
              color="error"
              isLoading={statsLoading}
            />
            <StatsCard
              title="Net Income"
              value={formatCurrency(stats.net_income)}
              icon={DollarSign}
              color={stats.net_income >= 0 ? 'success' : 'error'}
              isLoading={statsLoading}
            />
            <StatsCard
              title="Avg Transaction"
              value={formatCurrency(stats.avg_transaction_amount)}
              icon={Activity}
              isLoading={statsLoading}
            />
          </div>
        )}

        {/* Filters */}
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-lg">Filters</CardTitle>
            <CardDescription>
              Filter and search through your transactions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <AdvancedFilters
              filters={filters}
              onFiltersChange={setFilters}
              accounts={accounts}
              categories={categories}
              onReset={handleFiltersReset}
            />
          </CardContent>
        </Card>

        {/* Enhanced Bulk Actions - Sticky when scrolling */}
        {selectedTransactions.length > 0 && (
          <div className="sticky top-4 z-10">
            <BulkActions
              selectedTransactions={selectedTransactions}
              onClearSelection={handleClearSelection}
              onCategorize={handleBulkCategorize}
              onTransactionsUpdated={handleTransactionsUpdated}
            />
          </div>
        )}

        {/* Floating Action Button for Mobile */}
        {showFloatingActions && selectedTransactions.length > 0 && (
          <div className="fixed bottom-6 right-6 z-20 md:hidden">
            <Button
              onClick={handleBulkCategorize}
              className="h-14 w-14 rounded-full shadow-lg"
              size="sm"
            >
              <Tag className="h-6 w-6" />
            </Button>
          </div>
        )}

        {/* Transactions Table */}
        {transactionsError ? (
          <Card>
            <CardContent className="py-12">
              <EmptyState
                icon={AlertCircle}
                title="Error Loading Transactions"
                description={transactionsError.message || 'Failed to load transactions'}
                actionText="Try Again"
                onAction={handleRefresh}
              />
            </CardContent>
          </Card>
        ) : hasNoData ? (
          <Card>
            <CardContent className="py-12">
              <EmptyState
                icon={filters.date_from || filters.account_id ? FileText : Package}
                title={filters.date_from || filters.account_id ? "No Transactions Found" : "No Transactions Yet"}
                description={
                  filters.date_from || filters.account_id
                    ? "No transactions match your current filters. Try adjusting your search criteria."
                    : "You don't have any transactions yet. Connect your accounts to start tracking."
                }
                actionText={filters.date_from || filters.account_id ? "Clear Filters" : "Connect Account"}
                onAction={() => filters.date_from || filters.account_id ? handleFiltersReset() : window.location.href = '/accounts'}
              />
            </CardContent>
          </Card>
        ) : (
          <Card className="overflow-hidden">
            <DataTable
              columns={columns}
              data={transactions}
              onRowSelectionChange={handleSelectionChange}
              onRowClick={(transaction) => handleTransactionCategorize(transaction)}
              searchKey="description"
              searchPlaceholder="Search by description or merchant..."
              showColumnToggle={true}
              showPagination={true}
              pageSize={50}
              isLoading={isLoading || isRefreshing}
              emptyMessage="No transactions found matching your filters."
              className="border-0"
            />
          </Card>
        )}
      </div>

      {/* Categorization Modal */}
      <CategorizationModal
        isOpen={categorizationModalOpen}
        onClose={handleCategorizationModalClose}
        transactions={transactionsToCategrize}
        onTransactionsUpdated={handleTransactionsUpdated}
      />

      {/* Category Management Modal */}
      <CategoryManagement
        isOpen={categoryManagementOpen}
        onClose={() => setCategoryManagementOpen(false)}
      />
    </DashboardLayout>
  )
}