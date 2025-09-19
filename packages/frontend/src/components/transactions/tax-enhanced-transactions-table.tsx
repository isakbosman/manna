import React from 'react'
import {
  ColumnDef,
  Row
} from '@tanstack/react-table'
import {
  MoreHorizontalIcon,
  EditIcon,
  TrashIcon,
  TagIcon,
  EyeIcon,
  CalendarIcon,
  BuildingIcon,
  BrainIcon,
  Calculator,
  Receipt,
  DollarSign,
  CheckCircle,
  AlertTriangle,
  FileText,
} from 'lucide-react'
import { DataTable } from '../ui/data-table'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Tooltip } from '../ui/tooltip'
import { Transaction, Account, Category } from '@/lib/api'
import { transactionsApi } from '@/lib/api/transactions'
import { categoriesApi } from '@/lib/api/categories'
import { TaxCategorizationModal, BulkTaxCategorization } from '../tax'
import { cn } from '../../lib/utils'
import { format } from 'date-fns'

interface TaxEnhancedTransactionsTableProps {
  transactions: Transaction[]
  accounts: Account[]
  categories: Category[]
  isLoading?: boolean
  onTransactionSelect: (transaction: Transaction) => void
  onTransactionUpdate: (transaction: Transaction) => void
  onTransactionDelete: (transactionId: string) => void
  onRowSelectionChange: (selectedTransactions: Transaction[]) => void
  className?: string
}

interface TransactionWithTax extends Transaction {
  tax_categorization?: {
    id: string
    tax_category_id: string
    business_use_percentage: number
    business_purpose?: string
    receipt_url?: string
    mileage?: number
  }
}

