'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { formatCurrency } from '../../lib/utils'
import { 
  CreditCard, 
  Building2, 
  Wallet, 
  TrendingUp, 
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  Eye,
  EyeOff
} from 'lucide-react'
import { useState } from 'react'

export interface Account {
  id: string
  name: string
  type: 'checking' | 'savings' | 'credit' | 'investment' | 'loan'
  balance_current: number
  balance_available?: number
  mask?: string
  institution: string
  last_updated: string
  status: 'active' | 'inactive' | 'error' | 'pending'
  currency?: string
  credit_limit?: number
  minimum_payment?: number
  next_payment_due?: string
}

interface AccountBalanceCardsProps {
  accounts: Account[]
  isLoading?: boolean
  className?: string
  showBalances?: boolean
  onAccountClick?: (account: Account) => void
  onRefresh?: () => void
}

const getAccountIcon = (type: string) => {
  const iconMap: Record<string, React.ElementType> = {
    checking: Wallet,
    savings: Building2,
    credit: CreditCard,
    investment: TrendingUp,
    loan: DollarSign,
  }
  return iconMap[type] || Wallet
}

const getAccountColor = (type: string, balance: number) => {
  switch (type) {
    case 'checking':
    case 'savings':
      return balance >= 0 
        ? 'border-success-200 bg-success-50' 
        : 'border-error-200 bg-error-50'
    case 'credit':
      // For credit cards, negative balance means money owed
      return balance <= 0 
        ? 'border-warning-200 bg-warning-50' 
        : 'border-success-200 bg-success-50'
    case 'investment':
      return balance >= 0 
        ? 'border-primary-200 bg-primary-50' 
        : 'border-error-200 bg-error-50'
    case 'loan':
      return 'border-neutral-200 bg-neutral-50'
    default:
      return 'border-neutral-200 bg-white'
  }
}

const getBalanceColor = (type: string, balance: number) => {
  switch (type) {
    case 'checking':
    case 'savings':
      return balance >= 0 ? 'text-success-600' : 'text-error-600'
    case 'credit':
      return balance <= 0 ? 'text-warning-600' : 'text-success-600'
    case 'investment':
      return balance >= 0 ? 'text-primary-600' : 'text-error-600'
    case 'loan':
      return 'text-neutral-700'
    default:
      return 'text-neutral-900'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'active':
      return <CheckCircle className="h-4 w-4 text-success-500" />
    case 'error':
      return <AlertTriangle className="h-4 w-4 text-error-500" />
    case 'pending':
      return <Clock className="h-4 w-4 text-warning-500" />
    case 'inactive':
      return <AlertTriangle className="h-4 w-4 text-neutral-400" />
    default:
      return null
  }
}

const formatAccountNumber = (mask?: string) => {
  if (!mask) return ''
  return `••••${mask}`
}

const LoadingSkeleton = ({ count = 4 }: { count?: number }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 gap-4">
    {[...Array(count)].map((_, i) => (
      <Card key={i} className="animate-pulse">
        <CardHeader className="pb-2">
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <div className="h-4 bg-neutral-200 rounded w-24"></div>
              <div className="h-3 bg-neutral-200 rounded w-16"></div>
            </div>
            <div className="w-6 h-6 bg-neutral-200 rounded"></div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="h-8 bg-neutral-200 rounded w-28"></div>
            <div className="h-3 bg-neutral-200 rounded w-20"></div>
          </div>
        </CardContent>
      </Card>
    ))}
  </div>
)

