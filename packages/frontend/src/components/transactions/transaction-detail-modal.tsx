import React from 'react'
import { 
  EditIcon, 
  TrashIcon, 
  TagIcon, 
  CalendarIcon, 
  BuildingIcon,
  DollarSignIcon,
  ClockIcon,
  SaveIcon,
  XIcon,
  SplitIcon,
  MessageSquareIcon,
  BrainIcon
} from 'lucide-react'
import { Modal } from '../ui/modal'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Badge } from '../ui/badge'
import { Transaction, transactionsApi, Account, categoriesApi } from '@/lib/api'
import { CategoryPicker } from './category-picker'
import { cn } from '../../lib/utils'
import { format } from 'date-fns'

interface TransactionDetailModalProps {
  transaction: Transaction | null
  isOpen: boolean
  onClose: () => void
  onTransactionUpdated: (transaction: Transaction) => void
  onTransactionDeleted: (transactionId: string) => void
  accounts: Account[]
  className?: string
}

export function TransactionDetailModal({
  transaction,
  isOpen,
  onClose,
  onTransactionUpdated,
  onTransactionDeleted,
  accounts,
  className
}: TransactionDetailModalProps) {
  const [isEditing, setIsEditing] = React.useState(false)
  const [isSaving, setIsSaving] = React.useState(false)
  const [isDeleting, setIsDeleting] = React.useState(false)
  const [showSplitModal, setShowSplitModal] = React.useState(false)
  const [mlPredictions, setMlPredictions] = React.useState<any[]>([])
  const [feedbackGiven, setFeedbackGiven] = React.useState(false)
  
  // Form state
  const [formData, setFormData] = React.useState({
    description: '',
    category: '',
    subcategory: '',
    merchant_name: '',
    amount: 0,
    date: '',
    notes: ''
  })

  React.useEffect(() => {
    if (transaction && isOpen) {
      setFormData({
        description: transaction.description || '',
        category: transaction.category || '',
        subcategory: transaction.subcategory || '',
        merchant_name: transaction.merchant_name || '',
        amount: transaction.amount,
        date: transaction.date,
        notes: '' // Add notes field to Transaction interface
      })
      setIsEditing(false)
      setFeedbackGiven(false)
      
      // Load ML predictions if no category is set
      if (!transaction.category) {
        loadMLPredictions(transaction.id)
      }
    }
  }, [transaction, isOpen])

  const loadMLPredictions = async (transactionId: string) => {
    try {
      const predictions = await categoriesApi.categorizeTransaction(transactionId)
      setMlPredictions(predictions)
    } catch (error) {
      console.error('Failed to load ML predictions:', error)
    }
  }

  const handleSave = async () => {
    if (!transaction) return

    try {
      setIsSaving(true)
      const updatedTransaction = await transactionsApi.updateTransaction(transaction.id, {
        description: formData.description,
        category: formData.category,
        subcategory: formData.subcategory,
        merchant_name: formData.merchant_name,
        amount: formData.amount,
        date: formData.date
      })
      onTransactionUpdated(updatedTransaction)
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to update transaction:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!transaction || !window.confirm('Are you sure you want to delete this transaction?')) {
      return
    }

    try {
      setIsDeleting(true)
      await transactionsApi.deleteTransaction(transaction.id)
      onTransactionDeleted(transaction.id)
      onClose()
    } catch (error) {
      console.error('Failed to delete transaction:', error)
    } finally {
      setIsDeleting(false)
    }
  }

  const handleMLFeedback = async (categoryId: string, isCorrect: boolean) => {
    if (!transaction) return

    try {
      await categoriesApi.provideFeedback(transaction.id, categoryId, isCorrect)
      setFeedbackGiven(true)
    } catch (error) {
      console.error('Failed to provide feedback:', error)
    }
  }

  const getAccount = () => {
    return accounts.find(a => a.id === transaction?.account_id)
  }

  const formatAmount = (amount: number) => {
    const isNegative = amount < 0
    const absAmount = Math.abs(amount)
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(absAmount)
    
    return isNegative ? `-${formatted}` : formatted
  }

  const getAmountColor = (amount: number) => {
    return amount < 0 ? 'text-error-600' : 'text-success-600'
  }

  if (!transaction) return null

  const account = getAccount()

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title={isEditing ? 'Edit Transaction' : 'Transaction Details'}
        size="lg"
        className={className}
      >
        <div className="space-y-6">
          {/* Transaction Header */}
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {isEditing ? (
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="text-lg font-semibold"
                  placeholder="Transaction description"
                />
              ) : (
                <h3 className="text-lg font-semibold text-neutral-900">
                  {transaction.description}
                </h3>
              )}
              
              <div className="flex items-center gap-2 mt-2">
                <Badge variant={transaction.is_pending ? 'warning' : 'success'}>
                  {transaction.is_pending ? 'Pending' : 'Completed'}
                </Badge>
                {transaction.category && (
                  <Badge variant="outline">
                    {transaction.category}
                  </Badge>
                )}
              </div>
            </div>
            
            <div className="text-right">
              {isEditing ? (
                <Input
                  type="number"
                  step="0.01"
                  value={formData.amount}
                  onChange={(e) => setFormData(prev => ({ ...prev, amount: parseFloat(e.target.value) }))}
                  className="text-right text-xl font-bold"
                />
              ) : (
                <p className={cn('text-xl font-bold', getAmountColor(transaction.amount))}>
                  {formatAmount(transaction.amount)}
                </p>
              )}
            </div>
          </div>

          {/* Transaction Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Date */}
            <div className="flex items-center gap-3">
              <CalendarIcon className="h-5 w-5 text-neutral-500" />
              <div>
                <p className="text-sm text-neutral-600">Date</p>
                {isEditing ? (
                  <Input
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
                  />
                ) : (
                  <p className="font-medium">
                    {format(new Date(transaction.date), 'MMM d, yyyy')}
                  </p>
                )}
              </div>
            </div>

            {/* Account */}
            <div className="flex items-center gap-3">
              <BuildingIcon className="h-5 w-5 text-neutral-500" />
              <div>
                <p className="text-sm text-neutral-600">Account</p>
                <p className="font-medium">{account?.name}</p>
                <p className="text-xs text-neutral-500">{account?.subtype}</p>
              </div>
            </div>

            {/* Merchant */}
            {(transaction.merchant_name || isEditing) && (
              <div className="flex items-center gap-3">
                <BuildingIcon className="h-5 w-5 text-neutral-500" />
                <div className="flex-1">
                  <p className="text-sm text-neutral-600">Merchant</p>
                  {isEditing ? (
                    <Input
                      value={formData.merchant_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, merchant_name: e.target.value }))}
                      placeholder="Merchant name"
                    />
                  ) : (
                    <p className="font-medium">{transaction.merchant_name || 'Not specified'}</p>
                  )}
                </div>
              </div>
            )}

            {/* Category */}
            <div className="flex items-center gap-3">
              <TagIcon className="h-5 w-5 text-neutral-500" />
              <div className="flex-1">
                <p className="text-sm text-neutral-600">Category</p>
                {isEditing ? (
                  <CategoryPicker
                    selectedCategory={formData.category}
                    onCategorySelect={(categoryId) => 
                      setFormData(prev => ({ ...prev, category: categoryId }))
                    }
                    transactionDescription={transaction.description}
                    mlPredictions={mlPredictions}
                  />
                ) : (
                  <p className="font-medium">{transaction.category || 'Uncategorized'}</p>
                )}
              </div>
            </div>
          </div>

          {/* ML Predictions (if not categorized) */}
          {!transaction.category && mlPredictions.length > 0 && !isEditing && (
            <div className="rounded-lg bg-info-50 border border-info-200 p-4">
              <div className="flex items-center gap-2 mb-3">
                <BrainIcon className="h-5 w-5 text-info-600" />
                <h4 className="font-medium text-info-900">AI Category Suggestions</h4>
              </div>
              
              <div className="space-y-2">
                {mlPredictions.slice(0, 3).map((prediction, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{prediction.category_name}</span>
                      <Badge variant="info" className="text-xs">
                        {Math.round(prediction.confidence * 100)}% confidence
                      </Badge>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => {
                          setFormData(prev => ({ ...prev, category: prediction.category_id }))
                          handleMLFeedback(prediction.category_id, true)
                        }}
                      >
                        Use This
                      </Button>
                      {!feedbackGiven && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleMLFeedback(prediction.category_id, false)}
                        >
                          Not Right
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="text-xs text-neutral-500 space-y-1">
            <p>Created: {format(new Date(transaction.created_at), 'MMM d, yyyy h:mm a')}</p>
            <p>Updated: {format(new Date(transaction.updated_at), 'MMM d, yyyy h:mm a')}</p>
            {transaction.plaid_transaction_id && (
              <p>Plaid ID: {transaction.plaid_transaction_id}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between border-t pt-4">
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSplitModal(true)}
                disabled={isEditing}
              >
                <SplitIcon className="h-4 w-4 mr-1" />
                Split
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                disabled={isEditing}
              >
                <MessageSquareIcon className="h-4 w-4 mr-1" />
                Add Note
              </Button>
            </div>

            <div className="flex gap-2">
              {isEditing ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setIsEditing(false)
                      // Reset form data
                      setFormData({
                        description: transaction.description || '',
                        category: transaction.category || '',
                        subcategory: transaction.subcategory || '',
                        merchant_name: transaction.merchant_name || '',
                        amount: transaction.amount,
                        date: transaction.date,
                        notes: ''
                      })
                    }}
                  >
                    <XIcon className="h-4 w-4 mr-1" />
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSave}
                    loading={isSaving}
                  >
                    <SaveIcon className="h-4 w-4 mr-1" />
                    Save
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                  >
                    <EditIcon className="h-4 w-4 mr-1" />
                    Edit
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleDelete}
                    loading={isDeleting}
                  >
                    <TrashIcon className="h-4 w-4 mr-1" />
                    Delete
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </Modal>

      {/* Split Transaction Modal - TODO: Implement */}
      {showSplitModal && (
        <Modal
          isOpen={showSplitModal}
          onClose={() => setShowSplitModal(false)}
          title="Split Transaction"
          description="Split this transaction into multiple categories"
        >
          <div className="text-center text-neutral-600 py-8">
            Split transaction functionality coming soon...
          </div>
        </Modal>
      )}
    </>
  )
}