export function TaxEnhancedTransactionsTable({
  transactions,
  accounts,
  categories,
  isLoading = false,
  onTransactionSelect,
  onTransactionUpdate,
  onTransactionDelete,
  onRowSelectionChange,
  className
}: TaxEnhancedTransactionsTableProps) {
  const [selectedTransactions, setSelectedTransactions] = React.useState<Transaction[]>([])
  const [isTaxModalOpen, setIsTaxModalOpen] = React.useState<boolean>(false)
  const [isBulkTaxModalOpen, setIsBulkTaxModalOpen] = React.useState<boolean>(false)
  const [selectedTransactionForTax, setSelectedTransactionForTax] = React.useState<Transaction | null>(null)

  const formatAmount = (amount: number) => {
    const isNegative = amount < 0
    const absAmount = Math.abs(amount)
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(absAmount)

    return isNegative ? `-${formatted}` : formatted
  }

  const getAmountColor = (amount: number) => {
    return amount < 0 ? 'text-red-600' : 'text-green-600'
  }

  const getAccount = (accountId: string) => {
    return accounts.find(a => a.id === accountId)
  }

  const handleQuickCategorize = async (transaction: Transaction, categoryId: string) => {
    try {
      const updatedTransaction = await transactionsApi.updateTransaction(transaction.id, {
        category: categoryId
      })
      onTransactionUpdate(updatedTransaction)
    } catch (error) {
      console.error('Failed to update transaction category:', error)
    }
  }

  const handleMLCategorize = async (transaction: Transaction) => {
    try {
      const predictions = await categoriesApi.categorizeTransaction(transaction.id)
      if (predictions.length > 0) {
        const topPrediction = predictions[0]
        if (topPrediction.confidence > 0.8) {
          await handleQuickCategorize(transaction, topPrediction.category_id)
        }
      }
    } catch (error) {
      console.error('Failed to ML categorize:', error)
    }
  }

  const handleTaxCategorize = (transaction: Transaction) => {
    setSelectedTransactionForTax(transaction)
    setIsTaxModalOpen(true)
  }

  const handleBulkTaxCategorize = () => {
    if (selectedTransactions.length > 0) {
      setIsBulkTaxModalOpen(true)
    }
  }

  const getTaxStatus = (transaction: TransactionWithTax) => {
    const taxCat = transaction.tax_categorization
    if (!taxCat) return 'none'

    const hasReceipt = !!taxCat.receipt_url
    const hasPurpose = !!taxCat.business_purpose

    if (hasReceipt && hasPurpose) return 'complete'
    if (hasReceipt || hasPurpose) return 'partial'
    return 'minimal'
  }

  const getTaxStatusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'text-green-600 bg-green-50 border-green-200'
      case 'partial': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'minimal': return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'none': return 'text-gray-600 bg-gray-50 border-gray-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getTaxStatusIcon = (status: string) => {
    switch (status) {
      case 'complete': return <CheckCircle className="h-3 w-3" />
      case 'partial': return <AlertTriangle className="h-3 w-3" />
      case 'minimal': return <Calculator className="h-3 w-3" />
      case 'none': return <FileText className="h-3 w-3" />
      default: return <FileText className="h-3 w-3" />
    }
  }

  const columns: ColumnDef<TransactionWithTax>[] = [
    {
      accessorKey: 'date',
      header: 'Date',
      cell: ({ row }) => {
        const date = new Date(row.getValue('date'))
        return (
          <div className="flex items-center gap-2">
            <CalendarIcon className="h-4 w-4 text-gray-500" />
            <div>
              <p className="font-medium">
                {format(date, 'MMM d')}
              </p>
              <p className="text-xs text-gray-500">
                {format(date, 'yyyy')}
              </p>
            </div>
          </div>
        )
      },
    },
    {
      accessorKey: 'description',
      header: 'Description',
      cell: ({ row }) => {
        const transaction = row.original
        return (
          <div className="min-w-0">
            <button
              onClick={() => onTransactionSelect(transaction)}
              className="text-left hover:text-blue-600 transition-colors"
            >
              <p className="font-medium truncate">
                {transaction.description}
              </p>
              {transaction.merchant_name && (
                <p className="text-sm text-gray-600 truncate">
                  {transaction.merchant_name}
                </p>
              )}
            </button>

            {/* Status indicators */}
            <div className="flex items-center gap-1 mt-1">
              {transaction.is_pending && (
                <Badge variant="outline" className="text-xs text-yellow-600">
                  Pending
                </Badge>
              )}
            </div>
          </div>
        )
      },
    },
    {
      accessorKey: 'category',
      header: 'Category',
      cell: ({ row }) => {
        const transaction = row.original

        if (transaction.category) {
          const category = categories.find(c => c.name === transaction.category)
          return (
            <Badge
              variant={category?.type === 'income' ? 'default' :
                     category?.type === 'expense' ? 'destructive' : 'secondary'}
              className="text-xs"
            >
              {transaction.category}
            </Badge>
          )
        }

        return (
          <div className="flex items-center gap-2">
            <Select value="" onValueChange={(value) => value && handleQuickCategorize(transaction, value)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Uncategorized" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Select category</SelectItem>
                {categories.map(cat => (
                  <SelectItem key={cat.name} value={cat.name}>
                    <span className="flex items-center gap-2">
                      <span className="text-xs">{cat.type}</span>
                      {cat.name}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleMLCategorize(transaction)}
              className="h-6 w-6 p-0"
              title="AI Categorize"
            >
              <BrainIcon className="h-3 w-3" />
            </Button>
          </div>
        )
      },
    },
    {
      accessorKey: 'tax_categorization',
      header: 'Tax Status',
      cell: ({ row }) => {
        const transaction = row.original
        const taxStatus = getTaxStatus(transaction)
        const taxCat = transaction.tax_categorization

        return (
          <div className="flex items-center gap-2">
            <div className={cn(
              'flex items-center gap-1 px-2 py-1 rounded text-xs border',
              getTaxStatusColor(taxStatus)
            )}>
              {getTaxStatusIcon(taxStatus)}
              <span className="capitalize">
                {taxStatus === 'none' ? 'Not categorized' :
                 taxStatus === 'minimal' ? 'Basic' :
                 taxStatus === 'partial' ? 'Partial' : 'Complete'}
              </span>
            </div>

            {taxCat && (
              <Tooltip content={`Business use: ${taxCat.business_use_percentage}%`}>
                <Badge variant="outline" className="text-xs">
                  {taxCat.business_use_percentage}%
                </Badge>
              </Tooltip>
            )}

            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleTaxCategorize(transaction)}
              className="h-6 w-6 p-0"
              title="Tax Categorize"
            >
              <Calculator className="h-3 w-3" />
            </Button>
          </div>
        )
      },
    },
    {
      accessorKey: 'amount',
      header: 'Amount',
      cell: ({ row }) => {
        const amount = row.getValue('amount') as number
        const transaction = row.original
        const taxCat = transaction.tax_categorization

        let deductibleAmount = 0
        if (taxCat && amount < 0) { // Only expenses can be deductible
          deductibleAmount = Math.abs(amount) * (taxCat.business_use_percentage / 100)
        }

        return (
          <div className="text-right">
            <p className={cn('font-medium', getAmountColor(amount))}>
              {formatAmount(amount)}
            </p>
            {deductibleAmount > 0 && (
              <p className="text-xs text-green-600">
                Deductible: {formatAmount(deductibleAmount)}
              </p>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: 'account_id',
      header: 'Account',
      cell: ({ row }) => {
        const account = getAccount(row.getValue('account_id'))
        if (!account) return null

        return (
          <div className="flex items-center gap-2">
            <BuildingIcon className="h-4 w-4 text-gray-500" />
            <div>
              <p className="text-sm font-medium">{account.name}</p>
              <p className="text-xs text-gray-500">{account.subtype}</p>
            </div>
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => {
        const transaction = row.original
        const [showMenu, setShowMenu] = React.useState(false)

        return (
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowMenu(!showMenu)}
              className="h-8 w-8 p-0"
            >
              <MoreHorizontalIcon className="h-4 w-4" />
            </Button>

            {showMenu && (
              <div className="absolute right-0 top-8 z-50 w-48 rounded-md border border-gray-200 bg-white py-1 shadow-lg">
                <button
                  onClick={() => {
                    onTransactionSelect(transaction)
                    setShowMenu(false)
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50"
                >
                  <EyeIcon className="h-4 w-4" />
                  View Details
                </button>

                <button
                  onClick={() => {
                    handleTaxCategorize(transaction)
                    setShowMenu(false)
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50"
                >
                  <Calculator className="h-4 w-4" />
                  Tax Categorize
                </button>

                <button
                  onClick={() => {
                    // Edit functionality would open the detail modal in edit mode
                    onTransactionSelect(transaction)
                    setShowMenu(false)
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50"
                >
                  <EditIcon className="h-4 w-4" />
                  Edit
                </button>

                <button
                  onClick={() => {
                    handleMLCategorize(transaction)
                    setShowMenu(false)
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50"
                  disabled={!!transaction.category}
                >
                  <BrainIcon className="h-4 w-4" />
                  AI Categorize
                </button>

                <hr className="my-1" />

                <button
                  onClick={() => {
                    if (window.confirm('Are you sure you want to delete this transaction?')) {
                      onTransactionDelete(transaction.id)
                    }
                    setShowMenu(false)
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <TrashIcon className="h-4 w-4" />
                  Delete
                </button>
              </div>
            )}
          </div>
        )
      },
    },
  ]

  const handleRowSelectionChange = (newSelectedTransactions: Transaction[]) => {
    setSelectedTransactions(newSelectedTransactions)
    onRowSelectionChange(newSelectedTransactions)
  }

  const handleTransactionUpdated = (updatedTransaction: Transaction) => {
    onTransactionUpdate(updatedTransaction)
    setIsTaxModalOpen(false)
    setSelectedTransactionForTax(null)
  }

  const handleTransactionsUpdated = (updatedTransactions: Transaction[]) => {
    // Update multiple transactions
    updatedTransactions.forEach(transaction => {
      onTransactionUpdate(transaction)
    })
    setIsBulkTaxModalOpen(false)
    setSelectedTransactions([])
  }

  return (
    <div className={className}>
      {/* Bulk Actions Bar */}
      {selectedTransactions.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-blue-900">
              {selectedTransactions.length} transaction(s) selected
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleBulkTaxCategorize}
              >
                <Calculator className="h-4 w-4 mr-1" />
                Bulk Tax Categorize
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedTransactions([])}
              >
                Clear Selection
              </Button>
            </div>
          </div>
        </div>
      )}

      <DataTable
        columns={columns}
        data={transactions}
        enableRowSelection={true}
        enableSorting={true}
        enableFiltering={false} // We handle filtering at the parent level
        enablePagination={true}
        pageSize={25}
        loading={isLoading}
        onRowSelectionChange={handleRowSelectionChange}
        searchPlaceholder="Search transactions..."
        emptyMessage="No transactions found. Try adjusting your filters or sync your accounts."
      />

      {/* Tax Categorization Modal */}
      {selectedTransactionForTax && (
        <TaxCategorizationModal
          isOpen={isTaxModalOpen}
          onClose={() => {
            setIsTaxModalOpen(false)
            setSelectedTransactionForTax(null)
          }}
          transaction={selectedTransactionForTax}
          onTransactionUpdated={handleTransactionUpdated}
        />
      )}

      {/* Bulk Tax Categorization Modal */}
      <BulkTaxCategorization
        isOpen={isBulkTaxModalOpen}
        onClose={() => setIsBulkTaxModalOpen(false)}
        transactions={selectedTransactions}
        onTransactionsUpdated={handleTransactionsUpdated}
      />
    </div>
  )
}