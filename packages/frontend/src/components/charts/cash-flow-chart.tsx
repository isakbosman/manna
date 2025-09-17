'use client'

import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { formatCurrency } from '../../lib/utils'
import { format, parseISO } from 'date-fns'

interface CashFlowData {
  month: string
  income: number
  expenses: number
  netFlow: number
  runningBalance: number
}

interface CashFlowChartProps {
  data: CashFlowData[]
  isLoading?: boolean
  className?: string
  showRunningBalance?: boolean
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0]?.payload
    return (
      <div className="bg-white border border-neutral-200 rounded-lg shadow-lg p-3">
        <p className="font-medium text-neutral-900 mb-2">{label}</p>
        <div className="space-y-1">
          <p className="text-sm text-success-600">
            Income: <span className="font-medium">{formatCurrency(data.income)}</span>
          </p>
          <p className="text-sm text-error-600">
            Expenses: <span className="font-medium">{formatCurrency(Math.abs(data.expenses))}</span>
          </p>
          <p className={`text-sm font-medium ${
            data.netFlow >= 0 ? 'text-success-600' : 'text-error-600'
          }`}>
            Net Flow: {formatCurrency(data.netFlow)}
          </p>
          {data.runningBalance !== undefined && (
            <p className="text-sm text-neutral-700 border-t pt-1 mt-1">
              Balance: <span className="font-medium">{formatCurrency(data.runningBalance)}</span>
            </p>
          )}
        </div>
      </div>
    )
  }
  return null
}

const LoadingSkeleton = () => (
  <div className="h-80 flex items-center justify-center">
    <div className="animate-pulse w-full">
      <div className="flex justify-between mb-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="w-16 h-4 bg-neutral-200 rounded"></div>
        ))}
      </div>
      <div className="space-y-1">
        {[...Array(12)].map((_, i) => (
          <div key={i} className="flex space-x-1">
            <div className="w-full h-8 bg-neutral-200 rounded" style={{height: Math.random() * 60 + 20}}></div>
            <div className="w-full h-8 bg-neutral-200 rounded" style={{height: Math.random() * 60 + 20}}></div>
          </div>
        ))}
      </div>
    </div>
  </div>
)

export function CashFlowChart({
  data,
  isLoading = false,
  className = '',
  showRunningBalance = false
}: CashFlowChartProps) {
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Cash Flow Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton />
        </CardContent>
      </Card>
    )
  }

  if (data.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Cash Flow Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center">
            <div className="text-center">
              <p className="text-neutral-600 mb-2">No cash flow data available</p>
              <p className="text-sm text-neutral-500">
                Transaction data needed to show cash flow analysis
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Calculate summary metrics
  const totalIncome = data.reduce((sum, item) => sum + item.income, 0)
  const totalExpenses = data.reduce((sum, item) => sum + Math.abs(item.expenses), 0)
  const netCashFlow = totalIncome - totalExpenses
  const avgMonthlyIncome = totalIncome / data.length
  const avgMonthlyExpenses = totalExpenses / data.length
  const positiveMonths = data.filter(item => item.netFlow > 0).length

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Cash Flow Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80 mb-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
                tick={{ fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <ReferenceLine y={0} stroke="#374151" strokeWidth={1} />
              <Bar
                dataKey="income"
                fill="#10b981"
                name="Income"
                radius={[2, 2, 0, 0]}
              />
              <Bar
                dataKey="expenses"
                fill="#ef4444"
                name="Expenses"
                radius={[2, 2, 0, 0]}
              />
              <Bar
                dataKey="netFlow"
                fill={(entry: any) => entry.netFlow >= 0 ? "#3b82f6" : "#f59e0b"}
                name="Net Flow"
                radius={[2, 2, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Summary Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 pt-4 border-t">
          <div className="text-center">
            <p className="text-xs text-neutral-600">Total Income</p>
            <p className="text-lg font-bold text-success-600">
              {formatCurrency(totalIncome)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-neutral-600">Total Expenses</p>
            <p className="text-lg font-bold text-error-600">
              {formatCurrency(totalExpenses)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-neutral-600">Net Cash Flow</p>
            <p className={`text-lg font-bold ${
              netCashFlow >= 0 ? 'text-success-600' : 'text-error-600'
            }`}>
              {formatCurrency(netCashFlow)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-neutral-600">Monthly Avg Income</p>
            <p className="text-lg font-bold text-neutral-800">
              {formatCurrency(avgMonthlyIncome)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-neutral-600">Monthly Avg Expenses</p>
            <p className="text-lg font-bold text-neutral-800">
              {formatCurrency(avgMonthlyExpenses)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-neutral-600">Positive Months</p>
            <p className="text-lg font-bold text-primary-600">
              {positiveMonths}/{data.length}
            </p>
          </div>
        </div>

        {/* Health Indicator */}
        <div className="mt-4 p-3 rounded-lg bg-neutral-50">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-neutral-700">Cash Flow Health</span>
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                netCashFlow > 0 
                  ? 'bg-success-500' 
                  : netCashFlow === 0 
                  ? 'bg-warning-500' 
                  : 'bg-error-500'
              }`}></div>
              <span className="text-sm font-medium">
                {netCashFlow > 0 
                  ? 'Positive' 
                  : netCashFlow === 0 
                  ? 'Neutral' 
                  : 'Negative'}
              </span>
            </div>
          </div>
          <p className="text-xs text-neutral-600 mt-1">
            {positiveMonths > data.length / 2 
              ? `Strong performance with ${positiveMonths} positive months out of ${data.length}`
              : `Consider reviewing expenses - only ${positiveMonths} positive months out of ${data.length}`
            }
          </p>
        </div>
      </CardContent>
    </Card>
  )
}