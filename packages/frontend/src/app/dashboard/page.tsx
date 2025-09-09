'use client'

import React, { useState, useMemo } from 'react'
import Link from 'next/link'
import { DashboardLayout } from '@/components/layout/dashboard-layout'
import { withAuth } from '@/components/providers/auth-provider'
import { useAccounts } from '@/hooks/use-accounts'
import { Loading } from '@/components/ui/loading'
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card'
import { formatCurrency, calculateSavingsRate, calculateFinancialHealthScore, formatPercentage, calculatePercentageChange } from '@/lib/utils'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  CreditCard, 
  Activity, 
  Users,
  PiggyBank,
  Target,
  BarChart3,
  RefreshCw
} from 'lucide-react'

// Import new dashboard components
import {
  KPIWidget,
  FinancialSummaryCard,
  RecentTransactionsList,
  AccountBalanceCards,
  DateRangeSelector,
  AlertsNotificationsPanel,
  type DateRange,
  type Transaction,
  type Alert
} from '@/components/dashboard'

// Import chart components
import {
  SpendingByCategoryChart,
  TransactionTrendsChart,
  CashFlowChart
} from '@/components/charts'

// Import date utilities
import { subDays, format } from 'date-fns'

// Mock data for comprehensive financial dashboard
const mockFinancialStats = {
  monthlyIncome: 8750.00,
  monthlyExpenses: 6234.75,
  previousMonthIncome: 8100.00,
  previousMonthExpenses: 6800.00,
  incomeChange: 8.2,
  expenseChange: -3.1,
  savingsGoal: 2000.00,
  currentSavings: 1650.00
}

// Mock transaction data
const mockTransactions: Transaction[] = [
  {
    id: '1',
    date: '2024-09-08',
    description: 'Salary Deposit',
    amount: 5000.00,
    category: 'Income',
    account: 'Chase Checking',
    merchant: 'Employer Direct Deposit',
    type: 'credit'
  },
  {
    id: '2',
    date: '2024-09-07',
    description: 'Grocery Store',
    amount: -156.78,
    category: 'Food & Dining',
    account: 'Chase Checking',
    merchant: 'Whole Foods Market',
    type: 'debit'
  },
  {
    id: '3',
    date: '2024-09-06',
    description: 'Gas Station',
    amount: -45.32,
    category: 'Transportation',
    account: 'Chase Credit',
    merchant: 'Shell',
    type: 'debit'
  },
  {
    id: '4',
    date: '2024-09-05',
    description: 'Rent Payment',
    amount: -1800.00,
    category: 'Housing',
    account: 'Chase Checking',
    merchant: 'Property Management Co',
    type: 'debit'
  },
  {
    id: '5',
    date: '2024-09-04',
    description: 'Freelance Payment',
    amount: 750.00,
    category: 'Income',
    account: 'PayPal',
    merchant: 'Client ABC Inc',
    type: 'credit'
  },
  {
    id: '6',
    date: '2024-09-03',
    description: 'Coffee Shop',
    amount: -12.50,
    category: 'Food & Dining',
    account: 'Chase Credit',
    merchant: 'Starbucks',
    type: 'debit'
  },
  {
    id: '7',
    date: '2024-09-02',
    description: 'Utilities Payment',
    amount: -185.43,
    category: 'Utilities',
    account: 'Chase Checking',
    merchant: 'Electric Company',
    type: 'debit'
  },
  {
    id: '8',
    date: '2024-09-01',
    description: 'Investment Transfer',
    amount: -500.00,
    category: 'Transfer',
    account: 'Chase Checking',
    merchant: 'Vanguard',
    type: 'debit'
  }
]

// Mock spending by category data
const mockSpendingData = [
  { name: 'Housing', value: 1800, color: '#ef4444' },
  { name: 'Food & Dining', value: 580, color: '#f97316' },
  { name: 'Transportation', value: 320, color: '#eab308' },
  { name: 'Utilities', value: 285, color: '#22c55e' },
  { name: 'Entertainment', value: 180, color: '#3b82f6' },
  { name: 'Shopping', value: 150, color: '#8b5cf6' },
  { name: 'Healthcare', value: 120, color: '#ec4899' }
]

