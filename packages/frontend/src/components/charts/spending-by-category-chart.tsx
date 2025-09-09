'use client'

import React from 'react'
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Tooltip, 
  Legend 
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency } from '@/lib/utils'

interface CategoryData {
  name: string
  value: number
  color: string
  percentage?: number
}

interface SpendingByCategoryChartProps {
  data: CategoryData[]
  isLoading?: boolean
  className?: string
}

const COLORS = [
  '#0088FE', // Primary blue
  '#00C49F', // Teal
  '#FFBB28', // Yellow
  '#FF8042', // Orange
  '#8884D8', // Purple
  '#82CA9D', // Light green
  '#FFC658', // Gold
  '#FF7300', // Dark orange
  '#A4DE6C', // Lime
  '#8DD1E1'  // Light blue
]

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-white border border-neutral-200 rounded-lg shadow-lg p-3">
        <p className="font-medium text-neutral-900">{data.name}</p>
        <p className="text-sm text-neutral-600">
          Amount: <span className="font-medium">{formatCurrency(data.value)}</span>
        </p>
        {data.percentage && (
          <p className="text-sm text-neutral-600">
            Percentage: <span className="font-medium">{data.percentage.toFixed(1)}%</span>
          </p>
        )}
      </div>
    )
  }
  return null
}

const LoadingSkeleton = () => (
  <div className="h-80 flex items-center justify-center">
    <div className="animate-pulse">
      <div className="w-48 h-48 bg-neutral-200 rounded-full mx-auto mb-4"></div>
      <div className="space-y-2">
        <div className="h-4 bg-neutral-200 rounded w-32 mx-auto"></div>
        <div className="h-3 bg-neutral-200 rounded w-24 mx-auto"></div>
      </div>
    </div>
  </div>
)

export function SpendingByCategoryChart({ 
  data, 
  isLoading = false, 
  className = '' 
}: SpendingByCategoryChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0)
  const dataWithPercentages = data.map((item, index) => ({
    ...item,
    percentage: total > 0 ? (item.value / total) * 100 : 0,
    color: item.color || COLORS[index % COLORS.length]
  }))

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>Spending by Category</CardTitle>
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
          <CardTitle>Spending by Category</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center">
            <div className="text-center">
              <p className="text-neutral-600 mb-2">No spending data available</p>
              <p className="text-sm text-neutral-500">
                Connect accounts to see your spending breakdown
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Spending by Category</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={dataWithPercentages}
                cx="50%"
                cy="50%"
                outerRadius={100}
                innerRadius={40}
                paddingAngle={2}
                dataKey="value"
                label={({percentage}) => `${percentage.toFixed(1)}%`}
                labelLine={false}
              >
                {dataWithPercentages.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.color}
                    className="hover:opacity-80 transition-opacity"
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ paddingTop: '20px' }}
                formatter={(value, entry: any) => (
                  <span className="text-sm">
                    {value} - {formatCurrency(entry.payload.value)}
                  </span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        
        {/* Summary */}
        <div className="mt-4 pt-4 border-t">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-neutral-700">
              Total Spending
            </span>
            <span className="text-lg font-bold text-neutral-900">
              {formatCurrency(total)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}