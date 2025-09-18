'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../ui/select'
import {
  Popover,
  PopoverContent,
  PopoverTrigger
} from '../ui/popover'
import { Calendar } from '../ui/calendar'
import { Badge } from '../ui/badge'
import {
  Filter,
  CalendarIcon,
  X,
  RefreshCw,
  ChevronDown,
  Search,
  DollarSign
} from 'lucide-react'
import { format, parseISO, startOfMonth, endOfMonth, subDays, subMonths } from 'date-fns'
import { cn } from '../../lib/utils'
import type { Account } from '../../lib/api/accounts'
import type { Category } from '../../lib/api/categories'

export interface TransactionFilters {
  account_id?: string
  category_id?: string
  date_from?: string
  date_to?: string
  amount_min?: number
  amount_max?: number
  search?: string
  is_pending?: boolean
  merchant_name?: string
  transaction_type?: 'income' | 'expense' | 'all'
}

interface AdvancedFiltersProps {
  filters: TransactionFilters
  onFiltersChange: (filters: TransactionFilters) => void
  accounts: Account[]
  categories: Category[]
  onReset?: () => void
  className?: string
}

const DATE_PRESETS = [
  { label: 'Today', getValue: () => ({ from: new Date(), to: new Date() }) },
  { label: 'Yesterday', getValue: () => ({ from: subDays(new Date(), 1), to: subDays(new Date(), 1) }) },
  { label: 'Last 7 days', getValue: () => ({ from: subDays(new Date(), 6), to: new Date() }) },
  { label: 'Last 30 days', getValue: () => ({ from: subDays(new Date(), 29), to: new Date() }) },
  { label: 'This month', getValue: () => ({ from: startOfMonth(new Date()), to: endOfMonth(new Date()) }) },
  { label: 'Last month', getValue: () => {
    const lastMonth = subMonths(new Date(), 1)
    return { from: startOfMonth(lastMonth), to: endOfMonth(lastMonth) }
  }},
  { label: 'Last 3 months', getValue: () => ({ from: subMonths(new Date(), 3), to: new Date() }) },
  { label: 'Last 6 months', getValue: () => ({ from: subMonths(new Date(), 6), to: new Date() }) },
  { label: 'This year', getValue: () => ({ from: new Date(new Date().getFullYear(), 0, 1), to: new Date() }) }
]

