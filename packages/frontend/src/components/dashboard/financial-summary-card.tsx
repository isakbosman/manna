'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { formatCurrency } from '../../lib/utils'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Minus,
  Building2,
  CreditCard,
  Wallet
} from 'lucide-react'

interface FinancialSummaryData {
  totalAssets: number
  totalLiabilities: number
  netWorth: number
  liquidAssets: number
  monthlyChange: {
    assets: number
    liabilities: number
    netWorth: number
  }
  breakdown: {
    checking: number
    savings: number
    investments: number
    creditCards: number
    loans: number
    other: number
  }
}

interface FinancialSummaryCardProps {
  data: FinancialSummaryData
  isLoading?: boolean
  className?: string
}

const LoadingSkeleton = () => (
  <div className="animate-pulse space-y-4">
    <div className="grid grid-cols-3 gap-4">
      {[...Array(3)].map((_, i) => (
        <div key={i} className="space-y-2">
          <div className="h-4 bg-neutral-200 rounded w-20"></div>
          <div className="h-8 bg-neutral-200 rounded w-28"></div>
          <div className="h-3 bg-neutral-200 rounded w-16"></div>
        </div>
      ))}
    </div>
    <div className="border-t pt-4">
      <div className="space-y-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="flex justify-between">
            <div className="h-4 bg-neutral-200 rounded w-24"></div>
            <div className="h-4 bg-neutral-200 rounded w-20"></div>
          </div>
        ))}
      </div>
    </div>
  </div>
)

const ChangeIndicator = ({ value, showIcon = true }: { value: number, showIcon?: boolean }) => {
  const isPositive = value > 0
  const isZero = value === 0
  
  const color = isZero 
    ? 'text-neutral-600' 
    : isPositive 
    ? 'text-success-600' 
    : 'text-error-600'

  const Icon = isZero ? Minus : isPositive ? TrendingUp : TrendingDown

  return (
    <div className={`flex items-center text-xs ${color}`}>
      {showIcon && <Icon className="h-3 w-3 mr-1" />}
      <span>
        {isPositive ? '+' : ''}{formatCurrency(value)} this month
      </span>
    </div>
  )
}

export function FinancialSummaryCard({ 
  data, 
  isLoading = false, 
  className = '' 
}: FinancialSummaryCardProps) {
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Building2 className="h-5 w-5 mr-2" />
            Financial Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton />
        </CardContent>
      </Card>
    )
  }

  const netWorthColor = data.netWorth >= 0 ? 'text-success-600' : 'text-error-600'
  const liquidityRatio = data.totalAssets > 0 ? (data.liquidAssets / data.totalAssets) * 100 : 0
  const debtToAssetRatio = data.totalAssets > 0 ? (Math.abs(data.totalLiabilities) / data.totalAssets) * 100 : 0

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Building2 className="h-5 w-5 mr-2" />
          Financial Summary
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Main Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 rounded-lg bg-neutral-50">
            <div className="flex justify-center items-center mb-2">
              <Wallet className="h-4 w-4 text-success-600 mr-1" />
              <span className="text-sm font-medium text-neutral-700">Total Assets</span>
            </div>
            <div className="text-2xl font-bold text-success-600 mb-1">
              {formatCurrency(data.totalAssets)}
            </div>
            <ChangeIndicator value={data.monthlyChange.assets} />
          </div>

          <div className="text-center p-4 rounded-lg bg-neutral-50">
            <div className="flex justify-center items-center mb-2">
              <CreditCard className="h-4 w-4 text-error-600 mr-1" />
              <span className="text-sm font-medium text-neutral-700">Total Liabilities</span>
            </div>
            <div className="text-2xl font-bold text-error-600 mb-1">
              {formatCurrency(Math.abs(data.totalLiabilities))}
            </div>
            <ChangeIndicator value={data.monthlyChange.liabilities} />
          </div>

          <div className="text-center p-4 rounded-lg bg-primary-50">
            <div className="flex justify-center items-center mb-2">
              <DollarSign className="h-4 w-4 text-primary-600 mr-1" />
              <span className="text-sm font-medium text-neutral-700">Net Worth</span>
            </div>
            <div className={`text-2xl font-bold mb-1 ${netWorthColor}`}>
              {formatCurrency(data.netWorth)}
            </div>
            <ChangeIndicator value={data.monthlyChange.netWorth} />
          </div>
        </div>

        {/* Account Breakdown */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-neutral-700 mb-3">Account Breakdown</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-neutral-600">Checking Accounts</span>
              <span className="text-sm font-medium">
                {formatCurrency(data.breakdown.checking)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-neutral-600">Savings Accounts</span>
              <span className="text-sm font-medium">
                {formatCurrency(data.breakdown.savings)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-neutral-600">Investments</span>
              <span className="text-sm font-medium">
                {formatCurrency(data.breakdown.investments)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-neutral-600">Credit Cards</span>
              <span className="text-sm font-medium text-error-600">
                {formatCurrency(Math.abs(data.breakdown.creditCards))}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-neutral-600">Loans</span>
              <span className="text-sm font-medium text-error-600">
                {formatCurrency(Math.abs(data.breakdown.loans))}
              </span>
            </div>
          </div>
        </div>

        {/* Financial Health Indicators */}
        <div className="border-t pt-4 mt-4">
          <h4 className="text-sm font-medium text-neutral-700 mb-3">Financial Health</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-neutral-50">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-neutral-600">Liquidity Ratio</span>
                <span className={`text-sm font-medium ${
                  liquidityRatio >= 20 ? 'text-success-600' : 'text-warning-600'
                }`}>
                  {liquidityRatio.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-neutral-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    liquidityRatio >= 20 ? 'bg-success-500' : 'bg-warning-500'
                  }`}
                  style={{ width: `${Math.min(liquidityRatio, 100)}%` }}
                ></div>
              </div>
              <p className="text-xs text-neutral-500 mt-1">
                {liquidityRatio >= 20 ? 'Good liquidity' : 'Consider increasing liquid assets'}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-neutral-50">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-neutral-600">Debt-to-Asset Ratio</span>
                <span className={`text-sm font-medium ${
                  debtToAssetRatio <= 40 ? 'text-success-600' : 
                  debtToAssetRatio <= 60 ? 'text-warning-600' : 'text-error-600'
                }`}>
                  {debtToAssetRatio.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-neutral-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    debtToAssetRatio <= 40 ? 'bg-success-500' : 
                    debtToAssetRatio <= 60 ? 'bg-warning-500' : 'bg-error-500'
                  }`}
                  style={{ width: `${Math.min(debtToAssetRatio, 100)}%` }}
                ></div>
              </div>
              <p className="text-xs text-neutral-500 mt-1">
                {debtToAssetRatio <= 40 ? 'Healthy debt level' : 
                 debtToAssetRatio <= 60 ? 'Moderate debt level' : 'High debt level - consider reducing'}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}