'use client'

import React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Calculator,
  FileText,
  TrendingUp,
  Building,
  Download,
  Plus,
  Filter,
  Calendar,
} from 'lucide-react'
import { Card } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Badge } from '../../components/ui/badge'
import { Select } from '../../components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import {
  TaxSummaryDashboard,
  ChartOfAccountsManager,
} from '../../components/tax'
import { TaxEnhancedTransactionsTable } from '../../components/transactions/tax-enhanced-transactions-table'
import { transactionsApi, accountsApi, categoriesApi } from '../../lib/api'
import { taxApi } from '../../lib/api/tax'

export default function TaxPage() {
  const [selectedTab, setSelectedTab] = React.useState<string>('dashboard')
  const [selectedYear, setSelectedYear] = React.useState<number>(new Date().getFullYear())

  // Load data
  const { data: transactions = [], isLoading: isLoadingTransactions } = useQuery({
    queryKey: ['transactions'],
    queryFn: transactionsApi.getTransactions,
  })

  const { data: accounts = [] } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.getAccounts,
  })

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: categoriesApi.getCategories,
  })

  const { data: taxSummary } = useQuery({
    queryKey: ['tax-summary', selectedYear],
    queryFn: () => taxApi.getTaxSummary(selectedYear),
  })

  // Filter transactions for current year
  const currentYearTransactions = React.useMemo(() => {
    return transactions.filter(transaction => {
      const transactionYear = new Date(transaction.date).getFullYear()
      return transactionYear === selectedYear
    })
  }, [transactions, selectedYear])

  // Calculate basic stats
  const stats = React.useMemo(() => {
    const totalTransactions = currentYearTransactions.length
    const categorizedTransactions = currentYearTransactions.filter(t => t.tax_categorization).length
    const totalExpenses = currentYearTransactions
      .filter(t => t.amount < 0)
      .reduce((sum, t) => sum + Math.abs(t.amount), 0)
    const totalDeductions = taxSummary?.total_deductions || 0

    return {
      totalTransactions,
      categorizedTransactions,
      categorizationPercentage: totalTransactions > 0 ? Math.round((categorizedTransactions / totalTransactions) * 100) : 0,
      totalExpenses,
      totalDeductions,
      potentialSavings: totalDeductions * 0.25, // Rough estimate at 25% tax rate
    }
  }, [currentYearTransactions, taxSummary])

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const generateAvailableYears = () => {
    const currentYear = new Date().getFullYear()
    const years = []
    for (let i = 0; i < 5; i++) {
      years.push(currentYear - i)
    }
    return years
  }

  const handleTransactionUpdate = (updatedTransaction: any) => {
    // In a real app, you'd update the transactions query data
    console.log('Transaction updated:', updatedTransaction)
  }

  const handleTransactionDelete = (transactionId: string) => {
    // In a real app, you'd remove the transaction
    console.log('Transaction deleted:', transactionId)
  }

  const handleTransactionSelect = (transaction: any) => {
    // In a real app, you'd open a transaction detail modal
    console.log('Transaction selected:', transaction)
  }

  const handleRowSelectionChange = (selectedTransactions: any[]) => {
    console.log('Selected transactions:', selectedTransactions)
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Tax Management</h1>
          <p className="text-gray-600 mt-1">
            Categorize transactions and manage tax deductions for better financial reporting.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              {generateAvailableYears().map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export Tax Data
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-2">
            <FileText className="h-5 w-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Transactions</h3>
          </div>
          <p className="text-2xl font-bold text-blue-600">
            {stats.totalTransactions}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            {stats.categorizedTransactions} categorized ({stats.categorizationPercentage}%)
          </p>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="h-5 w-5 text-red-600" />
            <h3 className="font-semibold text-gray-900">Total Expenses</h3>
          </div>
          <p className="text-2xl font-bold text-red-600">
            {formatAmount(stats.totalExpenses)}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            Business expenses for {selectedYear}
          </p>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-3 mb-2">
            <Calculator className="h-5 w-5 text-green-600" />
            <h3 className="font-semibold text-gray-900">Tax Deductions</h3>
          </div>
          <p className="text-2xl font-bold text-green-600">
            {formatAmount(stats.totalDeductions)}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            Approved business deductions
          </p>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-3 mb-2">
            <Building className="h-5 w-5 text-purple-600" />
            <h3 className="font-semibold text-gray-900">Potential Savings</h3>
          </div>
          <p className="text-2xl font-bold text-purple-600">
            {formatAmount(stats.potentialSavings)}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            Est. tax savings (25% rate)
          </p>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="dashboard">Tax Dashboard</TabsTrigger>
          <TabsTrigger value="transactions">Categorize Transactions</TabsTrigger>
          <TabsTrigger value="accounts">Chart of Accounts</TabsTrigger>
          <TabsTrigger value="reports">Tax Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="space-y-6">
          <TaxSummaryDashboard />
        </TabsContent>

        <TabsContent value="transactions" className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Transaction Categorization</h2>
                <p className="text-gray-600 mt-1">
                  Review and categorize transactions for tax purposes. Focus on business expenses for maximum deductions.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline">
                  {stats.categorizationPercentage}% Categorized
                </Badge>
                <Button variant="outline" size="sm">
                  <Filter className="h-4 w-4 mr-1" />
                  Filter Uncategorized
                </Button>
              </div>
            </div>

            <TaxEnhancedTransactionsTable
              transactions={currentYearTransactions}
              accounts={accounts}
              categories={categories}
              isLoading={isLoadingTransactions}
              onTransactionSelect={handleTransactionSelect}
              onTransactionUpdate={handleTransactionUpdate}
              onTransactionDelete={handleTransactionDelete}
              onRowSelectionChange={handleRowSelectionChange}
            />
          </Card>
        </TabsContent>

        <TabsContent value="accounts" className="space-y-6">
          <ChartOfAccountsManager />
        </TabsContent>

        <TabsContent value="reports" className="space-y-6">
          <Card className="p-8 text-center">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Tax Reports</h3>
            <p className="text-gray-600 mb-6">
              Generate comprehensive tax reports including Schedule C, profit & loss statements, and deduction summaries.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
              <Button variant="outline" className="h-auto p-4">
                <div className="text-center">
                  <h4 className="font-medium">Schedule C</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Export business income and expenses
                  </p>
                </div>
              </Button>
              <Button variant="outline" className="h-auto p-4">
                <div className="text-center">
                  <h4 className="font-medium">P&L Statement</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Profit and loss for tax year
                  </p>
                </div>
              </Button>
              <Button variant="outline" className="h-auto p-4">
                <div className="text-center">
                  <h4 className="font-medium">Deduction Summary</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Detailed breakdown by category
                  </p>
                </div>
              </Button>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}