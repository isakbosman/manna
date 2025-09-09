'use client'

import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency } from '@/lib/utils'
import { format, parseISO } from 'date-fns'

interface TrendData {
  date: string
  income: number
  expenses: number
  netFlow: number
}

interface TransactionTrendsChartProps {
  data: TrendData[]
  isLoading?: boolean
  className?: string
  chartType?: 'line' | 'area'
  dateRange?: string
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const date = parseISO(label)
    return (
      <div className="bg-white border border-neutral-200 rounded-lg shadow-lg p-3">
        <p className="font-medium text-neutral-900 mb-2">
          {format(date, 'MMM dd, yyyy')}
        </p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: <span className="font-medium">
              {formatCurrency(entry.value)}
            </span>
          </p>
        ))}
      </div>
    )
  }
  return null
}

const LoadingSkeleton = () => (
  <div className="h-80 flex items-center justify-center">
    <div className="animate-pulse w-full">
      <div className="flex justify-between mb-4">
        {[...Array(7)].map((_, i) => (
          <div key={i} className="w-8 h-4 bg-neutral-200 rounded"></div>
        ))}
      </div>
      <div className="space-y-2">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="flex justify-between">
            <div className="w-full h-6 bg-neutral-200 rounded"></div>
          </div>
        ))}
      </div>
    </div>
  </div>
)

export function TransactionTrendsChart({
  data,
  isLoading = false,
  className = '',
  chartType = 'line',
  dateRange = 'Last 30 days'
}: TransactionTrendsChartProps) {
  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Transaction Trends</CardTitle>
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
          <CardTitle>Transaction Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center">
            <div className="text-center">
              <p className="text-neutral-600 mb-2">No transaction data available</p>
              <p className="text-sm text-neutral-500">
                Connect accounts to see your transaction trends
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const formatXAxisLabel = (tickItem: string) => {
    try {
      const date = parseISO(tickItem)
      return format(date, 'MMM dd')
    } catch {
      return tickItem
    }
  }

  const chartContent = chartType === 'area' ? (
    <AreaChart data={data}>
      <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
      <XAxis
        dataKey="date"
        tickFormatter={formatXAxisLabel}
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
      <Area
        type="monotone"
        dataKey="income"
        stackId="1"
        stroke="#10b981"
        fill="#10b981"
        fillOpacity={0.3}
        name="Income"
        strokeWidth={2}
      />
      <Area
        type="monotone"
        dataKey="expenses"
        stackId="2"
        stroke="#ef4444"
        fill="#ef4444"
        fillOpacity={0.3}
        name="Expenses"
        strokeWidth={2}
      />
    </AreaChart>
  ) : (
    <LineChart data={data}>
      <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
      <XAxis
        dataKey="date"
        tickFormatter={formatXAxisLabel}
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
      <Line
        type="monotone"
        dataKey="income"
        stroke="#10b981"
        strokeWidth={3}
        dot={{ r: 4, fill: '#10b981' }}
        activeDot={{ r: 6, fill: '#10b981' }}
        name="Income"
      />
      <Line
        type="monotone"
        dataKey="expenses"
        stroke="#ef4444"
        strokeWidth={3}
        dot={{ r: 4, fill: '#ef4444' }}
        activeDot={{ r: 6, fill: '#ef4444' }}
        name="Expenses"
      />
      <Line
        type="monotone"
        dataKey="netFlow"
        stroke="#3b82f6"
        strokeWidth={2}
        dot={{ r: 3, fill: '#3b82f6' }}
        activeDot={{ r: 5, fill: '#3b82f6' }}
        name="Net Flow"
        strokeDasharray="5 5"
      />
    </LineChart>
  )

  // Calculate summary statistics
  const totalIncome = data.reduce((sum, item) => sum + item.income, 0)
  const totalExpenses = data.reduce((sum, item) => sum + Math.abs(item.expenses), 0)
  const netFlow = totalIncome - totalExpenses
  const avgDailySpending = totalExpenses / data.length

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Transaction Trends</CardTitle>
          <span className="text-sm text-neutral-600">{dateRange}</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-80 mb-4">
          <ResponsiveContainer width="100%" height="100%">
            {chartContent}
          </ResponsiveContainer>
        </div>

        {/* Summary Statistics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
          <div className="text-center">
            <p className="text-sm text-neutral-600">Total Income</p>
            <p className="text-lg font-bold text-success-600">
              {formatCurrency(totalIncome)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-neutral-600">Total Expenses</p>
            <p className="text-lg font-bold text-error-600">
              {formatCurrency(totalExpenses)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-neutral-600">Net Flow</p>
            <p className={`text-lg font-bold ${
              netFlow >= 0 ? 'text-success-600' : 'text-error-600'
            }`}>
              {formatCurrency(netFlow)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-neutral-600">Daily Avg</p>
            <p className="text-lg font-bold text-neutral-800">
              {formatCurrency(avgDailySpending)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}