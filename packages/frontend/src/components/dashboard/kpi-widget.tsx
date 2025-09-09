'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatPercentage, formatNumber } from '@/lib/utils'
import { 
  TrendingUp, 
  TrendingDown, 
  ArrowUp, 
  ArrowDown,
  Minus,
  LucideIcon
} from 'lucide-react'

interface KPIWidgetProps {
  title: string
  value: number
  change?: {
    value: number
    type: 'percentage' | 'currency' | 'number'
    period?: string
    isPositive?: boolean
  }
  format: 'currency' | 'percentage' | 'number'
  icon?: LucideIcon
  description?: string
  target?: number
  isLoading?: boolean
  className?: string
  size?: 'sm' | 'md' | 'lg'
  color?: 'default' | 'success' | 'warning' | 'error' | 'info'
}

const LoadingSkeleton = ({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) => {
  const heights = {
    sm: 'h-24',
    md: 'h-32',
    lg: 'h-40'
  }

  return (
    <div className={`animate-pulse p-4 ${heights[size]}`}>
      <div className="flex justify-between items-start mb-2">
        <div className="h-4 bg-neutral-200 rounded w-24"></div>
        <div className="h-5 w-5 bg-neutral-200 rounded"></div>
      </div>
      <div className="h-8 bg-neutral-200 rounded w-32 mb-2"></div>
      <div className="flex items-center space-x-2">
        <div className="h-3 bg-neutral-200 rounded w-16"></div>
        <div className="h-3 bg-neutral-200 rounded w-20"></div>
      </div>
    </div>
  )
}

export function KPIWidget({
  title,
  value,
  change,
  format,
  icon: Icon,
  description,
  target,
  isLoading = false,
  className = '',
  size = 'md',
  color = 'default'
}: KPIWidgetProps) {
  const formatValue = (val: number, fmt: string) => {
    switch (fmt) {
      case 'currency':
        return formatCurrency(val)
      case 'percentage':
        return formatPercentage(val)
      case 'number':
        return formatNumber(val)
      default:
        return val.toString()
    }
  }

  const getChangeIcon = () => {
    if (!change) return null
    
    const isPositive = change.isPositive !== undefined 
      ? change.isPositive 
      : change.value > 0

    if (change.value === 0) return <Minus className="h-3 w-3" />
    return isPositive 
      ? <ArrowUp className="h-3 w-3" />
      : <ArrowDown className="h-3 w-3" />
  }

  const getChangeColor = () => {
    if (!change) return 'text-neutral-600'
    
    const isPositive = change.isPositive !== undefined 
      ? change.isPositive 
      : change.value > 0

    if (change.value === 0) return 'text-neutral-600'
    return isPositive ? 'text-success-600' : 'text-error-600'
  }

  const getColorClasses = () => {
    const colors = {
      default: 'text-neutral-900 border-neutral-200',
      success: 'text-success-900 border-success-200 bg-success-50',
      warning: 'text-warning-900 border-warning-200 bg-warning-50',
      error: 'text-error-900 border-error-200 bg-error-50',
      info: 'text-info-900 border-info-200 bg-info-50'
    }
    return colors[color] || colors.default
  }

  const sizeClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-3xl'
  }

  const getTargetProgress = () => {
    if (!target || target === 0) return null
    
    const progress = (value / target) * 100
    const isOnTrack = progress >= 80
    
    return {
      percentage: Math.min(progress, 100),
      isOnTrack,
      remaining: target - value
    }
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardContent className="p-0">
          <LoadingSkeleton size={size} />
        </CardContent>
      </Card>
    )
  }

  const targetProgress = getTargetProgress()

  return (
    <Card className={`${className} ${getColorClasses()}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          {title}
        </CardTitle>
        {Icon && <Icon className="h-4 w-4 text-neutral-600" />}
      </CardHeader>
      <CardContent>
        <div className={`${sizeClasses[size]} font-bold mb-1`}>
          {formatValue(value, format)}
        </div>
        
        {/* Change indicator */}
        {change && (
          <div className={`flex items-center text-xs ${getChangeColor()} mb-2`}>
            {getChangeIcon()}
            <span className="ml-1">
              {formatValue(Math.abs(change.value), change.type)} 
              {change.period && ` ${change.period}`}
            </span>
          </div>
        )}

        {/* Description */}
        {description && (
          <p className="text-xs text-neutral-600 mb-2">
            {description}
          </p>
        )}

        {/* Target progress */}
        {targetProgress && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span className="text-neutral-600">Target Progress</span>
              <span className={targetProgress.isOnTrack ? 'text-success-600' : 'text-warning-600'}>
                {targetProgress.percentage.toFixed(0)}%
              </span>
            </div>
            <div className="w-full bg-neutral-200 rounded-full h-1.5">
              <div
                className={`h-1.5 rounded-full transition-all ${
                  targetProgress.isOnTrack ? 'bg-success-500' : 'bg-warning-500'
                }`}
                style={{ width: `${targetProgress.percentage}%` }}
              ></div>
            </div>
            {targetProgress.remaining > 0 && (
              <p className="text-xs text-neutral-600">
                {formatValue(targetProgress.remaining, format)} remaining to reach target
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}