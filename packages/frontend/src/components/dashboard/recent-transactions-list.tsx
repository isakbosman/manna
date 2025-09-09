'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency } from '@/lib/utils'
import { format, parseISO, isToday, isYesterday, isThisWeek } from 'date-fns'
import { 
  ArrowUpRight, 
  ArrowDownLeft, 
  CreditCard, 
  Building2,
  ShoppingCart,
  Car,
  Home,
  Coffee,
  Smartphone,
  MoreHorizontal,
  TrendingUp,
  Filter
} from 'lucide-react'

export interface Transaction {
  id: string
  date: string
  description: string
  amount: number
  category: string
  account: string
  merchant?: string
  pending?: boolean
  type?: 'debit' | 'credit'
}

interface RecentTransactionsListProps {
  transactions: Transaction[]
  isLoading?: boolean
  className?: string
  maxItems?: number
  showFilters?: boolean
  onTransactionClick?: (transaction: Transaction) => void
  onViewAll?: () => void
}

const getCategoryIcon = (category: string) => {
  const categoryMap: Record<string, React.ElementType> = {
    'Food & Dining': Coffee,
    'Groceries': ShoppingCart,
    'Transportation': Car,
    'Housing': Home,
    'Utilities': Building2,
    'Shopping': ShoppingCart,
    'Entertainment': Smartphone,
    'Income': TrendingUp,
    'Transfer': ArrowUpRight,
    'Payment': CreditCard,
  }

  const Icon = categoryMap[category] || MoreHorizontal
  return Icon
}

const getRelativeDate = (dateString: string) => {
  try {
    const date = parseISO(dateString)
    
    if (isToday(date)) {
      return 'Today'
    } else if (isYesterday(date)) {
      return 'Yesterday'
    } else if (isThisWeek(date)) {
      return format(date, 'EEEE')
    } else {
      return format(date, 'MMM dd')
    }
  } catch {
    return dateString
  }
}

const LoadingSkeleton = ({ count = 5 }: { count?: number }) => (
  <div className="space-y-4">
    {[...Array(count)].map((_, i) => (
      <div key={i} className="animate-pulse flex items-center space-x-3">
        <div className="w-10 h-10 bg-neutral-200 rounded-full"></div>
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-neutral-200 rounded w-3/4"></div>
          <div className="h-3 bg-neutral-200 rounded w-1/2"></div>
        </div>
        <div className="h-4 bg-neutral-200 rounded w-20"></div>
      </div>
    ))}
  </div>
)

export function RecentTransactionsList({
  transactions,
  isLoading = false,
  className = '',
  maxItems = 10,
  showFilters = false,
  onTransactionClick,
  onViewAll
}: RecentTransactionsListProps) {
  const displayTransactions = transactions.slice(0, maxItems)

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Recent Transactions</CardTitle>
            {showFilters && (
              <Filter className="h-4 w-4 text-neutral-400" />
            )}
          </div>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton count={maxItems} />
        </CardContent>
      </Card>
    )
  }

  if (transactions.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <CreditCard className="h-12 w-12 text-neutral-300 mx-auto mb-3" />
            <p className="text-neutral-600 mb-2">No transactions found</p>
            <p className="text-sm text-neutral-500">
              Connect accounts to see your transaction history
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Recent Transactions</CardTitle>
          <div className="flex items-center space-x-2">
            {showFilters && (
              <button className="p-1 hover:bg-neutral-100 rounded">
                <Filter className="h-4 w-4 text-neutral-400" />
              </button>
            )}
            {onViewAll && transactions.length > maxItems && (
              <button
                onClick={onViewAll}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                View all
              </button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {displayTransactions.map((transaction) => {
            const Icon = getCategoryIcon(transaction.category)
            const isIncome = transaction.amount > 0
            const isTransfer = transaction.category.toLowerCase().includes('transfer')
            
            return (
              <div
                key={transaction.id}
                className={`flex items-center space-x-3 p-2 rounded-lg transition-colors ${
                  onTransactionClick 
                    ? 'hover:bg-neutral-50 cursor-pointer' 
                    : ''
                } ${
                  transaction.pending ? 'opacity-70' : ''
                }`}
                onClick={() => onTransactionClick?.(transaction)}
              >
                {/* Transaction Icon */}
                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                  isIncome 
                    ? 'bg-success-100 text-success-600'
                    : isTransfer
                    ? 'bg-primary-100 text-primary-600'
                    : 'bg-neutral-100 text-neutral-600'
                }`}>
                  <Icon className="h-5 w-5" />
                </div>

                {/* Transaction Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-neutral-900 truncate">
                      {transaction.description}
                      {transaction.pending && (
                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-warning-100 text-warning-800">
                          Pending
                        </span>
                      )}
                    </h4>
                    <div className="flex-shrink-0 ml-4">
                      <p className={`text-sm font-medium ${
                        isIncome 
                          ? 'text-success-600' 
                          : 'text-error-600'
                      }`}>
                        {isIncome ? '+' : ''}{formatCurrency(transaction.amount)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between mt-1">
                    <div className="flex items-center space-x-2 text-xs text-neutral-500">
                      <span>{transaction.category}</span>
                      <span>•</span>
                      <span>{transaction.account}</span>
                      {transaction.merchant && (
                        <>
                          <span>•</span>
                          <span>{transaction.merchant}</span>
                        </>
                      )}
                    </div>
                    <span className="text-xs text-neutral-500 flex-shrink-0">
                      {getRelativeDate(transaction.date)}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Summary Footer */}
        {transactions.length > 0 && (
          <div className="mt-6 pt-4 border-t">
            <div className="flex justify-between text-sm">
              <span className="text-neutral-600">
                Showing {Math.min(maxItems, transactions.length)} of {transactions.length} transactions
              </span>
              <div className="flex space-x-4">
                <span className="text-success-600">
                  Income: {formatCurrency(
                    transactions.filter(t => t.amount > 0).reduce((sum, t) => sum + t.amount, 0)
                  )}
                </span>
                <span className="text-error-600">
                  Expenses: {formatCurrency(
                    Math.abs(transactions.filter(t => t.amount < 0).reduce((sum, t) => sum + t.amount, 0))
                  )}
                </span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}