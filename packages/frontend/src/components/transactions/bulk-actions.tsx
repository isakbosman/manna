import React from 'react'
import {
  TagIcon,
  TrashIcon,
  DownloadIcon,
  BrainIcon,
  CheckIcon,
  XIcon
} from 'lucide-react'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Modal } from '../ui/modal'
import { CategoryPicker } from './category-picker'
import { Transaction, transactionsApi, categoriesApi } from '@/lib/api'
import { cn } from '../../lib/utils'

interface BulkActionsProps {
  selectedTransactions: Transaction[]
  onTransactionsUpdated: (transactions: Transaction[]) => void
  onTransactionsDeleted: (transactionIds: string[]) => void
  onSelectionClear: () => void
  className?: string
}

export function BulkActions({
  selectedTransactions,
  onTransactionsUpdated,
  onTransactionsDeleted,
  onSelectionClear,
  className
}: BulkActionsProps) {
  const [showCategoryModal, setShowCategoryModal] = React.useState(false)
  const [showDeleteModal, setShowDeleteModal] = React.useState(false)
  const [isLoading, setIsLoading] = React.useState(false)
  const [selectedCategory, setSelectedCategory] = React.useState('')
  const [mlResults, setMlResults] = React.useState<any>(null)

  if (selectedTransactions.length === 0) {
    return null
  }

  const handleBulkCategorize = async () => {
    if (!selectedCategory) return

    try {
      setIsLoading(true)
      const transactionIds = selectedTransactions.map(t => t.id)
      const updatedTransactions = await transactionsApi.bulkUpdateTransactions({
        transaction_ids: transactionIds,
        updates: { category: selectedCategory }
      })
      
      onTransactionsUpdated(updatedTransactions)
      setShowCategoryModal(false)
      setSelectedCategory('')
      onSelectionClear()
    } catch (error) {
      console.error('Failed to bulk categorize:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleBulkDelete = async () => {
    try {
      setIsLoading(true)
      const deletePromises = selectedTransactions.map(t => 
        transactionsApi.deleteTransaction(t.id)
      )
      await Promise.all(deletePromises)
      
      onTransactionsDeleted(selectedTransactions.map(t => t.id))
      setShowDeleteModal(false)
      onSelectionClear()
    } catch (error) {
      console.error('Failed to bulk delete:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleMLCategorize = async () => {
    try {
      setIsLoading(true)
      const transactionIds = selectedTransactions.map(t => t.id)
      const results = await categoriesApi.bulkCategorize(transactionIds)
      setMlResults(results)
    } catch (error) {
      console.error('Failed to ML categorize:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleExport = async (format: 'csv' | 'xlsx') => {
    try {
      setIsLoading(true)
      // Export selected transactions only
      const transactionIds = selectedTransactions.map(t => t.id)
      await transactionsApi.exportTransactions(
        { transaction_ids: transactionIds } as any, 
        format
      )
    } catch (error) {
      console.error('Failed to export:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const totalAmount = selectedTransactions.reduce((sum, t) => sum + t.amount, 0)
  const uncategorizedCount = selectedTransactions.filter(t => !t.category).length

  return (
    <>
      <div className={cn('flex items-center justify-between p-4 bg-primary-50 border border-primary-200 rounded-lg', className)}>
        {/* Selection Summary */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <CheckIcon className="h-5 w-5 text-primary-600" />
            <span className="font-medium text-primary-900">
              {selectedTransactions.length} selected
            </span>
          </div>
          
          <div className="text-sm text-primary-700">
            Total: ${Math.abs(totalAmount).toFixed(2)}
          </div>
          
          {uncategorizedCount > 0 && (
            <Badge variant="warning" className="text-xs">
              {uncategorizedCount} uncategorized
            </Badge>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCategoryModal(true)}
            disabled={isLoading}
          >
            <TagIcon className="h-4 w-4 mr-1" />
            Categorize
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleMLCategorize}
            disabled={isLoading || uncategorizedCount === 0}
            loading={isLoading}
          >
            <BrainIcon className="h-4 w-4 mr-1" />
            AI Categorize
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('csv')}
            disabled={isLoading}
          >
            <DownloadIcon className="h-4 w-4 mr-1" />
            Export
          </Button>
          
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setShowDeleteModal(true)}
            disabled={isLoading}
          >
            <TrashIcon className="h-4 w-4 mr-1" />
            Delete
          </Button>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={onSelectionClear}
          >
            <XIcon className="h-4 w-4 mr-1" />
            Clear
          </Button>
        </div>
      </div>

      {/* Category Selection Modal */}
      <Modal
        isOpen={showCategoryModal}
        onClose={() => setShowCategoryModal(false)}
        title="Bulk Categorize Transactions"
        description={`Assign a category to ${selectedTransactions.length} selected transactions`}
      >
        <div className="space-y-4">
          <CategoryPicker
            selectedCategory={selectedCategory}
            onCategorySelect={setSelectedCategory}
            placeholder="Select category for all transactions"
          />
          
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setShowCategoryModal(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleBulkCategorize}
              disabled={!selectedCategory}
              loading={isLoading}
            >
              Apply to {selectedTransactions.length} transactions
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Transactions"
        description={`Are you sure you want to delete ${selectedTransactions.length} selected transactions? This action cannot be undone.`}
      >
        <div className="space-y-4">
          <div className="bg-error-50 border border-error-200 rounded-lg p-4">
            <div className="text-sm text-error-700">
              <strong>Warning:</strong> This will permanently delete the selected transactions:
            </div>
            <ul className="mt-2 text-sm text-error-600 max-h-32 overflow-y-auto">
              {selectedTransactions.slice(0, 10).map((transaction) => (
                <li key={transaction.id} className="truncate">
                  • {transaction.description} - ${Math.abs(transaction.amount).toFixed(2)}
                </li>
              ))}
              {selectedTransactions.length > 10 && (
                <li className="text-error-500">...and {selectedTransactions.length - 10} more</li>
              )}
            </ul>
          </div>
          
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setShowDeleteModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleBulkDelete}
              loading={isLoading}
            >
              Delete {selectedTransactions.length} transactions
            </Button>
          </div>
        </div>
      </Modal>

      {/* ML Results Modal */}
      {mlResults && (
        <Modal
          isOpen={!!mlResults}
          onClose={() => setMlResults(null)}
          title="AI Categorization Results"
          description={`AI suggestions for ${selectedTransactions.length} transactions`}
          size="lg"
        >
          <div className="space-y-4">
            <div className="text-sm text-neutral-600">
              Successfully categorized {mlResults.categorized_count} transactions.
            </div>
            
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {Object.entries(mlResults.predictions).map(([transactionId, predictions]: [string, any]) => {
                const transaction = selectedTransactions.find(t => t.id === transactionId)
                const topPrediction = predictions[0]
                
                return (
                  <div key={transactionId} className="flex items-center justify-between p-2 border rounded">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{transaction?.description}</p>
                      <p className="text-xs text-neutral-500">${Math.abs(transaction?.amount || 0).toFixed(2)}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="info" className="text-xs">
                        {topPrediction.category_name}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {Math.round(topPrediction.confidence * 100)}%
                      </Badge>
                    </div>
                  </div>
                )
              })}
            </div>
            
            <div className="flex justify-end">
              <Button onClick={() => setMlResults(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  )
}