import React from 'react'
import {
  TagIcon,
  SearchIcon,
  CheckIcon,
  XIcon,
  BrainIcon,
  PlusIcon,
  ArrowRightIcon,
  DollarSignIcon,
  CalendarIcon,
  BuildingIcon,
  Store,
  HashIcon,
  SparklesIcon,
  AlertCircleIcon,
  CheckCircleIcon
} from 'lucide-react'
import { Modal } from '../ui/modal'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Badge } from '../ui/badge'
import { ScrollArea } from '../ui/scroll-area'
import { Transaction } from '../../lib/api/transactions'
import { Category, categoriesApi, MLCategoryPrediction } from '../../lib/api/categories'
import { transactionsApi } from '../../lib/api/transactions'
import { cn } from '../../lib/utils'
import { format } from 'date-fns'

interface CategorizationModalProps {
  isOpen: boolean
  onClose: () => void
  transactions: Transaction[]
  onTransactionsUpdated: (transactions: Transaction[]) => void
  className?: string
}

interface CategoryWithIcon extends Category {
  icon_element?: React.ReactNode
}

// Enhanced category icons mapping
const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  // Income
  salary: <DollarSignIcon className="h-4 w-4" />,
  freelance: <DollarSignIcon className="h-4 w-4" />,
  investment: <DollarSignIcon className="h-4 w-4" />,
  business: <BuildingIcon className="h-4 w-4" />,
  other_income: <DollarSignIcon className="h-4 w-4" />,

  // Common expense categories
  groceries: <Store className="h-4 w-4" />,
  restaurants: <Store className="h-4 w-4" />,
  gas: <Store className="h-4 w-4" />,
  utilities: <BuildingIcon className="h-4 w-4" />,
  rent: <BuildingIcon className="h-4 w-4" />,
  mortgage: <BuildingIcon className="h-4 w-4" />,

  // Default
  default: <TagIcon className="h-4 w-4" />,
}

