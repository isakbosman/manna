import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Receipt,
  Car,
  Percent,
  FileText,
  AlertCircle,
  CheckCircle,
  Calculator,
  Users,
  BarChart3,
  Info,
  ExternalLink,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Badge } from '../ui/badge'
import { Slider } from '../ui/slider'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '../ui/tooltip'
import { ScrollArea } from '../ui/scroll-area'
import { Progress as ProgressBar } from '../ui/progress'
import { taxApi, TaxCategory, CategorizeBulkRequest } from '../../lib/api/tax'
import { Transaction } from '../../lib/api/transactions'
import { cn } from '../../lib/utils'
import { format } from 'date-fns'

interface BulkTaxCategorizationProps {
  isOpen: boolean
  onClose: () => void
  transactions: Transaction[]
  onTransactionsUpdated: (transactions: Transaction[]) => void
}

export function BulkTaxCategorization({
  isOpen,
  onClose,
  transactions,
  onTransactionsUpdated,
}: BulkTaxCategorizationProps) {
  const queryClient = useQueryClient()

  // Form state
  const [selectedTaxCategoryId, setSelectedTaxCategoryId] = React.useState<string>('')
  const [businessUsePercentage, setBusinessUsePercentage] = React.useState<number>(100)
  const [businessPurpose, setBusinessPurpose] = React.useState<string>('')
  const [receiptUrl, setReceiptUrl] = React.useState<string>('')
  const [mileage, setMileage] = React.useState<number>(0)
  const [searchTerm, setSearchTerm] = React.useState<string>('')
  const [currentStep, setCurrentStep] = React.useState<'select' | 'processing' | 'complete'>('select')
  const [progress, setProgress] = React.useState<number>(0)
  const [processedCount, setProcessedCount] = React.useState<number>(0)
  const [errors, setErrors] = React.useState<string[]>([])

  // Form validation
  const [formErrors, setFormErrors] = React.useState<Record<string, string>>({})

  // Load tax categories
  const { data: taxCategories = [], isLoading: isLoadingCategories } = useQuery({
    queryKey: ['tax-categories'],
    queryFn: taxApi.getTaxCategories,
  })

  // Filter categories based on search
  const filteredCategories = React.useMemo(() => {
    if (!searchTerm) return taxCategories
    return taxCategories.filter(category =>
      category.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      category.schedule_c_line.toLowerCase().includes(searchTerm.toLowerCase()) ||
      category.description.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [taxCategories, searchTerm])

  // Get selected category
  const selectedCategory = React.useMemo(
    () => taxCategories.find(cat => cat.id === selectedTaxCategoryId),
    [taxCategories, selectedTaxCategoryId]
  )

  // Bulk categorization mutation
  const bulkCategorizeMutation = useMutation({
    mutationFn: async (data: CategorizeBulkRequest) => {
      setCurrentStep('processing')
      setProgress(0)
      setProcessedCount(0)
      setErrors([])

      // Process in batches to show progress
      const batchSize = 10
      const batches = []
      for (let i = 0; i < data.transaction_ids.length; i += batchSize) {
        batches.push(data.transaction_ids.slice(i, i + batchSize))
      }

      const allResults = []
      const batchErrors = []

      for (let i = 0; i < batches.length; i++) {
        try {
          const batchData = {
            ...data,
            transaction_ids: batches[i],
          }
          const result = await taxApi.categorizeBulk(batchData)
          allResults.push(...result)
          setProcessedCount(prev => prev + batches[i].length)
          setProgress(((i + 1) / batches.length) * 100)
        } catch (error: any) {
          batchErrors.push(`Batch ${i + 1}: ${error.message}`)
        }
      }

      if (batchErrors.length > 0) {
        setErrors(batchErrors)
      }

      return allResults
    },
    onSuccess: (results) => {
      // Update transactions with tax categorizations
      const updatedTransactions = transactions.map(transaction => {
        const result = results.find(r => r.transaction_id === transaction.id)
        if (result) {
          return {
            ...transaction,
            tax_categorization: result,
          }
        }
        return transaction
      })

      onTransactionsUpdated(updatedTransactions)
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['tax-summary'] })
      setCurrentStep('complete')
    },
    onError: (error: any) => {
      setErrors([error.message || 'Failed to categorize transactions'])
      setCurrentStep('select')
    },
  })

  // Reset form when modal opens/closes
  React.useEffect(() => {
    if (isOpen) {
      setSelectedTaxCategoryId('')
      setBusinessUsePercentage(100)
      setBusinessPurpose('')
      setReceiptUrl('')
      setMileage(0)
      setSearchTerm('')
      setCurrentStep('select')
      setProgress(0)
      setProcessedCount(0)
      setErrors([])
      setFormErrors({})
    }
  }, [isOpen])

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!selectedTaxCategoryId) {
      newErrors.category = 'Please select a tax category'
    }

    if (selectedCategory?.requires_receipt && !receiptUrl.trim()) {
      newErrors.receipt = 'Receipt is required for this category'
    }

    if (selectedCategory?.is_vehicle_expense && mileage <= 0) {
      newErrors.mileage = 'Mileage is required for vehicle expenses'
    }

    if (!businessPurpose.trim()) {
      newErrors.businessPurpose = 'Business purpose is required'
    }

    if (businessUsePercentage < 1 || businessUsePercentage > 100) {
      newErrors.businessUse = 'Business use percentage must be between 1% and 100%'
    }

    setFormErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!validateForm()) return

    const data: CategorizeBulkRequest = {
      transaction_ids: transactions.map(t => t.id),
      tax_category_id: selectedTaxCategoryId,
      business_use_percentage: businessUsePercentage,
      business_purpose: businessPurpose.trim() || undefined,
      receipt_url: receiptUrl.trim() || undefined,
      mileage: selectedCategory?.is_vehicle_expense ? mileage : undefined,
    }

    bulkCategorizeMutation.mutate(data)
  }

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Math.abs(amount))
  }

  const totalAmount = transactions.reduce((sum, t) => sum + Math.abs(t.amount), 0)

  const calculateTotalDeductibleAmount = () => {
    if (!selectedCategory) return 0
    let amount = totalAmount

    // Apply business use percentage
    amount = amount * (businessUsePercentage / 100)

    // Apply 50% limit for meals
    if (selectedCategory.is_meals_50_percent) {
      amount = amount * 0.5
    }

    return amount
  }

  const handleClose = () => {
    if (currentStep === 'processing') return // Prevent closing during processing
    onClose()
  }

  if (!isOpen) return null

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Bulk Tax Categorization
          </DialogTitle>
          <DialogDescription>
            Apply the same tax category to {transactions.length} selected transactions.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Error Messages */}
          {errors.length > 0 && (
            <div className="space-y-2">
              {errors.map((error, index) => (
                <div key={index} className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  <AlertCircle className="h-5 w-5" />
                  <span>{error}</span>
                </div>
              ))}
            </div>
          )}

          {currentStep === 'select' && (
            <>
              {/* Transaction Summary */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                    <Calculator className="h-5 w-5" />
                    {transactions.length} Selected Transactions
                  </h3>
                  <div className="text-right">
                    <p className="text-lg font-bold text-gray-900">
                      Total: {formatAmount(totalAmount)}
                    </p>
                    {selectedCategory && (
                      <p className="text-sm text-green-600">
                        Deductible: {formatAmount(calculateTotalDeductibleAmount())}
                      </p>
                    )}
                  </div>
                </div>

                {/* Sample transactions preview */}
                <div className="space-y-2">
                  <p className="text-sm text-gray-600 mb-2">Sample transactions:</p>
                  {transactions.slice(0, 3).map((transaction) => (
                    <div key={transaction.id} className="flex items-center justify-between bg-white border rounded p-2 text-sm">
                      <div className="flex-1">
                        <p className="font-medium">{transaction.description}</p>
                        <p className="text-gray-600">{format(new Date(transaction.date), 'MMM d, yyyy')}</p>
                      </div>
                      <p className="font-medium">{formatAmount(transaction.amount)}</p>
                    </div>
                  ))}
                  {transactions.length > 3 && (
                    <p className="text-sm text-gray-500 text-center">
                      ... and {transactions.length - 3} more transactions
                    </p>
                  )}
                </div>
              </div>

              {/* Category Search */}
              <div className="space-y-3">
                <Label htmlFor="category-search">Tax Category</Label>
                <Input
                  id="category-search"
                  placeholder="Search tax categories..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className={formErrors.category ? 'border-red-500' : ''}
                />
                {formErrors.category && (
                  <p className="text-sm text-red-600">{formErrors.category}</p>
                )}
              </div>

              {/* Category List */}
              <ScrollArea className="h-48 border rounded-lg">
                <div className="p-2 space-y-1">
                  {isLoadingCategories ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="h-6 w-6 animate-spin rounded-full border-b-2 border-blue-600" />
                    </div>
                  ) : filteredCategories.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      {searchTerm ? 'No categories found' : 'No tax categories available'}
                    </div>
                  ) : (
                    filteredCategories.map((category) => (
                      <button
                        key={category.id}
                        onClick={() => setSelectedTaxCategoryId(category.id)}
                        className={cn(
                          'w-full flex items-start gap-3 p-3 rounded-lg border text-left transition-colors hover:bg-gray-50',
                          selectedTaxCategoryId === category.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200'
                        )}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-medium text-gray-900">{category.name}</p>
                            <Badge variant="outline" className="text-xs">
                              Line {category.schedule_c_line}
                            </Badge>
                            {category.is_meals_50_percent && (
                              <Badge variant="secondary" className="text-xs">
                                50% Deductible
                              </Badge>
                            )}
                            {category.requires_receipt && (
                              <Receipt className="h-4 w-4 text-orange-500" />
                            )}
                            {category.is_vehicle_expense && (
                              <Car className="h-4 w-4 text-blue-500" />
                            )}
                          </div>
                          <p className="text-sm text-gray-600">{category.description}</p>
                        </div>
                        {selectedTaxCategoryId === category.id && (
                          <CheckCircle className="h-5 w-5 text-blue-600 flex-shrink-0" />
                        )}
                      </button>
                    ))
                  )}
                </div>
              </ScrollArea>

              {/* Category-specific fields */}
              {selectedCategory && (
                <div className="space-y-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-900 flex items-center gap-2">
                    <Info className="h-4 w-4" />
                    Category Details: {selectedCategory.name}
                  </h4>

                  {/* Business Use Percentage */}
                  {selectedCategory.has_business_use_percentage && (
                    <div className="space-y-2">
                      <Label className="flex items-center gap-2">
                        <Percent className="h-4 w-4" />
                        Business Use Percentage: {businessUsePercentage}%
                      </Label>
                      <Slider
                        value={[businessUsePercentage]}
                        onValueChange={(value) => setBusinessUsePercentage(value[0])}
                        max={100}
                        min={1}
                        step={1}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-gray-600">
                        <span>1%</span>
                        <span>100%</span>
                      </div>
                      {formErrors.businessUse && (
                        <p className="text-sm text-red-600">{formErrors.businessUse}</p>
                      )}
                    </div>
                  )}

                  {/* Business Purpose */}
                  <div className="space-y-2">
                    <Label htmlFor="business-purpose" className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Business Purpose *
                    </Label>
                    <Input
                      id="business-purpose"
                      placeholder="Describe the business purpose of these expenses..."
                      value={businessPurpose}
                      onChange={(e) => setBusinessPurpose(e.target.value)}
                      className={formErrors.businessPurpose ? 'border-red-500' : ''}
                    />
                    {formErrors.businessPurpose && (
                      <p className="text-sm text-red-600">{formErrors.businessPurpose}</p>
                    )}
                  </div>

                  {/* Receipt URL */}
                  {selectedCategory.requires_receipt && (
                    <div className="space-y-2">
                      <Label htmlFor="receipt-url" className="flex items-center gap-2">
                        <Receipt className="h-4 w-4" />
                        Receipt URL *
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-4 w-4 text-gray-400 cursor-help" />
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>For bulk operations, provide a general receipt or folder link</p>
                          </TooltipContent>
                        </Tooltip>
                      </Label>
                      <div className="flex gap-2">
                        <Input
                          id="receipt-url"
                          placeholder="https://..."
                          value={receiptUrl}
                          onChange={(e) => setReceiptUrl(e.target.value)}
                          className={cn('flex-1', formErrors.receipt ? 'border-red-500' : '')}
                        />
                        {receiptUrl && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(receiptUrl, '_blank')}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                      {formErrors.receipt && (
                        <p className="text-sm text-red-600">{formErrors.receipt}</p>
                      )}
                    </div>
                  )}

                  {/* Mileage for Vehicle Expenses */}
                  {selectedCategory.is_vehicle_expense && (
                    <div className="space-y-2">
                      <Label htmlFor="mileage" className="flex items-center gap-2">
                        <Car className="h-4 w-4" />
                        Total Business Miles *
                      </Label>
                      <Input
                        id="mileage"
                        type="number"
                        placeholder="0"
                        value={mileage || ''}
                        onChange={(e) => setMileage(parseInt(e.target.value) || 0)}
                        min="0"
                        className={formErrors.mileage ? 'border-red-500' : ''}
                      />
                      {formErrors.mileage && (
                        <p className="text-sm text-red-600">{formErrors.mileage}</p>
                      )}
                      <p className="text-xs text-gray-600">
                        Total business miles for all selected vehicle expenses
                      </p>
                    </div>
                  )}

                  {/* 50% Meals Notice */}
                  {selectedCategory.is_meals_50_percent && (
                    <div className="flex items-center gap-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
                      <Info className="h-4 w-4" />
                      <span>
                        Business meals are generally 50% deductible. The calculation has been adjusted automatically.
                      </span>
                    </div>
                  )}

                  {/* Total Deductible Amount Preview */}
                  <div className="flex items-center justify-between p-3 bg-white border border-blue-200 rounded">
                    <span className="font-medium text-gray-900">Estimated Total Deductible Amount:</span>
                    <span className="text-lg font-bold text-green-600">
                      {formatAmount(calculateTotalDeductibleAmount())}
                    </span>
                  </div>
                </div>
              )}
            </>
          )}

          {currentStep === 'processing' && (
            <div className="space-y-4 text-center">
              <div className="flex items-center justify-center">
                <BarChart3 className="h-8 w-8 animate-spin" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">Processing Transactions</h3>
                <p className="text-gray-600 mb-4">
                  Applying tax categorization to {transactions.length} transactions...
                </p>
                <ProgressBar value={progress} className="w-full" />
                <p className="text-sm text-gray-600 mt-2">
                  {processedCount} of {transactions.length} transactions processed
                </p>
              </div>
            </div>
          )}

          {currentStep === 'complete' && (
            <div className="space-y-4 text-center">
              <div className="flex items-center justify-center">
                <CheckCircle className="h-16 w-16 text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-green-900">Categorization Complete</h3>
                <p className="text-gray-600">
                  Successfully categorized {processedCount} transactions for tax purposes.
                </p>
                {errors.length > 0 && (
                  <p className="text-orange-600 text-sm">
                    {errors.length} batch(es) encountered errors. Some transactions may need manual review.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          {currentStep === 'select' && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={!selectedTaxCategoryId || bulkCategorizeMutation.isPending}
              >
                Apply to {transactions.length} Transactions
              </Button>
            </>
          )}
          {currentStep === 'processing' && (
            <Button disabled>
              Processing...
            </Button>
          )}
          {currentStep === 'complete' && (
            <Button onClick={handleClose}>
              Done
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}