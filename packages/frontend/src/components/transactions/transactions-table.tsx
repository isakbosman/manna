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
  BrainIcon
} from 'lucide-react'
import { DataTable } from '../ui/data-table'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Transaction, Account, Category } from '@/lib/api'
import { transactionsApi } from '@/lib/api/transactions'
import { categoriesApi } from '@/lib/api/categories'
import { cn } from '../../lib/utils'
import { format } from 'date-fns'

interface TransactionsTableProps {
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

export function TransactionsTable({
  transactions,
  accounts,
  categories,
  isLoading = false,
  onTransactionSelect,
  onTransactionUpdate,
  onTransactionDelete,
  onRowSelectionChange,
  className
}: TransactionsTableProps) {
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
    return amount < 0 ? 'text-error-600' : 'text-success-600'
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

  const columns: ColumnDef<Transaction>[] = [
    {
      accessorKey: 'date',
      header: 'Date',
      cell: ({ row }) => {
        const date = new Date(row.getValue('date'))
        return (
          <div className="flex items-center gap-2">
            <CalendarIcon className="h-4 w-4 text-neutral-500" />
            <div>
              <p className="font-medium">
                {format(date, 'MMM d')}
              </p>
              <p className="text-xs text-neutral-500">
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
              className="text-left hover:text-primary-600 transition-colors"
            >
              <p className="font-medium truncate">
                {transaction.description}
              </p>
              {transaction.merchant_name && (
                <p className="text-sm text-neutral-600 truncate">
                  {transaction.merchant_name}
                </p>
              )}
            </button>
            
            {/* Status indicators */}
            <div className="flex items-center gap-1 mt-1">
              {transaction.is_pending && (
                <Badge variant="warning" className="text-xs">
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
              variant={category?.type === 'income' ? 'success' : 
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
      accessorKey: 'amount',
      header: 'Amount',
      cell: ({ row }) => {
        const amount = row.getValue('amount') as number
        return (
          <div className="text-right">
            <p className={cn('font-medium', getAmountColor(amount))}>
              {formatAmount(amount)}
            </p>
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
            <BuildingIcon className="h-4 w-4 text-neutral-500" />
            <div>
              <p className="text-sm font-medium">{account.name}</p>
              <p className="text-xs text-neutral-500">{account.subtype}</p>
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
              <div className="absolute right-0 top-8 z-50 w-48 rounded-md border border-neutral-200 bg-white py-1 shadow-lg">
                <button
                  onClick={() => {
                    onTransactionSelect(transaction)
                    setShowMenu(false)
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-neutral-50"
                >
                  <EyeIcon className="h-4 w-4" />
                  View Details
                </button>
                
                <button
                  onClick={() => {
                    // Edit functionality would open the detail modal in edit mode
                    onTransactionSelect(transaction)
                    setShowMenu(false)
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-neutral-50"
                >
                  <EditIcon className="h-4 w-4" />
                  Edit
                </button>
                
                <button
                  onClick={() => {
                    handleMLCategorize(transaction)
                    setShowMenu(false)
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-neutral-50"
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
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-error-600 hover:bg-error-50"
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

  return (
    <div className={className}>
      <DataTable
        columns={columns}
        data={transactions}
        enableRowSelection={true}
        enableSorting={true}
        enableFiltering={false} // We handle filtering at the parent level
        enablePagination={true}
        pageSize={25}
        loading={isLoading}
        onRowSelectionChange={onRowSelectionChange}
        searchPlaceholder="Search transactions..."
        emptyMessage="No transactions found. Try adjusting your filters or sync your accounts."
      />
    </div>
  )
}