export function CategorizationModal({
  isOpen,
  onClose,
  transactions,
  onTransactionsUpdated,
  className
}: CategorizationModalProps) {
  const [categories, setCategories] = React.useState<CategoryWithIcon[]>([])
  const [filteredCategories, setFilteredCategories] = React.useState<CategoryWithIcon[]>([])
  const [searchTerm, setSearchTerm] = React.useState('')
  const [selectedCategory, setSelectedCategory] = React.useState<string>('')
  const [mlPredictions, setMlPredictions] = React.useState<Record<string, MLCategoryPrediction[]>>({})
  const [isLoading, setIsLoading] = React.useState(false)
  const [isSaving, setIsSaving] = React.useState(false)
  const [showCreateCategory, setShowCreateCategory] = React.useState(false)
  const [newCategoryName, setNewCategoryName] = React.useState('')
  const [newCategoryType, setNewCategoryType] = React.useState<'income' | 'expense' | 'transfer'>('expense')
  const [successMessage, setSuccessMessage] = React.useState<string>('')
  const [errorMessage, setErrorMessage] = React.useState<string>('')
  const [selectedTransactionIndex, setSelectedTransactionIndex] = React.useState(0)

  // Focus management for keyboard navigation
  const searchInputRef = React.useRef<HTMLInputElement>(null)
  const categoryRefs = React.useRef<(HTMLButtonElement | null)[]>([])

  React.useEffect(() => {
    if (isOpen) {
      loadCategories()
      loadMLPredictions()
      setSearchTerm('')
      setSelectedCategory('')
      setSuccessMessage('')
      setErrorMessage('')
      setSelectedTransactionIndex(0)

      // Focus search input when modal opens
      setTimeout(() => {
        searchInputRef.current?.focus()
      }, 100)
    }
  }, [isOpen, transactions])

  React.useEffect(() => {
    // Filter categories based on search term
    const filtered = categories.filter(category =>
      category.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      category.type.toLowerCase().includes(searchTerm.toLowerCase())
    )

    // Sort by ML predictions for current transaction if available
    const currentTransaction = transactions[selectedTransactionIndex]
    if (currentTransaction && mlPredictions[currentTransaction.id]) {
      const predictionCategoryIds = new Set(
        mlPredictions[currentTransaction.id].map(p => p.category_id)
      )

      filtered.sort((a, b) => {
        const aHasPrediction = predictionCategoryIds.has(a.id)
        const bHasPrediction = predictionCategoryIds.has(b.id)

        if (aHasPrediction && !bHasPrediction) return -1
        if (!aHasPrediction && bHasPrediction) return 1

        return a.name.localeCompare(b.name)
      })
    } else {
      filtered.sort((a, b) => a.name.localeCompare(b.name))
    }

    setFilteredCategories(filtered)
  }, [categories, searchTerm, mlPredictions, selectedTransactionIndex, transactions])

  // Keyboard navigation
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      switch (e.key) {
        case 'Escape':
          if (showCreateCategory) {
            setShowCreateCategory(false)
          } else {
            onClose()
          }
          break
        case 'ArrowDown':
          e.preventDefault()
          if (searchInputRef.current === document.activeElement) {
            categoryRefs.current[0]?.focus()
          } else {
            const currentIndex = categoryRefs.current.findIndex(ref => ref === document.activeElement)
            const nextIndex = Math.min(currentIndex + 1, filteredCategories.length - 1)
            categoryRefs.current[nextIndex]?.focus()
          }
          break
        case 'ArrowUp':
          e.preventDefault()
          const currentIndex = categoryRefs.current.findIndex(ref => ref === document.activeElement)
          if (currentIndex <= 0) {
            searchInputRef.current?.focus()
          } else {
            categoryRefs.current[currentIndex - 1]?.focus()
          }
          break
        case 'Enter':
          e.preventDefault()
          const focusedIndex = categoryRefs.current.findIndex(ref => ref === document.activeElement)
          if (focusedIndex >= 0) {
            const category = filteredCategories[focusedIndex]
            handleCategorySelect(category.id)
          }
          break
        case 'ArrowLeft':
          if (selectedTransactionIndex > 0) {
            setSelectedTransactionIndex(prev => prev - 1)
            setSelectedCategory('')
          }
          break
        case 'ArrowRight':
          if (selectedTransactionIndex < transactions.length - 1) {
            setSelectedTransactionIndex(prev => prev + 1)
            setSelectedCategory('')
          }
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, filteredCategories, selectedTransactionIndex, transactions.length, showCreateCategory, onClose])

  const loadCategories = async () => {
    try {
      setIsLoading(true)
      const data = await categoriesApi.getCategories()

      // Add icon elements to categories
      const categoriesWithIcons = data.map(category => ({
        ...category,
        icon_element: getCategoryIcon(category)
      }))

      setCategories(categoriesWithIcons)
    } catch (error) {
      console.error('Failed to load categories:', error)
      setErrorMessage('Failed to load categories')
    } finally {
      setIsLoading(false)
    }
  }

  const loadMLPredictions = async () => {
    if (transactions.length === 0) return

    try {
      const transactionIds = transactions.map(t => t.id)
      const result = await categoriesApi.bulkCategorize(transactionIds)
      setMlPredictions(result.predictions)
    } catch (error) {
      console.error('Failed to load ML predictions:', error)
    }
  }

  const getCategoryIcon = (category: Category) => {
    const iconKey = category.icon || category.name.toLowerCase().replace(/\s+/g, '_')
    return CATEGORY_ICONS[iconKey] || CATEGORY_ICONS.default
  }

  const getCategoryColor = (category: Category) => {
    switch (category.type) {
      case 'income': return 'success'
      case 'expense': return 'destructive'
      case 'transfer': return 'secondary'
      default: return 'outline'
    }
  }

  const getMLConfidence = (categoryId: string, transactionId: string) => {
    const predictions = mlPredictions[transactionId]
    if (!predictions) return 0
    const prediction = predictions.find(p => p.category_id === categoryId)
    return prediction?.confidence || 0
  }

  const handleCategorySelect = (categoryId: string) => {
    setSelectedCategory(categoryId)
  }

  const handleCreateCategory = async () => {
    if (!newCategoryName.trim()) return

    try {
      setIsLoading(true)
      const category = await categoriesApi.createCategory({
        name: newCategoryName.trim(),
        type: newCategoryType,
        is_system: false
      })

      const categoryWithIcon = {
        ...category,
        icon_element: getCategoryIcon(category)
      }

      setCategories(prev => [...prev, categoryWithIcon])
      setSelectedCategory(category.id)
      setShowCreateCategory(false)
      setNewCategoryName('')
      setSuccessMessage(`Created category "${category.name}"`)
    } catch (error) {
      console.error('Failed to create category:', error)
      setErrorMessage('Failed to create category')
    } finally {
      setIsLoading(false)
    }
  }

  const handleApplyCategorization = async () => {
    if (!selectedCategory) return

    try {
      setIsSaving(true)
      setErrorMessage('')
      setSuccessMessage('')

      if (transactions.length === 1) {
        // Single transaction
        const updatedTransaction = await transactionsApi.updateTransaction(
          transactions[0].id,
          { category_id: selectedCategory }
        )
        onTransactionsUpdated([updatedTransaction])
        setSuccessMessage('Transaction categorized successfully')
      } else {
        // Bulk update with progress tracking
        let completed = 0
        const errors: string[] = []
        const batchSize = 10 // Process in batches for better UX

        // Split transactions into batches
        const batches = []
        for (let i = 0; i < transactions.length; i += batchSize) {
          batches.push(transactions.slice(i, i + batchSize))
        }

        const updatedTransactions: Transaction[] = []

        for (const batch of batches) {
          try {
            const result = await transactionsApi.bulkUpdateTransactions({
              transaction_ids: batch.map(t => t.id),
              updates: { category_id: selectedCategory }
            })
            updatedTransactions.push(...result)
            completed += batch.length
          } catch (error: any) {
            errors.push(`Failed to update ${batch.length} transactions: ${error.message}`)
          }
        }

        onTransactionsUpdated(updatedTransactions)

        if (errors.length === 0) {
          setSuccessMessage(`${completed} transactions categorized successfully`)
        } else {
          setSuccessMessage(`${completed} transactions categorized successfully`)
          if (errors.length > 0) {
            setErrorMessage(`${errors.length} batches failed. Some transactions may not have been updated.`)
          }
        }
      }

      // Auto-close after success if no errors
      if (transactions.length === 1) {
        setTimeout(() => {
          onClose()
        }, 1500)
      }
    } catch (error: any) {
      console.error('Failed to categorize transactions:', error)
      setErrorMessage(error.message || 'Failed to categorize transactions')
    } finally {
      setIsSaving(false)
    }
  }

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(Math.abs(amount))
  }

  const currentTransaction = transactions[selectedTransactionIndex]
  const currentPredictions = currentTransaction ? mlPredictions[currentTransaction.id] || [] : []
  const selectedCategoryData = categories.find(c => c.id === selectedCategory)

  if (!isOpen) return null

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={transactions.length === 1 ? 'Categorize Transaction' : `Categorize ${transactions.length} Transactions`}
      description={transactions.length === 1 ? 'Select a category for this transaction' : 'Select a category to apply to all selected transactions'}
      size="xl"
      className={className}
    >
      <div className="space-y-6">
        {/* Error/Success Messages */}
        {errorMessage && (
          <div className="flex items-center gap-2 p-3 bg-error-50 border border-error-200 rounded-lg text-error-700">
            <AlertCircleIcon className="h-5 w-5" />
            <span>{errorMessage}</span>
            <button
              onClick={() => setErrorMessage('')}
              className="ml-auto p-1 hover:bg-error-100 rounded"
            >
              <XIcon className="h-4 w-4" />
            </button>
          </div>
        )}

        {successMessage && (
          <div className="flex items-center gap-2 p-3 bg-success-50 border border-success-200 rounded-lg text-success-700">
            <CheckCircleIcon className="h-5 w-5" />
            <span>{successMessage}</span>
            <button
              onClick={() => setSuccessMessage('')}
              className="ml-auto p-1 hover:bg-success-100 rounded"
            >
              <XIcon className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Transaction Preview */}
        <div className="space-y-4">
          {transactions.length === 1 ? (
            <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-neutral-900">
                    {currentTransaction.description}
                  </h3>
                  <div className="flex items-center gap-3 mt-2 text-sm text-neutral-600">
                    <div className="flex items-center gap-1">
                      <CalendarIcon className="h-4 w-4" />
                      {format(new Date(currentTransaction.date), 'MMM d, yyyy')}
                    </div>
                    {currentTransaction.merchant_name && (
                      <div className="flex items-center gap-1">
                        <BuildingIcon className="h-4 w-4" />
                        {currentTransaction.merchant_name}
                      </div>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className={cn(
                    'text-lg font-bold',
                    currentTransaction.amount < 0 ? 'text-error-600' : 'text-success-600'
                  )}>
                    {currentTransaction.amount < 0 ? '-' : '+'}{formatAmount(currentTransaction.amount)}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold text-neutral-900">
                    {transactions.length} Selected Transactions
                  </h3>
                  <div className="text-sm text-neutral-600">
                    Total: {formatAmount(transactions.reduce((sum, t) => sum + t.amount, 0))}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedTransactionIndex(prev => Math.max(0, prev - 1))}
                    disabled={selectedTransactionIndex === 0}
                  >
                    Previous
                  </Button>
                  <span className="flex items-center px-3 py-1 bg-white border rounded text-sm">
                    {selectedTransactionIndex + 1} of {transactions.length}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedTransactionIndex(prev => Math.min(transactions.length - 1, prev + 1))}
                    disabled={selectedTransactionIndex === transactions.length - 1}
                  >
                    Next
                  </Button>
                </div>
              </div>

              {/* Current transaction preview */}
              <div className="flex items-start justify-between bg-white border rounded-lg p-3">
                <div className="flex-1">
                  <h4 className="font-medium text-neutral-900">
                    {currentTransaction.description}
                  </h4>
                  <div className="flex items-center gap-3 mt-1 text-sm text-neutral-600">
                    <div className="flex items-center gap-1">
                      <CalendarIcon className="h-4 w-4" />
                      {format(new Date(currentTransaction.date), 'MMM d, yyyy')}
                    </div>
                    {currentTransaction.merchant_name && (
                      <div className="flex items-center gap-1">
                        <BuildingIcon className="h-4 w-4" />
                        {currentTransaction.merchant_name}
                      </div>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className={cn(
                    'font-bold',
                    currentTransaction.amount < 0 ? 'text-error-600' : 'text-success-600'
                  )}>
                    {currentTransaction.amount < 0 ? '-' : '+'}{formatAmount(currentTransaction.amount)}
                  </p>
                </div>
              </div>

              {/* Bulk operation summary */}
              {transactions.length > 1 && (
                <div className="mt-3 p-3 bg-info-50 border border-info-200 rounded-lg">
                  <div className="flex items-center gap-2 text-sm text-info-700">
                    <SparklesIcon className="h-4 w-4" />
                    <span className="font-medium">Bulk Operation:</span>
                    The selected category will be applied to all {transactions.length} transactions.
                  </div>
                  <div className="mt-2 text-xs text-info-600">
                    {transactions.filter(t => !t.category_id).length} uncategorized transactions will be updated.
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ML Predictions */}
        {currentPredictions.length > 0 && (
          <div className="bg-info-50 border border-info-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <BrainIcon className="h-5 w-5 text-info-600" />
              <h4 className="font-medium text-info-900">AI Suggestions</h4>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {currentPredictions.slice(0, 4).map((prediction, index) => {
                const category = categories.find(c => c.id === prediction.category_id)
                if (!category) return null

                return (
                  <button
                    key={prediction.category_id}
                    onClick={() => handleCategorySelect(prediction.category_id)}
                    className={cn(
                      'flex items-center gap-2 p-3 rounded-lg border text-left transition-colors hover:bg-info-100',
                      selectedCategory === prediction.category_id ? 'border-info-500 bg-info-100' : 'border-info-200 bg-white'
                    )}
                  >
                    {category.icon_element}
                    <div className="flex-1">
                      <p className="font-medium">{category.name}</p>
                      <Badge variant="info" className="text-xs">
                        {Math.round(prediction.confidence * 100)}% confidence
                      </Badge>
                    </div>
                    {selectedCategory === prediction.category_id && (
                      <CheckIcon className="h-4 w-4 text-info-600" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Category Search */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
              <Input
                ref={searchInputRef}
                placeholder="Search categories..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCreateCategory(true)}
            >
              <PlusIcon className="h-4 w-4 mr-1" />
              New
            </Button>
          </div>

          {/* Create New Category Inline */}
          {showCreateCategory && (
            <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-4 space-y-3">
              <h4 className="font-medium text-neutral-900">Create New Category</h4>
              <div className="flex gap-2">
                <Input
                  placeholder="Category name"
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleCreateCategory()
                    }
                  }}
                  className="flex-1"
                />
                <select
                  value={newCategoryType}
                  onChange={(e) => setNewCategoryType(e.target.value as any)}
                  className="px-3 py-2 border border-neutral-300 rounded-md text-sm"
                >
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                  <option value="transfer">Transfer</option>
                </select>
                <Button
                  onClick={handleCreateCategory}
                  disabled={!newCategoryName.trim() || isLoading}
                  loading={isLoading}
                >
                  Create
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowCreateCategory(false)
                    setNewCategoryName('')
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Category List */}
        <div className="space-y-2">
          <h4 className="font-medium text-neutral-900">
            Categories ({filteredCategories.length})
          </h4>
          <ScrollArea className="max-h-80">
            <div className="space-y-1 pr-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="h-6 w-6 animate-spin rounded-full border-b-2 border-primary-600" />
                </div>
              ) : filteredCategories.length === 0 ? (
                <div className="text-center py-8 text-neutral-500">
                  {searchTerm ? 'No categories found' : 'No categories available'}
                </div>
              ) : (
                filteredCategories.map((category, index) => {
                  const confidence = getMLConfidence(category.id, currentTransaction?.id || '')
                  const isSelected = selectedCategory === category.id

                  return (
                    <button
                      key={category.id}
                      ref={(el) => { categoryRefs.current[index] = el }}
                      onClick={() => handleCategorySelect(category.id)}
                      className={cn(
                        'w-full flex items-center gap-3 p-3 rounded-lg border text-left transition-colors hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-primary-500',
                        isSelected ? 'border-primary-500 bg-primary-50' : 'border-neutral-200',
                        confidence > 0.7 && 'ring-2 ring-info-200'
                      )}
                    >
                      <div className="flex-shrink-0">
                        {category.icon_element}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-neutral-900 truncate">
                          {category.name}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant={getCategoryColor(category)} className="text-xs">
                            {category.type}
                          </Badge>
                          {confidence > 0 && (
                            <Badge variant="info" className="text-xs">
                              {Math.round(confidence * 100)}% match
                            </Badge>
                          )}
                        </div>
                      </div>
                      {isSelected && (
                        <CheckIcon className="h-5 w-5 text-primary-600 flex-shrink-0" />
                      )}
                    </button>
                  )
                })
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Selected Category Preview */}
        {selectedCategoryData && (
          <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                {selectedCategoryData.icon_element}
                <span className="font-medium text-primary-900">
                  Selected: {selectedCategoryData.name}
                </span>
              </div>
              <Badge variant={getCategoryColor(selectedCategoryData)}>
                {selectedCategoryData.type}
              </Badge>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between border-t pt-4">
          <div className="text-sm text-neutral-600">
            {transactions.length === 1 ? (
              'Use arrow keys to navigate, Enter to select'
            ) : (
              `Will apply to ${transactions.length} transactions • Use ← → to preview`
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleApplyCategorization}
              disabled={!selectedCategory || isSaving}
              loading={isSaving}
              className={transactions.length > 1 ? 'bg-primary-600 hover:bg-primary-700' : ''}
            >
              {isSaving ? (
                transactions.length === 1 ? 'Applying...' : `Applying to ${transactions.length} transactions...`
              ) : (
                transactions.length === 1 ? 'Apply Category' : `Apply to ${transactions.length} transactions`
              )}
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  )
}