/**
 * Example integration of tax categorization features into existing transaction management
 *
 * This file demonstrates how to integrate the tax categorization components
 * with the existing transaction table and management system.
 */

import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calculator, Receipt, FileText } from 'lucide-react'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { transactionsApi, categoriesApi, accountsApi } from '../../lib/api'
import { TaxCategorizationModal, BulkTaxCategorization } from './index'
import { TransactionsTable } from '../transactions/transactions-table'

// Example of how to add tax features to existing transactions page
export function TaxIntegratedTransactionsPage() {
  // State for tax modals
  const [isTaxModalOpen, setIsTaxModalOpen] = React.useState(false)
  const [isBulkTaxModalOpen, setIsBulkTaxModalOpen] = React.useState(false)
  const [selectedTransaction, setSelectedTransaction] = React.useState(null)
  const [selectedTransactions, setSelectedTransactions] = React.useState([])

  // Existing data loading
  const { data: transactions = [], isLoading } = useQuery({
    queryKey: ['transactions'],
    queryFn: transactionsApi.getTransactions,
  })

  const { data: accounts = [] } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.getAccounts,
  })

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: categoriesApi.getCategories,
  })

  // Handlers for tax categorization
  const handleTaxCategorize = (transaction) => {
    setSelectedTransaction(transaction)
    setIsTaxModalOpen(true)
  }

  const handleBulkTaxCategorize = () => {
    if (selectedTransactions.length > 0) {
      setIsBulkTaxModalOpen(true)
    }
  }

  const handleTransactionUpdate = (updatedTransaction) => {
    // Update the transaction in your state/query cache
    console.log('Transaction updated with tax categorization:', updatedTransaction)
  }

  const handleBulkTransactionsUpdate = (updatedTransactions) => {
    // Update multiple transactions in your state/query cache
    console.log('Bulk transactions updated:', updatedTransactions)
    setSelectedTransactions([])
  }

  // Calculate tax stats
  const taxStats = React.useMemo(() => {
    const categorized = transactions.filter(t => t.tax_categorization)
    const totalDeductions = categorized.reduce((sum, t) => {
      if (t.amount < 0 && t.tax_categorization) {
        const deduction = Math.abs(t.amount) * (t.tax_categorization.business_use_percentage / 100)
        return sum + deduction
      }
      return sum
    }, 0)

    return {
      totalTransactions: transactions.length,
      categorizedCount: categorized.length,
      categorizationPercentage: transactions.length > 0 ? Math.round((categorized.length / transactions.length) * 100) : 0,
      totalDeductions,
    }
  }, [transactions])

  return (
    <div className="space-y-6">
      {/* Enhanced header with tax stats */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Transactions</h1>
          <div className="flex items-center gap-4 mt-2">
            <Badge variant="outline" className="flex items-center gap-1">
              <FileText className="h-3 w-3" />
              {taxStats.categorizedCount} / {taxStats.totalTransactions} Categorized
            </Badge>
            <Badge variant="outline" className="flex items-center gap-1">
              <Calculator className="h-3 w-3" />
              {taxStats.categorizationPercentage}% Complete
            </Badge>
            {taxStats.totalDeductions > 0 && (
              <Badge variant="outline" className="flex items-center gap-1 text-green-600">
                <Receipt className="h-3 w-3" />
                ${taxStats.totalDeductions.toLocaleString()} Deductions
              </Badge>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Bulk actions */}
          {selectedTransactions.length > 0 && (
            <Button
              variant="outline"
              onClick={handleBulkTaxCategorize}
              className="flex items-center gap-1"
            >
              <Calculator className="h-4 w-4" />
              Tax Categorize ({selectedTransactions.length})
            </Button>
          )}

          {/* Quick filter for uncategorized */}
          <Button
            variant="outline"
            onClick={() => {
              // Filter to show only uncategorized transactions
              // This would depend on your filtering implementation
            }}
          >
            Show Uncategorized
          </Button>
        </div>
      </div>

      {/* Enhanced transactions table */}
      <div className="bg-white rounded-lg border">
        <TransactionsTable
          transactions={transactions}
          accounts={accounts}
          categories={categories}
          isLoading={isLoading}
          onTransactionSelect={(transaction) => {
            // You can either open the existing detail modal or the tax modal
            handleTaxCategorize(transaction)
          }}
          onTransactionUpdate={handleTransactionUpdate}
          onTransactionDelete={(id) => {
            // Handle deletion
          }}
          onRowSelectionChange={setSelectedTransactions}
          // Add custom action for tax categorization
          customActions={(transaction) => (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleTaxCategorize(transaction)}
              className="flex items-center gap-1"
            >
              <Calculator className="h-3 w-3" />
              Tax
            </Button>
          )}
        />
      </div>

      {/* Tax categorization modals */}
      {selectedTransaction && (
        <TaxCategorizationModal
          isOpen={isTaxModalOpen}
          onClose={() => {
            setIsTaxModalOpen(false)
            setSelectedTransaction(null)
          }}
          transaction={selectedTransaction}
          onTransactionUpdated={handleTransactionUpdate}
        />
      )}

      <BulkTaxCategorization
        isOpen={isBulkTaxModalOpen}
        onClose={() => setIsBulkTaxModalOpen(false)}
        transactions={selectedTransactions}
        onTransactionsUpdated={handleBulkTransactionsUpdate}
      />
    </div>
  )
}

