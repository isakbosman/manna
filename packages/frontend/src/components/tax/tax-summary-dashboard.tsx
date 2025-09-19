import React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Download,
  Calendar,
  DollarSign,
  Receipt,
  FileText,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Filter,
  Eye,
  ExternalLink,
} from 'lucide-react'
import { Card } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Select } from '../ui/select'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { ScrollArea } from '../ui/scroll-area'
import { Progress } from '../ui/progress'
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '../ui/tooltip'
import { taxApi, TaxSummary } from '../../lib/api/tax'
import { cn } from '../../lib/utils'

interface TaxSummaryDashboardProps {
  className?: string
}

export function TaxSummaryDashboard({ className }: TaxSummaryDashboardProps) {
  const currentYear = new Date().getFullYear()
  const [selectedYear, setSelectedYear] = React.useState<number>(currentYear)
  const [filterCategory, setFilterCategory] = React.useState<string>('')
  const [isExporting, setIsExporting] = React.useState<{csv: boolean, pdf: boolean}>({
    csv: false,
    pdf: false,
  })

  // Load tax summary for selected year
  const { data: taxSummary, isLoading: isLoadingSummary, error } = useQuery({
    queryKey: ['tax-summary', selectedYear],
    queryFn: () => taxApi.getTaxSummary(selectedYear),
    enabled: !!selectedYear,
  })

  // Generate available years (current year and previous 4 years)
  const availableYears = React.useMemo(() => {
    const years = []
    for (let i = 0; i < 5; i++) {
      years.push(currentYear - i)
    }
    return years
  }, [currentYear])

  // Filter categories based on search
  const filteredCategories = React.useMemo(() => {
    if (!taxSummary?.categories) return []
    if (!filterCategory) return taxSummary.categories

    return taxSummary.categories.filter(category =>
      category.category_name.toLowerCase().includes(filterCategory.toLowerCase()) ||
      category.schedule_c_line.toLowerCase().includes(filterCategory.toLowerCase())
    )
  }, [taxSummary?.categories, filterCategory])

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const getDocumentationColor = (status: 'complete' | 'partial' | 'missing') => {
    switch (status) {
      case 'complete': return 'text-green-600 bg-green-50 border-green-200'
      case 'partial': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'missing': return 'text-red-600 bg-red-50 border-red-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getDocumentationIcon = (status: 'complete' | 'partial' | 'missing') => {
    switch (status) {
      case 'complete': return <CheckCircle className="h-4 w-4" />
      case 'partial': return <AlertTriangle className="h-4 w-4" />
      case 'missing': return <FileText className="h-4 w-4" />
      default: return <FileText className="h-4 w-4" />
    }
  }

  const handleExport = async (format: 'csv' | 'pdf') => {
    try {
      setIsExporting(prev => ({ ...prev, [format]: true }))
      await taxApi.downloadScheduleC(selectedYear, format)
    } catch (error) {
      console.error('Export failed:', error)
    } finally {
      setIsExporting(prev => ({ ...prev, [format]: false }))
    }
  }

  const calculateDocumentationProgress = () => {
    if (!taxSummary?.documentation_status) return 0
    const { total_transactions, with_receipts, complete_business_purpose } = taxSummary.documentation_status
    if (total_transactions === 0) return 100

    const receiptsScore = (with_receipts / total_transactions) * 50
    const purposeScore = (complete_business_purpose / total_transactions) * 50
    return Math.round(receiptsScore + purposeScore)
  }

  if (error) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Tax Summary</h3>
          <p className="text-gray-600">
            Unable to load tax summary for {selectedYear}. Please try again later.
          </p>
        </div>
      </Card>
    )
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-gray-900">Tax Summary</h2>
          <Select
            value={selectedYear.toString()}
            onValueChange={(value) => setSelectedYear(parseInt(value))}
          >
            <option value="">Select Year</option>
            {availableYears.map(year => (
              <option key={year} value={year.toString()}>
                {year}
              </option>
            ))}
          </Select>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('csv')}
            disabled={!taxSummary || isExporting.csv}
          >
            {isExporting.csv ? (
              <div className="h-4 w-4 animate-spin rounded-full border-b-2 border-gray-600" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            Export CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('pdf')}
            disabled={!taxSummary || isExporting.pdf}
          >
            {isExporting.pdf ? (
              <div className="h-4 w-4 animate-spin rounded-full border-b-2 border-gray-600" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            Export PDF
          </Button>
        </div>
      </div>

      {isLoadingSummary ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-8 bg-gray-200 rounded w-1/2" />
            </Card>
          ))}
        </div>
      ) : taxSummary ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <DollarSign className="h-5 w-5 text-green-600" />
                <h3 className="font-semibold text-gray-900">Total Deductions</h3>
              </div>
              <p className="text-2xl font-bold text-green-600">
                {formatAmount(taxSummary.total_deductions)}
              </p>
            </Card>

            <Card className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <FileText className="h-5 w-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Categories</h3>
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {taxSummary.categories.length}
              </p>
            </Card>

            <Card className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <Receipt className="h-5 w-5 text-orange-600" />
                <h3 className="font-semibold text-gray-900">Transactions</h3>
              </div>
              <p className="text-2xl font-bold text-orange-600">
                {taxSummary.documentation_status.total_transactions}
              </p>
            </Card>

            <Card className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold text-gray-900">Documentation</h3>
              </div>
              <div className="flex items-center gap-2">
                <p className="text-2xl font-bold text-purple-600">
                  {calculateDocumentationProgress()}%
                </p>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <AlertTriangle className="h-4 w-4 text-gray-400 cursor-help" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Percentage of transactions with complete receipts and business purpose</p>
                  </TooltipContent>
                </Tooltip>
              </div>
            </Card>
          </div>

          {/* Documentation Status */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Receipt className="h-5 w-5" />
              Documentation Status
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-700 mb-3">Receipt Documentation</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>With Receipts</span>
                    <span>{taxSummary.documentation_status.with_receipts}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Missing Receipts</span>
                    <span className="text-red-600">{taxSummary.documentation_status.missing_receipts}</span>
                  </div>
                  <Progress
                    value={(taxSummary.documentation_status.with_receipts / taxSummary.documentation_status.total_transactions) * 100}
                    className="h-2"
                  />
                </div>
              </div>
              <div>
                <h4 className="font-medium text-gray-700 mb-3">Business Purpose</h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Complete</span>
                    <span>{taxSummary.documentation_status.complete_business_purpose}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Missing</span>
                    <span className="text-red-600">{taxSummary.documentation_status.missing_business_purpose}</span>
                  </div>
                  <Progress
                    value={(taxSummary.documentation_status.complete_business_purpose / taxSummary.documentation_status.total_transactions) * 100}
                    className="h-2"
                  />
                </div>
              </div>
            </div>
          </Card>

          {/* Categories List */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Deductions by Category
              </h3>
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Filter categories..."
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  className="w-48"
                />
              </div>
            </div>

            <ScrollArea className="max-h-96">
              <div className="space-y-3">
                {filteredCategories.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    {filterCategory ? 'No categories match your filter' : 'No categorized transactions found'}
                  </div>
                ) : (
                  filteredCategories.map((category) => (
                    <div
                      key={category.tax_category_id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h4 className="font-medium text-gray-900">
                            {category.category_name}
                          </h4>
                          <Badge variant="outline" className="text-xs">
                            Line {category.schedule_c_line}
                          </Badge>
                          <div className={cn(
                            'flex items-center gap-1 px-2 py-1 rounded text-xs border',
                            getDocumentationColor(category.documentation_status)
                          )}>
                            {getDocumentationIcon(category.documentation_status)}
                            <span className="capitalize">{category.documentation_status}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <span>{category.transaction_count} transactions</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-gray-900">
                          {formatAmount(category.total_amount)}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs"
                          >
                            <Eye className="h-3 w-3 mr-1" />
                            View Details
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </Card>

          {/* Quick Actions */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button variant="outline" className="h-auto p-4 text-left">
                <div>
                  <h4 className="font-medium">Review Missing Receipts</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    {taxSummary.documentation_status.missing_receipts} transactions need receipts
                  </p>
                </div>
              </Button>
              <Button variant="outline" className="h-auto p-4 text-left">
                <div>
                  <h4 className="font-medium">Complete Business Purpose</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    {taxSummary.documentation_status.missing_business_purpose} transactions need descriptions
                  </p>
                </div>
              </Button>
              <Button variant="outline" className="h-auto p-4 text-left">
                <div>
                  <h4 className="font-medium">Generate Schedule C</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Export data for tax filing
                  </p>
                </div>
              </Button>
            </div>
          </Card>
        </>
      ) : (
        <Card className="p-12 text-center">
          <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Tax Data</h3>
          <p className="text-gray-600">
            No tax categorization data found for {selectedYear}. Start categorizing transactions to see your tax summary.
          </p>
        </Card>
      )}
    </div>
  )
}