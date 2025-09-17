import React from 'react'
import { 
  CalendarIcon, 
  DollarSignIcon, 
  FilterIcon, 
  XIcon,
  SearchIcon,
  BanknotesIcon
} from 'lucide-react'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { CustomSelect } from '../ui/select'
import { Badge } from '../ui/badge'
import { TransactionFilters as ITransactionFilters, Account, Category } from '@/lib/api'
import { cn } from '../../lib/utils'
import { format } from 'date-fns'

interface TransactionFiltersProps {
  filters: ITransactionFilters
  onFiltersChange: (filters: ITransactionFilters) => void
  accounts: Account[]
  categories: Category[]
  onReset: () => void
  className?: string
}

export function TransactionFilters({
  filters,
  onFiltersChange,
  accounts,
  categories,
  onReset,
  className
}: TransactionFiltersProps) {
  const [searchDebounce, setSearchDebounce] = React.useState<NodeJS.Timeout | null>(null)
  const [showAdvanced, setShowAdvanced] = React.useState(false)

  const handleSearchChange = (value: string) => {
    // Clear existing debounce
    if (searchDebounce) {
      clearTimeout(searchDebounce)
    }

    // Set new debounce
    const timeout = setTimeout(() => {
      onFiltersChange({ ...filters, search: value || undefined })
    }, 300)

    setSearchDebounce(timeout)
  }

  const handleFilterChange = (key: keyof ITransactionFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value || undefined })
  }

  const getActiveFiltersCount = () => {
    let count = 0
    if (filters.account_id) count++
    if (filters.category) count++
    if (filters.date_from) count++
    if (filters.date_to) count++
    if (filters.amount_min) count++
    if (filters.amount_max) count++
    if (filters.is_pending !== undefined) count++
    if (filters.search) count++
    return count
  }

  const accountOptions = accounts.map(account => ({
    value: account.id,
    label: `${account.name} (${account.subtype})`,
    icon: <BanknotesIcon className="h-4 w-4" />
  }))

  const categoryOptions = categories.map(category => ({
    value: category.name,
    label: category.name,
    icon: <span className="text-xs">{category.type}</span>
  }))

  const statusOptions = [
    { value: 'all', label: 'All Transactions' },
    { value: 'false', label: 'Completed Only' },
    { value: 'true', label: 'Pending Only' }
  ]

  React.useEffect(() => {
    return () => {
      if (searchDebounce) {
        clearTimeout(searchDebounce)
      }
    }
  }, [searchDebounce])

  return (
    <div className={cn('space-y-4', className)}>
      {/* Main Filters Row */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Search */}
        <div className="relative min-w-0 flex-1">
          <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
          <Input
            placeholder="Search transactions..."
            defaultValue={filters.search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Account Filter */}
        <div className="w-48">
          <CustomSelect
            options={[{ value: '', label: 'All Accounts' }, ...accountOptions]}
            value={filters.account_id || ''}
            onChange={(value) => handleFilterChange('account_id', value)}
            placeholder="Select account"
          />
        </div>

        {/* Category Filter */}
        <div className="w-48">
          <CustomSelect
            options={[{ value: '', label: 'All Categories' }, ...categoryOptions]}
            value={filters.category || ''}
            onChange={(value) => handleFilterChange('category', value)}
            placeholder="Select category"
          />
        </div>

        {/* Advanced Toggle */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className={cn(
            'flex items-center gap-2',
            showAdvanced && 'bg-primary-50 border-primary-200'
          )}
        >
          <FilterIcon className="h-4 w-4" />
          Advanced
          {getActiveFiltersCount() > 0 && (
            <Badge variant="secondary" className="ml-1">
              {getActiveFiltersCount()}
            </Badge>
          )}
        </Button>

        {/* Reset Filters */}
        {getActiveFiltersCount() > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            className="text-neutral-600 hover:text-neutral-900"
          >
            <XIcon className="h-4 w-4 mr-1" />
            Reset
          </Button>
        )}
      </div>

      {/* Advanced Filters */}
      {showAdvanced && (
        <div className="rounded-lg border bg-neutral-50 p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                From Date
              </label>
              <div className="relative">
                <CalendarIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
                <Input
                  type="date"
                  value={filters.date_from || ''}
                  onChange={(e) => handleFilterChange('date_from', e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                To Date
              </label>
              <div className="relative">
                <CalendarIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
                <Input
                  type="date"
                  value={filters.date_to || ''}
                  onChange={(e) => handleFilterChange('date_to', e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Amount Range */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Min Amount
              </label>
              <div className="relative">
                <DollarSignIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
                <Input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={filters.amount_min || ''}
                  onChange={(e) => handleFilterChange('amount_min', parseFloat(e.target.value) || undefined)}
                  className="pl-10"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Max Amount
              </label>
              <div className="relative">
                <DollarSignIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
                <Input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={filters.amount_max || ''}
                  onChange={(e) => handleFilterChange('amount_max', parseFloat(e.target.value) || undefined)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Status Filter */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Status
              </label>
              <CustomSelect
                options={statusOptions}
                value={filters.is_pending === undefined ? 'all' : filters.is_pending.toString()}
                onChange={(value) => {
                  if (value === 'all') {
                    handleFilterChange('is_pending', undefined)
                  } else {
                    handleFilterChange('is_pending', value === 'true')
                  }
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Active Filters Summary */}
      {getActiveFiltersCount() > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-neutral-700">Active filters:</span>
          
          {filters.account_id && (
            <Badge variant="outline" className="flex items-center gap-1">
              Account: {accounts.find(a => a.id === filters.account_id)?.name}
              <button
                onClick={() => handleFilterChange('account_id', undefined)}
                className="ml-1 hover:bg-neutral-200 rounded"
              >
                <XIcon className="h-3 w-3" />
              </button>
            </Badge>
          )}
          
          {filters.category && (
            <Badge variant="outline" className="flex items-center gap-1">
              Category: {filters.category}
              <button
                onClick={() => handleFilterChange('category', undefined)}
                className="ml-1 hover:bg-neutral-200 rounded"
              >
                <XIcon className="h-3 w-3" />
              </button>
            </Badge>
          )}
          
          {filters.date_from && (
            <Badge variant="outline" className="flex items-center gap-1">
              From: {format(new Date(filters.date_from), 'MMM d, yyyy')}
              <button
                onClick={() => handleFilterChange('date_from', undefined)}
                className="ml-1 hover:bg-neutral-200 rounded"
              >
                <XIcon className="h-3 w-3" />
              </button>
            </Badge>
          )}
          
          {filters.date_to && (
            <Badge variant="outline" className="flex items-center gap-1">
              To: {format(new Date(filters.date_to), 'MMM d, yyyy')}
              <button
                onClick={() => handleFilterChange('date_to', undefined)}
                className="ml-1 hover:bg-neutral-200 rounded"
              >
                <XIcon className="h-3 w-3" />
              </button>
            </Badge>
          )}
          
          {(filters.amount_min || filters.amount_max) && (
            <Badge variant="outline" className="flex items-center gap-1">
              Amount: {filters.amount_min ? `$${filters.amount_min}` : '$0'} - {filters.amount_max ? `$${filters.amount_max}` : '∞'}
              <button
                onClick={() => {
                  handleFilterChange('amount_min', undefined)
                  handleFilterChange('amount_max', undefined)
                }}
                className="ml-1 hover:bg-neutral-200 rounded"
              >
                <XIcon className="h-3 w-3" />
              </button>
            </Badge>
          )}
          
          {filters.is_pending !== undefined && (
            <Badge variant="outline" className="flex items-center gap-1">
              Status: {filters.is_pending ? 'Pending' : 'Completed'}
              <button
                onClick={() => handleFilterChange('is_pending', undefined)}
                className="ml-1 hover:bg-neutral-200 rounded"
              >
                <XIcon className="h-3 w-3" />
              </button>
            </Badge>
          )}
          
          {filters.search && (
            <Badge variant="outline" className="flex items-center gap-1">
              Search: "{filters.search}"
              <button
                onClick={() => handleFilterChange('search', undefined)}
                className="ml-1 hover:bg-neutral-200 rounded"
              >
                <XIcon className="h-3 w-3" />
              </button>
            </Badge>
          )}
        </div>
      )}
    </div>
  )
}