// Mock trend data for charts
const mockTrendData = [
  { date: '2024-08-01', income: 8100, expenses: -6800, netFlow: 1300 },
  { date: '2024-08-02', income: 0, expenses: -280, netFlow: -280 },
  { date: '2024-08-03', income: 750, expenses: -150, netFlow: 600 },
  { date: '2024-08-04', income: 0, expenses: -90, netFlow: -90 },
  { date: '2024-08-05', income: 0, expenses: -1800, netFlow: -1800 },
  { date: '2024-08-06', income: 0, expenses: -45, netFlow: -45 },
  { date: '2024-08-07', income: 0, expenses: -157, netFlow: -157 },
  { date: '2024-08-08', income: 5000, expenses: 0, netFlow: 5000 }
]

// Mock cash flow data
const mockCashFlowData = [
  { month: 'Jun', income: 7800, expenses: -6200, netFlow: 1600, runningBalance: 15600 },
  { month: 'Jul', income: 8100, expenses: -6800, netFlow: 1300, runningBalance: 16900 },
  { month: 'Aug', income: 8750, expenses: -6234, netFlow: 2516, runningBalance: 19416 },
]

// Mock alerts data
const mockAlerts: Alert[] = [
  {
    id: '1',
    type: 'warning',
    title: 'High Credit Card Utilization',
    message: 'Your credit utilization is at 85% on Chase Freedom card',
    category: 'account',
    priority: 'high',
    created_at: '2024-09-08T10:00:00Z',
    data: {
      account_name: 'Chase Freedom',
      utilization: 0.85,
      amount: 4250
    },
    actionable: true
  },
  {
    id: '2',
    type: 'info',
    title: 'Monthly Budget Update',
    message: 'You\'re 82% through your monthly dining budget',
    category: 'budget',
    priority: 'medium',
    created_at: '2024-09-07T15:30:00Z',
    data: {
      amount: 580
    }
  },
  {
    id: '3',
    type: 'success',
    title: 'Savings Goal Progress',
    message: 'Great job! You\'re ahead of your savings goal this month',
    category: 'budget',
    priority: 'low',
    created_at: '2024-09-06T09:00:00Z',
    data: {
      amount: 1650
    }
  }
]