export function AdvancedFilters({
  filters,
  onFiltersChange,
  accounts,
  categories,
  onReset,
  className
}: AdvancedFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({})
  const [showDatePicker, setShowDatePicker] = useState(false)

  // Initialize date range from filters
  useEffect(() => {
    if (filters.date_from || filters.date_to) {
      setDateRange({
        from: filters.date_from ? parseISO(filters.date_from) : undefined,
        to: filters.date_to ? parseISO(filters.date_to) : undefined
      })
    }
  }, [filters.date_from, filters.date_to])

  const handleFilterChange = (key: keyof TransactionFilters, value: any) => {
    const newFilters = { ...filters }

    if (value === '' || value === undefined || value === 'all') {
      delete newFilters[key]
    } else {
      newFilters[key] = value
    }

    onFiltersChange(newFilters)
  }

  const handleDateRangeChange = (range: { from?: Date; to?: Date }) => {
    setDateRange(range)
    onFiltersChange({
      ...filters,
      date_from: range.from ? format(range.from, 'yyyy-MM-dd') : undefined,
      date_to: range.to ? format(range.to, 'yyyy-MM-dd') : undefined
    })
  }

  const handleDatePreset = (preset: typeof DATE_PRESETS[0]) => {
    const range = preset.getValue()
    handleDateRangeChange(range)
    setShowDatePicker(false)
  }

  const activeFiltersCount = Object.keys(filters).filter(
    key => filters[key as keyof TransactionFilters] !== undefined && key !== 'limit' && key !== 'offset'
  ).length

  const clearAllFilters = () => {
    setDateRange({})
    if (onReset) {
      onReset()
    } else {
      onFiltersChange({})
    }
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Quick Filters Row */}
      <div className="flex flex-wrap gap-2">
        {/* Date Range Picker */}
        <Popover open={showDatePicker} onOpenChange={setShowDatePicker}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className={cn(
                'w-[240px] justify-start text-left font-normal',
                !dateRange.from && 'text-muted-foreground'
              )}
            >
              <CalendarIcon className="mr-2 h-4 w-4" />
              {dateRange.from ? (
                dateRange.to ? (
                  <>
                    {format(dateRange.from, 'MMM d, yyyy')} - {format(dateRange.to, 'MMM d, yyyy')}
                  </>
                ) : (
                  format(dateRange.from, 'MMM d, yyyy')
                )
              ) : (
                'Select date range'
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <div className="flex">
              {/* Presets */}
              <div className="border-r p-3 space-y-1">
                <p className="text-sm font-medium text-muted-foreground mb-2">Quick Select</p>
                {DATE_PRESETS.map((preset) => (
                  <Button
                    key={preset.label}
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start text-left"
                    onClick={() => handleDatePreset(preset)}
                  >
                    {preset.label}
                  </Button>
                ))}
              </div>
              {/* Calendar */}
              <div className="p-3">
                <Calendar
                  mode="range"
                  selected={dateRange}
                  onSelect={handleDateRangeChange as any}
                  initialFocus
                  numberOfMonths={2}
                />
              </div>
            </div>
          </PopoverContent>
        </Popover>

        {/* Account Filter */}
        <Select
          value={filters.account_id || 'all'}
          onValueChange={(value) => handleFilterChange('account_id', value === 'all' ? undefined : value)}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All accounts" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All accounts</SelectItem>
            {accounts.map((account) => (
              <SelectItem key={account.id} value={account.id}>
                <div className="flex items-center">
                  <span>{account.name}</span>
                  {account.mask && (
                    <span className="ml-2 text-xs text-muted-foreground">•••• {account.mask}</span>
                  )}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Category Filter */}
        <Select
          value={filters.category_id || 'all'}
          onValueChange={(value) => handleFilterChange('category_id', value === 'all' ? undefined : value)}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All categories</SelectItem>
            {categories.map((category) => (
              <SelectItem key={category.id} value={category.id}>
                <div className="flex items-center">
                  {category.icon && <span className="mr-2">{category.icon}</span>}
                  <span>{category.name}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Transaction Type Filter */}
        <Select
          value={filters.transaction_type || 'all'}
          onValueChange={(value) => handleFilterChange('transaction_type', value)}
        >
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            <SelectItem value="income">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-green-500 mr-2" />
                Income
              </div>
            </SelectItem>
            <SelectItem value="expense">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-red-500 mr-2" />
                Expense
              </div>
            </SelectItem>
          </SelectContent>
        </Select>

        {/* Search Input */}
        <div className="relative flex-1 min-w-[200px] max-w-[400px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by description or merchant..."
            value={filters.search || ''}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Expand/Collapse Advanced Filters */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <Filter className="mr-2 h-4 w-4" />
          Advanced
          <ChevronDown className={cn('ml-2 h-4 w-4 transition-transform', isExpanded && 'rotate-180')} />
        </Button>

        {/* Clear Filters */}
        {activeFiltersCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAllFilters}
          >
            <X className="mr-2 h-4 w-4" />
            Clear ({activeFiltersCount})
          </Button>
        )}
      </div>

      {/* Advanced Filters Section */}
      {isExpanded && (
        <div className="border rounded-lg p-4 space-y-4 bg-muted/30">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Amount Range */}
            <div className="space-y-2">
              <Label>Amount Range</Label>
              <div className="flex items-center space-x-2">
                <div className="relative flex-1">
                  <DollarSign className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    type="number"
                    placeholder="Min"
                    value={filters.amount_min || ''}
                    onChange={(e) => handleFilterChange('amount_min', e.target.value ? parseFloat(e.target.value) : undefined)}
                    className="pl-9"
                  />
                </div>
                <span className="text-muted-foreground">to</span>
                <div className="relative flex-1">
                  <DollarSign className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    type="number"
                    placeholder="Max"
                    value={filters.amount_max || ''}
                    onChange={(e) => handleFilterChange('amount_max', e.target.value ? parseFloat(e.target.value) : undefined)}
                    className="pl-9"
                  />
                </div>
              </div>
            </div>

            {/* Merchant Name */}
            <div className="space-y-2">
              <Label>Merchant Name</Label>
              <Input
                placeholder="Enter merchant name..."
                value={filters.merchant_name || ''}
                onChange={(e) => handleFilterChange('merchant_name', e.target.value)}
              />
            </div>

            {/* Pending Status */}
            <div className="space-y-2">
              <Label>Transaction Status</Label>
              <Select
                value={filters.is_pending === undefined ? 'all' : filters.is_pending.toString()}
                onValueChange={(value) => handleFilterChange('is_pending', value === 'all' ? undefined : value === 'true')}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  <SelectItem value="false">Posted</SelectItem>
                  <SelectItem value="true">Pending</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Active Filters Display */}
          {activeFiltersCount > 0 && (
            <div className="flex flex-wrap gap-2 pt-2 border-t">
              <span className="text-sm text-muted-foreground">Active filters:</span>
              {filters.date_from && filters.date_to && (
                <Badge variant="secondary">
                  {format(parseISO(filters.date_from), 'MMM d')} - {format(parseISO(filters.date_to), 'MMM d')}
                </Badge>
              )}
              {filters.account_id && (
                <Badge variant="secondary">
                  Account: {accounts.find(a => a.id === filters.account_id)?.name}
                </Badge>
              )}
              {filters.category_id && (
                <Badge variant="secondary">
                  Category: {categories.find(c => c.id === filters.category_id)?.name}
                </Badge>
              )}
              {filters.transaction_type && filters.transaction_type !== 'all' && (
                <Badge variant="secondary">
                  Type: {filters.transaction_type}
                </Badge>
              )}
              {filters.amount_min !== undefined && (
                <Badge variant="secondary">
                  Min: ${filters.amount_min}
                </Badge>
              )}
              {filters.amount_max !== undefined && (
                <Badge variant="secondary">
                  Max: ${filters.amount_max}
                </Badge>
              )}
              {filters.merchant_name && (
                <Badge variant="secondary">
                  Merchant: {filters.merchant_name}
                </Badge>
              )}
              {filters.is_pending !== undefined && (
                <Badge variant="secondary">
                  Status: {filters.is_pending ? 'Pending' : 'Posted'}
                </Badge>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}