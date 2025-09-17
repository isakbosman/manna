'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { formatCurrency, formatPercentage } from '../../lib/utils'
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle,
  Target,
  Calendar
} from 'lucide-react'

export interface Budget {
  id: string
  category: string
  budgetAmount: number
  spentAmount: number
  period: 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  startDate: string
  endDate: string
  status: 'on-track' | 'warning' | 'over-budget' | 'completed'
  remainingDays: number
}

interface BudgetProgressIndicatorsProps {
  budgets: Budget[]
  isLoading?: boolean
  className?: string
  maxItems?: number
  onBudgetClick?: (budget: Budget) => void
  onViewAll?: () => void
}

const getBudgetStatusIcon = (status: string) => {
  switch (status) {
    case 'on-track':
      return CheckCircle
    case 'warning':
      return AlertTriangle
    case 'over-budget':
      return TrendingUp
    case 'completed':
      return Target
    default:
      return Target
  }
}

const getBudgetStatusColor = (status: string, percentage: number) => {
  switch (status) {
    case 'on-track':
      return 'text-success-600 border-success-200 bg-success-50'
    case 'warning':
      return 'text-warning-600 border-warning-200 bg-warning-50'
    case 'over-budget':
      return 'text-error-600 border-error-200 bg-error-50'
    case 'completed':
      return 'text-primary-600 border-primary-200 bg-primary-50'
    default:
      return 'text-neutral-600 border-neutral-200 bg-neutral-50'
  }
}

const getProgressBarColor = (percentage: number) => {
  if (percentage <= 50) return 'bg-success-500'
  if (percentage <= 80) return 'bg-warning-500'
  return 'bg-error-500'
}

const LoadingSkeleton = ({ count = 4 }: { count?: number }) => (
  <div className="space-y-4">
    {[...Array(count)].map((_, i) => (
      <div key={i} className="animate-pulse border rounded-lg p-4">
        <div className="flex justify-between items-start mb-3">
          <div className="space-y-2">
            <div className="h-4 bg-neutral-200 rounded w-24"></div>
            <div className="h-3 bg-neutral-200 rounded w-16"></div>
          </div>
          <div className="w-6 h-6 bg-neutral-200 rounded"></div>
        </div>
        <div className="space-y-2">
          <div className="w-full bg-neutral-200 rounded-full h-2"></div>
          <div className="flex justify-between">
            <div className="h-3 bg-neutral-200 rounded w-16"></div>
            <div className="h-3 bg-neutral-200 rounded w-12"></div>
          </div>
        </div>
      </div>
    ))}
  </div>
)

export function BudgetProgressIndicators({
  budgets,
  isLoading = false,
  className = '',
  maxItems = 6,
  onBudgetClick,
  onViewAll
}: BudgetProgressIndicatorsProps) {
  const displayBudgets = budgets.slice(0, maxItems)

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Target className="h-5 w-5 mr-2" />
            Budget Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton count={maxItems} />
        </CardContent>
      </Card>
    )
  }

  if (budgets.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Target className="h-5 w-5 mr-2" />
            Budget Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Target className="h-12 w-12 text-neutral-300 mx-auto mb-3" />
            <p className="text-neutral-600 mb-2">No budgets set up yet</p>
            <p className="text-sm text-neutral-500">
              Create budgets to track your spending goals
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Calculate summary statistics
  const totalBudgeted = budgets.reduce((sum, budget) => sum + budget.budgetAmount, 0)
  const totalSpent = budgets.reduce((sum, budget) => sum + budget.spentAmount, 0)
  const overBudgetCount = budgets.filter(b => b.status === 'over-budget').length
  const onTrackCount = budgets.filter(b => b.status === 'on-track').length

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center">
            <Target className="h-5 w-5 mr-2" />
            Budget Progress
          </CardTitle>
          {onViewAll && budgets.length > maxItems && (
            <button
              onClick={onViewAll}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              View all
            </button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6 p-3 bg-neutral-50 rounded-lg">
          <div className="text-center">
            <p className="text-xs text-neutral-600">Total Budgeted</p>
            <p className="text-sm font-bold text-neutral-900">
              {formatCurrency(totalBudgeted)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-neutral-600">Total Spent</p>
            <p className="text-sm font-bold text-neutral-900">
              {formatCurrency(totalSpent)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-neutral-600">Utilization</p>
            <p className={`text-sm font-bold ${
              (totalSpent / totalBudgeted) <= 0.8 ? 'text-success-600' : 'text-warning-600'
            }`}>
              {formatPercentage((totalSpent / totalBudgeted) * 100)}
            </p>
          </div>
        </div>

        {/* Budget Items */}
        <div className="space-y-4">
          {displayBudgets.map((budget) => {
            const percentage = (budget.spentAmount / budget.budgetAmount) * 100
            const remaining = budget.budgetAmount - budget.spentAmount
            const StatusIcon = getBudgetStatusIcon(budget.status)
            const statusColorClass = getBudgetStatusColor(budget.status, percentage)
            const progressBarColor = getProgressBarColor(percentage)

            return (
              <div
                key={budget.id}
                className={`border rounded-lg p-4 transition-all hover:shadow-sm ${
                  onBudgetClick ? 'cursor-pointer' : ''
                } ${statusColorClass}`}
                onClick={() => onBudgetClick?.(budget)}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-medium text-sm">{budget.category}</h4>
                    <p className="text-xs opacity-75 capitalize">
                      {budget.period} budget • {budget.remainingDays} days left
                    </p>
                  </div>
                  <StatusIcon className="h-5 w-5 opacity-75" />
                </div>

                <div className="space-y-2">
                  <div className="w-full bg-neutral-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${progressBarColor}`}
                      style={{ width: `${Math.min(percentage, 100)}%` }}
                    />
                  </div>

                  <div className="flex justify-between text-xs">
                    <span>
                      {formatCurrency(budget.spentAmount)} of {formatCurrency(budget.budgetAmount)}
                    </span>
                    <span className={percentage > 100 ? 'text-error-600 font-medium' : ''}>
                      {percentage.toFixed(0)}%
                    </span>
                  </div>

                  <div className="flex justify-between items-center pt-1 border-t border-opacity-50">
                    <span className="text-xs opacity-75">
                      {remaining >= 0 ? 'Remaining' : 'Over budget'}
                    </span>
                    <span className={`text-xs font-medium ${
                      remaining >= 0 ? 'text-success-600' : 'text-error-600'
                    }`}>
                      {remaining >= 0 ? formatCurrency(remaining) : formatCurrency(-remaining)}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Health Summary */}
        <div className="mt-4 pt-4 border-t">
          <div className="flex justify-between text-sm">
            <span className="text-neutral-600">Budget Health</span>
            <div className="flex space-x-3">
              <span className="text-success-600">{onTrackCount} on track</span>
              {overBudgetCount > 0 && (
                <span className="text-error-600">{overBudgetCount} over budget</span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}