function DashboardPage() {
  const { 
    accounts,
    totalBalance,
    activeAccounts,
    isLoading: accountsLoading,
    error: accountsError,
    refetch
  } = useAccounts()

  // State for date range selector
  const [selectedDateRange, setSelectedDateRange] = useState<DateRange>({
    start: subDays(new Date(), 29),
    end: new Date(),
    label: 'Last 30 days'
  })

  const [isRefreshing, setIsRefreshing] = useState(false)

  // Calculate comprehensive financial metrics
  const financialMetrics = useMemo(() => {
    const savingsRate = calculateSavingsRate(
      mockFinancialStats.monthlyIncome,
      mockFinancialStats.monthlyExpenses
    )
    
    const incomeChange = calculatePercentageChange(
      mockFinancialStats.monthlyIncome,
      mockFinancialStats.previousMonthIncome
    )
    
    const expenseChange = calculatePercentageChange(
      mockFinancialStats.monthlyExpenses,
      mockFinancialStats.previousMonthExpenses
    )
    
    const netWorth = totalBalance // Using actual account data
    const monthlyNetFlow = mockFinancialStats.monthlyIncome - mockFinancialStats.monthlyExpenses
    
    const financialHealthScore = calculateFinancialHealthScore({
      savingsRate,
      debtToIncomeRatio: 25, // Mock value
      creditUtilization: 45, // Mock value
      emergencyFundMonths: 3.5 // Mock value
    })

    return {
      savingsRate,
      incomeChange,
      expenseChange,
      netWorth,
      monthlyNetFlow,
      financialHealthScore,
      avgDailySpending: mockFinancialStats.monthlyExpenses / 30
    }
  }, [totalBalance, mockFinancialStats])

  // Mock financial summary data
  const financialSummaryData = {
    totalAssets: Math.max(0, totalBalance + 50000), // Add mock investments
    totalLiabilities: Math.max(0, -totalBalance + 15000), // Mock liabilities
    netWorth: financialMetrics.netWorth,
    liquidAssets: totalBalance,
    monthlyChange: {
      assets: 2500,
      liabilities: -500,
      netWorth: 3000
    },
    breakdown: {
      checking: accounts.filter(a => a.type === 'checking').reduce((sum, a) => sum + a.balance_current, 0),
      savings: accounts.filter(a => a.type === 'savings').reduce((sum, a) => sum + a.balance_current, 0),
      investments: 35000, // Mock
      creditCards: accounts.filter(a => a.type === 'credit').reduce((sum, a) => sum + a.balance_current, 0),
      loans: -12000, // Mock
      other: 0
    }
  }

  // Handle refresh functionality
  const handleRefresh = async () => {
    setIsRefreshing(true)
    await refetch()
    // Simulate additional data refresh
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  // Define KPI widgets data
  const kpiWidgets = [
    {
      title: 'Net Worth',
      value: financialMetrics.netWorth,
      format: 'currency' as const,
      change: {
        value: 3000,
        type: 'currency' as const,
        period: 'this month',
        isPositive: true
      },
      icon: DollarSign,
      description: 'Total assets minus liabilities',
      color: 'success' as const
    },
    {
      title: 'Monthly Cash Flow',
      value: financialMetrics.monthlyNetFlow,
      format: 'currency' as const,
      change: {
        value: financialMetrics.incomeChange,
        type: 'percentage' as const,
        period: 'vs last month'
      },
      icon: TrendingUp,
      description: 'Income minus expenses'
    },
    {
      title: 'Savings Rate',
      value: financialMetrics.savingsRate,
      format: 'percentage' as const,
      icon: PiggyBank,
      description: 'Percentage of income saved',
      target: 20,
      color: financialMetrics.savingsRate >= 15 ? 'success' as const : 'warning' as const
    },
    {
      title: 'Daily Spending Avg',
      value: financialMetrics.avgDailySpending,
      format: 'currency' as const,
      icon: BarChart3,
      description: 'Average daily expenses',
      target: 180
    },
    {
      title: 'Financial Health',
      value: financialMetrics.financialHealthScore,
      format: 'number' as const,
      icon: Target,
      description: 'Overall financial wellness score',
      color: financialMetrics.financialHealthScore >= 80 ? 'success' as const : 
             financialMetrics.financialHealthScore >= 60 ? 'warning' as const : 'error' as const
    },
    {
      title: 'Connected Accounts',
      value: accounts.length,
      format: 'number' as const,
      icon: CreditCard,
      description: `${activeAccounts.length} active accounts`,
      color: 'info' as const
    }
  ]

  // Use real account data for balance display
  const balanceAccounts = accounts

  if (accountsLoading) {
    return (
      <DashboardLayout
        title="Dashboard"
        description="Welcome back! Here's an overview of your financial data."
      >
        <div className="flex items-center justify-center py-12">
          <Loading size="lg" />
          <span className="ml-2 text-lg">Loading your financial dashboard...</span>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout
      title="Financial Dashboard"
      description="Welcome back! Here's your comprehensive financial overview."
    >
      <div className="space-y-6">
        {/* Header with Date Range and Refresh */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Financial Overview</h1>
            <p className="text-sm text-neutral-600 mt-1">
              {format(new Date(), 'EEEE, MMMM dd, yyyy')}
            </p>
          </div>
          <div className="flex items-center space-x-3 mt-4 sm:mt-0">
            <DateRangeSelector
              selectedRange={selectedDateRange}
              onRangeChange={setSelectedDateRange}
              disabled={isRefreshing}
            />
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="inline-flex items-center px-3 py-2 border border-neutral-300 shadow-sm text-sm leading-4 font-medium rounded-md text-neutral-700 bg-white hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {accountsError && (
          <div className="p-4 bg-error-50 border-l-4 border-error-400 rounded-md">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-error-700">
                  <strong>Error loading account data:</strong> {accountsError.message}
                </p>
                <button 
                  onClick={handleRefresh} 
                  className="mt-2 text-sm text-error-700 underline hover:text-error-800"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Financial Summary Card */}
        <FinancialSummaryCard
          data={financialSummaryData}
          isLoading={accountsLoading || isRefreshing}
          className="col-span-full"
        />

        {/* KPI Widgets Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {kpiWidgets.map((widget, index) => (
            <KPIWidget
              key={index}
              {...widget}
              isLoading={accountsLoading || isRefreshing}
              size="md"
            />
          ))}
        </div>

        {/* Account Balance Cards */}
        <AccountBalanceCards
          accounts={balanceAccounts}
          isLoading={accountsLoading || isRefreshing}
          onAccountClick={(account) => console.log('Account clicked:', account)}
          onRefresh={handleRefresh}
        />

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SpendingByCategoryChart
            data={mockSpendingData}
            isLoading={accountsLoading || isRefreshing}
            className="col-span-1"
          />
          <TransactionTrendsChart
            data={mockTrendData}
            isLoading={accountsLoading || isRefreshing}
            dateRange={selectedDateRange.label}
            className="col-span-1"
          />
        </div>

        {/* Cash Flow Chart - Full Width */}
        <CashFlowChart
          data={mockCashFlowData}
          isLoading={accountsLoading || isRefreshing}
          showRunningBalance={true}
        />

        {/* Bottom Section - Transactions and Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <RecentTransactionsList
            transactions={mockTransactions}
            isLoading={accountsLoading || isRefreshing}
            className="lg:col-span-2"
            maxItems={8}
            showFilters={true}
            onTransactionClick={(transaction) => console.log('Transaction clicked:', transaction)}
            onViewAll={() => console.log('View all transactions')}
          />
          
          <AlertsNotificationsPanel
            alerts={mockAlerts}
            isLoading={accountsLoading || isRefreshing}
            className="lg:col-span-1"
            maxItems={5}
            onAlertClick={(alert) => console.log('Alert clicked:', alert)}
            onDismissAlert={(alertId) => console.log('Dismiss alert:', alertId)}
            onViewAll={() => console.log('View all alerts')}
          />
        </div>

        {/* Quick Actions Card */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common financial tasks and shortcuts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <Link href="/transactions" className="flex items-center justify-center space-x-2 rounded-lg border border-neutral-200 p-4 text-center text-sm hover:bg-neutral-50 transition-colors group">
                <Activity className="h-5 w-5 text-neutral-600 group-hover:text-primary-600" />
                <span className="font-medium">Sync Transactions</span>
              </Link>
              <Link href="/accounts" className="flex items-center justify-center space-x-2 rounded-lg border border-neutral-200 p-4 text-center text-sm hover:bg-neutral-50 transition-colors group">
                <CreditCard className="h-5 w-5 text-neutral-600 group-hover:text-primary-600" />
                <span className="font-medium">Connect Account</span>
              </Link>
              <Link href="/reports" className="flex items-center justify-center space-x-2 rounded-lg border border-neutral-200 p-4 text-center text-sm hover:bg-neutral-50 transition-colors group">
                <BarChart3 className="h-5 w-5 text-neutral-600 group-hover:text-primary-600" />
                <span className="font-medium">Generate Report</span>
              </Link>
              <Link href="/budgets" className="flex items-center justify-center space-x-2 rounded-lg border border-neutral-200 p-4 text-center text-sm hover:bg-neutral-50 transition-colors group">
                <Target className="h-5 w-5 text-neutral-600 group-hover:text-primary-600" />
                <span className="font-medium">Manage Budgets</span>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}

// Export protected version
export default withAuth(DashboardPage)