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
  DollarSign,
  Calendar,
  Building,
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
import { Select } from '../ui/select'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '../ui/tooltip'
import { ScrollArea } from '../ui/scroll-area'
import { taxApi, TaxCategory, CategorizeSingleRequest } from '../../lib/api/tax'
import { Transaction } from '../../lib/api/transactions'
import { cn } from '../../lib/utils'
import { format } from 'date-fns'

interface TaxCategorizationModalProps {
  isOpen: boolean
  onClose: () => void
  transaction: Transaction
  onTransactionUpdated: (transaction: Transaction) => void
}

export function TaxCategorizationModal({
  isOpen,
  onClose,
  transaction,
  onTransactionUpdated,
}: TaxCategorizationModalProps) {
  const queryClient = useQueryClient()

  // Form state
  const [selectedTaxCategoryId, setSelectedTaxCategoryId] = React.useState<string>('')
  const [businessUsePercentage, setBusinessUsePercentage] = React.useState<number>(100)
  const [businessPurpose, setBusinessPurpose] = React.useState<string>('')
  const [receiptUrl, setReceiptUrl] = React.useState<string>('')
  const [mileage, setMileage] = React.useState<number>(0)
  const [searchTerm, setSearchTerm] = React.useState<string>('')

  // Form validation
  const [errors, setErrors] = React.useState<Record<string, string>>({})

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

  // Categorization mutation
  const categorizeMutation = useMutation({
    mutationFn: (data: CategorizeSingleRequest) =>
      taxApi.categorizeSingle(transaction.id, data),
    onSuccess: (result) => {
      // Update the transaction with tax categorization
      const updatedTransaction = {
        ...transaction,
        tax_categorization: result,
      }
      onTransactionUpdated(updatedTransaction)
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['tax-summary'] })
      onClose()
    },
    onError: (error: any) => {
      setErrors({ submit: error.message || 'Failed to categorize transaction' })
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
      setErrors({})
    }
  }, [isOpen])

  // Auto-detect category based on merchant/description
  React.useEffect(() => {
    if (!transaction || taxCategories.length === 0) return

    const description = transaction.description?.toLowerCase() || ''
    const merchant = transaction.merchant_name?.toLowerCase() || ''
    const combined = `${description} ${merchant}`.toLowerCase()

    // Simple auto-detection rules
    let suggestedCategory: TaxCategory | undefined

    if (combined.includes('uber') || combined.includes('lyft') || combined.includes('taxi')) {
      suggestedCategory = taxCategories.find(cat => cat.is_vehicle_expense)
    } else if (combined.includes('restaurant') || combined.includes('cafe') || combined.includes('food')) {
      suggestedCategory = taxCategories.find(cat => cat.is_meals_50_percent)
    } else if (combined.includes('office') || combined.includes('supplies')) {
      suggestedCategory = taxCategories.find(cat => cat.name.toLowerCase().includes('supplies'))
    } else if (combined.includes('internet') || combined.includes('phone') || combined.includes('software')) {
      suggestedCategory = taxCategories.find(cat => cat.name.toLowerCase().includes('utilities') || cat.name.toLowerCase().includes('software'))
    }

    if (suggestedCategory && !selectedTaxCategoryId) {
      setSelectedTaxCategoryId(suggestedCategory.id)
      if (suggestedCategory.is_meals_50_percent) {
        setBusinessUsePercentage(50)
      }
    }
  }, [transaction, taxCategories, selectedTaxCategoryId])

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

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!validateForm()) return

    const data: CategorizeSingleRequest = {
      tax_category_id: selectedTaxCategoryId,
      business_use_percentage: businessUsePercentage,
      business_purpose: businessPurpose.trim() || undefined,
      receipt_url: receiptUrl.trim() || undefined,
      mileage: selectedCategory?.is_vehicle_expense ? mileage : undefined,
    }

    categorizeMutation.mutate(data)
  }

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Math.abs(amount))
  }

  const calculateDeductibleAmount = () => {
    if (!selectedCategory) return 0
    let amount = Math.abs(transaction.amount)

    // Apply business use percentage
    amount = amount * (businessUsePercentage / 100)

    // Apply 50% limit for meals
    if (selectedCategory.is_meals_50_percent) {
      amount = amount * 0.5
    }

    return amount
  }

  if (!isOpen) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5" />
            Tax Categorization
          </DialogTitle>
          <DialogDescription>
            Categorize this transaction for tax purposes and business expense tracking.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Error Messages */}
          {errors.submit && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
              <AlertCircle className="h-5 w-5" />
              <span>{errors.submit}</span>
            </div>
          )}

          {/* Transaction Details */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">
                  {transaction.description}
                </h3>
                <div className="flex items-center gap-3 mt-2 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    {format(new Date(transaction.date), 'MMM d, yyyy')}
                  </div>
                  {transaction.merchant_name && (
                    <div className="flex items-center gap-1">
                      <Building className="h-4 w-4" />
                      {transaction.merchant_name}
                    </div>
                  )}
                </div>
              </div>
              <div className="text-right">
                <p className={cn(
                  'text-lg font-bold',
                  transaction.amount < 0 ? 'text-red-600' : 'text-green-600'
                )}>
                  {transaction.amount < 0 ? '-' : '+'}{formatAmount(transaction.amount)}
                </p>
                {selectedCategory && (
                  <p className="text-sm text-gray-600 mt-1">
                    Deductible: {formatAmount(calculateDeductibleAmount())}
                  </p>
                )}
              </div>
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
              className={errors.category ? 'border-red-500' : ''}
            />
            {errors.category && (
              <p className="text-sm text-red-600">{errors.category}</p>
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
                  {errors.businessUse && (
                    <p className="text-sm text-red-600">{errors.businessUse}</p>
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
                  placeholder="Describe the business purpose of this expense..."
                  value={businessPurpose}
                  onChange={(e) => setBusinessPurpose(e.target.value)}
                  className={errors.businessPurpose ? 'border-red-500' : ''}
                />
                {errors.businessPurpose && (
                  <p className="text-sm text-red-600">{errors.businessPurpose}</p>
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
                        <p>Upload your receipt to cloud storage and paste the link here</p>
                      </TooltipContent>
                    </Tooltip>
                  </Label>
                  <div className="flex gap-2">
                    <Input
                      id="receipt-url"
                      placeholder="https://..."
                      value={receiptUrl}
                      onChange={(e) => setReceiptUrl(e.target.value)}
                      className={cn('flex-1', errors.receipt ? 'border-red-500' : '')}
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
                  {errors.receipt && (
                    <p className="text-sm text-red-600">{errors.receipt}</p>
                  )}
                </div>
              )}

              {/* Mileage for Vehicle Expenses */}
              {selectedCategory.is_vehicle_expense && (
                <div className="space-y-2">
                  <Label htmlFor="mileage" className="flex items-center gap-2">
                    <Car className="h-4 w-4" />
                    Business Miles *
                  </Label>
                  <Input
                    id="mileage"
                    type="number"
                    placeholder="0"
                    value={mileage || ''}
                    onChange={(e) => setMileage(parseInt(e.target.value) || 0)}
                    min="0"
                    className={errors.mileage ? 'border-red-500' : ''}
                  />
                  {errors.mileage && (
                    <p className="text-sm text-red-600">{errors.mileage}</p>
                  )}
                  <p className="text-xs text-gray-600">
                    Standard mileage rate for business use is typically deductible
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

              {/* Deductible Amount Preview */}
              <div className="flex items-center justify-between p-3 bg-white border border-blue-200 rounded">
                <span className="font-medium text-gray-900">Estimated Deductible Amount:</span>
                <span className="text-lg font-bold text-green-600">
                  {formatAmount(calculateDeductibleAmount())}
                </span>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!selectedTaxCategoryId || categorizeMutation.isPending}
          >
            {categorizeMutation.isPending ? 'Categorizing...' : 'Apply Tax Category'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}