// Example of adding tax categorization button to transaction row actions
export function TaxCategorizeButton({ transaction, onCategorize }) {
  const hasTaxCategorization = !!transaction.tax_categorization
  const isExpense = transaction.amount < 0

  // Only show for expenses (potential deductions)
  if (!isExpense) return null

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => onCategorize(transaction)}
      className={`flex items-center gap-1 ${
        hasTaxCategorization ? 'text-green-600' : 'text-gray-600'
      }`}
      title={hasTaxCategorization ? 'Edit tax categorization' : 'Add tax categorization'}
    >
      <Calculator className="h-3 w-3" />
      {hasTaxCategorization ? 'Edit Tax' : 'Tax'}
    </Button>
  )
}

// Example of tax status indicator for transaction rows
export function TaxStatusIndicator({ transaction }) {
  const taxCat = transaction.tax_categorization

  if (!taxCat) {
    return (
      <Badge variant="outline" className="text-xs text-gray-600">
        Not categorized
      </Badge>
    )
  }

  const hasReceipt = !!taxCat.receipt_url
  const hasPurpose = !!taxCat.business_purpose
  const businessUse = taxCat.business_use_percentage

  let status = 'complete'
  let color = 'text-green-600 bg-green-50 border-green-200'

  if (!hasReceipt || !hasPurpose) {
    status = 'incomplete'
    color = 'text-yellow-600 bg-yellow-50 border-yellow-200'
  }

  return (
    <div className="flex items-center gap-2">
      <Badge variant="outline" className={`text-xs ${color}`}>
        {businessUse}% business
      </Badge>
      {hasReceipt && (
        <Receipt className="h-3 w-3 text-green-600" title="Has receipt" />
      )}
      {hasPurpose && (
        <FileText className="h-3 w-3 text-blue-600" title="Has business purpose" />
      )}
    </div>
  )
}

// Example of integrating tax filters into existing filter system
export function TaxFilters({ onFilterChange, currentFilters }) {
  return (
    <div className="flex items-center gap-2">
      <select
        value={currentFilters.taxStatus || ''}
        onChange={(e) => onFilterChange({ ...currentFilters, taxStatus: e.target.value })}
        className="px-3 py-2 border border-gray-300 rounded-md text-sm"
      >
        <option value="">All Tax Status</option>
        <option value="categorized">Tax Categorized</option>
        <option value="uncategorized">Not Categorized</option>
        <option value="complete">Complete Documentation</option>
        <option value="incomplete">Incomplete Documentation</option>
      </select>

      <select
        value={currentFilters.deductible || ''}
        onChange={(e) => onFilterChange({ ...currentFilters, deductible: e.target.value })}
        className="px-3 py-2 border border-gray-300 rounded-md text-sm"
      >
        <option value="">All Transactions</option>
        <option value="deductible">Business Deductible</option>
        <option value="personal">Personal Expenses</option>
      </select>
    </div>
  )
}