export function AccountBalanceCards({
  accounts,
  isLoading = false,
  className = '',
  showBalances: initialShowBalances = true,
  onAccountClick,
  onRefresh
}: AccountBalanceCardsProps) {
  const [showBalances, setShowBalances] = useState(initialShowBalances)

  if (isLoading) {
    return (
      <div className={className}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Account Balances</h3>
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 bg-neutral-200 rounded animate-pulse"></div>
            <div className="w-16 h-6 bg-neutral-200 rounded animate-pulse"></div>
          </div>
        </div>
        <LoadingSkeleton count={4} />
      </div>
    )
  }

  if (accounts.length === 0) {
    return (
      <div className={className}>
        <h3 className="text-lg font-semibold mb-4">Account Balances</h3>
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <CreditCard className="h-12 w-12 text-neutral-300 mx-auto mb-3" />
              <p className="text-neutral-600 mb-2">No accounts connected</p>
              <p className="text-sm text-neutral-500">
                Connect your financial accounts to see balance information
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const totalBalance = accounts.reduce((sum, account) => {
    // For credit cards and loans, we want to show debt as negative
    if (account.type === 'credit' || account.type === 'loan') {
      return sum - Math.abs(account.balance_current)
    }
    return sum + account.balance_current
  }, 0)

  return (
    <div className={className}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Account Balances</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowBalances(!showBalances)}
            className="p-1 hover:bg-neutral-100 rounded transition-colors"
            title={showBalances ? 'Hide balances' : 'Show balances'}
          >
            {showBalances ? (
              <EyeOff className="h-4 w-4 text-neutral-600" />
            ) : (
              <Eye className="h-4 w-4 text-neutral-600" />
            )}
          </button>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="text-sm text-primary-600 hover:text-primary-700 transition-colors"
            >
              Refresh
            </button>
          )}
        </div>
      </div>

      {/* Total Balance Summary */}
      <Card className="mb-4 border-2 border-primary-200 bg-primary-50">
        <CardContent className="py-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-neutral-600">Total Net Worth</p>
              <p className={`text-2xl font-bold ${
                totalBalance >= 0 ? 'text-success-600' : 'text-error-600'
              }`}>
                {showBalances ? formatCurrency(totalBalance) : '••••••'}
              </p>
            </div>
            <Building2 className="h-8 w-8 text-primary-600" />
          </div>
        </CardContent>
      </Card>

      {/* Account Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 gap-4">
        {accounts.map((account) => {
          const Icon = getAccountIcon(account.type)
          const colorClasses = getAccountColor(account.type, account.balance_current)
          const balanceColor = getBalanceColor(account.type, account.balance_current)

          return (
            <Card
              key={account.id}
              className={`transition-all hover:shadow-md ${colorClasses} ${
                onAccountClick ? 'cursor-pointer' : ''
              }`}
              onClick={() => onAccountClick?.(account)}
            >
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-neutral-900 truncate">
                      {account.name}
                    </p>
                    <p className="text-xs text-neutral-600">
                      {account.institution}
                    </p>
                    {account.mask && (
                      <p className="text-xs text-neutral-500 mt-1">
                        {formatAccountNumber(account.mask)}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-col items-end space-y-1">
                    <Icon className="h-5 w-5 text-neutral-600" />
                    {getStatusIcon(account.status)}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div>
                    <p className="text-xs text-neutral-600">
                      {account.type === 'credit' ? 'Balance' : 'Current Balance'}
                    </p>
                    <p className={`text-xl font-bold ${balanceColor}`}>
                      {showBalances ? formatCurrency(account.balance_current) : '••••••'}
                    </p>
                  </div>

                  {/* Additional Info based on account type */}
                  {account.type === 'credit' && account.credit_limit && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-neutral-600">Credit Limit</span>
                        <span className="text-neutral-700">
                          {showBalances ? formatCurrency(account.credit_limit) : '••••••'}
                        </span>
                      </div>
                      {account.credit_limit > 0 && (
                        <div className="w-full bg-neutral-200 rounded-full h-1">
                          <div
                            className={`h-1 rounded-full ${
                              (Math.abs(account.balance_current) / account.credit_limit) > 0.8
                                ? 'bg-error-500'
                                : (Math.abs(account.balance_current) / account.credit_limit) > 0.5
                                ? 'bg-warning-500'
                                : 'bg-success-500'
                            }`}
                            style={{
                              width: `${Math.min(
                                (Math.abs(account.balance_current) / account.credit_limit) * 100,
                                100
                              )}%`
                            }}
                          />
                        </div>
                      )}
                    </div>
                  )}

                  {account.balance_available !== undefined && 
                   account.balance_available !== account.balance_current && (
                    <div className="text-xs text-neutral-600">
                      Available: {showBalances ? formatCurrency(account.balance_available) : '••••••'}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}