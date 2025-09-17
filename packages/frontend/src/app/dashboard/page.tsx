'use client'

import React, { useState, useMemo } from 'react'
import Link from 'next/link'
import { DashboardLayout } from '../../components/layout/dashboard-layout'
import { useAccounts } from '../../hooks/use-accounts'
import {
  useFinancialSummary,
  useRecentTransactions,
  useSpendingByCategory,
  useTransactionTrends,
  useCashFlow,
  useAlerts,
  useKPIs
} from '../../hooks/use-dashboard'
import { Loading } from '../../components/ui/loading'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '../../components/ui/card'
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
  RefreshCw,
  AlertCircle,
  Package,
  FileText,
  TrendingUpIcon
} from 'lucide-react'

// Import dashboard components
import {
  KPIWidget,
  FinancialSummaryCard,
  RecentTransactionsList,
  AccountBalanceCards,
  DateRangeSelector,
  AlertsNotificationsPanel,
  type DateRange,
} from '../../components/dashboard'

// Import chart components
import {
  SpendingByCategoryChart,
  TransactionTrendsChart,
  CashFlowChart
} from '../../components/charts'

// Import date utilities
import { subDays, format } from 'date-fns'

// Empty state component
function EmptyState({
  icon: Icon,
  title,
  description,
  actionText,
  onAction
}: {
  icon: any
  title: string
  description: string
  actionText?: string
  onAction?: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Icon className="h-12 w-12 text-gray-400 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 mb-4 max-w-sm">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          {actionText}
        </button>
      )}
    </div>
  )
}

function DashboardPage() {
  const {
    accounts,
    totalBalance,
    activeAccounts,
    isLoading: accountsLoading,
    error: accountsError,
    refetch: refetchAccounts
  } = useAccounts()

  // Fetch dashboard data from API
  const { data: financialSummary, isLoading: summaryLoading, error: summaryError } = useFinancialSummary()
  const { data: recentTransactions = [], isLoading: transactionsLoading } = useRecentTransactions(10)
  const { data: spendingData = [], isLoading: spendingLoading } = useSpendingByCategory(30)
  const { data: trendsData = [], isLoading: trendsLoading } = useTransactionTrends(30)
  const { data: cashFlowData = [], isLoading: cashFlowLoading } = useCashFlow(6)
  const { data: alerts = [], isLoading: alertsLoading } = useAlerts()
  const { data: kpis, isLoading: kpisLoading } = useKPIs()

  // State for date range selector
  const [selectedDateRange, setSelectedDateRange] = useState<DateRange>({
    start: subDays(new Date(), 29),
    end: new Date(),
    label: 'Last 30 days'
  })

  const [isRefreshing, setIsRefreshing] = useState(false)

  // Handle refresh functionality
  const handleRefresh = async () => {
    setIsRefreshing(true)
    await Promise.all([
      refetchAccounts(),
      // Refetch all dashboard data
    ])
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  // Define KPI widgets data based on API data
  const kpiWidgets = useMemo(() => {
    if (!kpis) return []

    return [
      {
        title: 'Total Balance',
        value: kpis.totalBalance || 0,
        format: 'currency' as const,
        icon: DollarSign,
        description: 'Total across all accounts',
        color: kpis.totalBalance > 0 ? 'success' as const : 'warning' as const
      },
      {
        title: 'Monthly Income',
        value: kpis.monthlyIncome || 0,
        format: 'currency' as const,
        icon: TrendingUp,
        description: 'Income this month'
      },
      {
        title: 'Monthly Expenses',
        value: kpis.monthlyExpenses || 0,
        format: 'currency' as const,
        icon: TrendingDown,
        description: 'Expenses this month'
      },
      {
        title: 'Savings Rate',
        value: kpis.savingsRate || 0,
        format: 'percentage' as const,
        icon: PiggyBank,
        description: 'Percentage of income saved',
        color: kpis.savingsRate >= 20 ? 'success' as const : 'warning' as const
      },
      {
        title: 'Net Cash Flow',
        value: (kpis.monthlyIncome || 0) - (kpis.monthlyExpenses || 0),
        format: 'currency' as const,
        icon: Activity,
        description: 'Income minus expenses'
      },
      {
        title: 'Connected Accounts',
        value: kpis.accountCount || 0,
        format: 'number' as const,
        icon: CreditCard,
        description: 'Active account connections',
        color: 'info' as const
      }
    ]
  }, [kpis])

  const isLoading = accountsLoading || summaryLoading || kpisLoading

  if (isLoading && !financialSummary && !kpis) {
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

  // Check if we have any data at all
  const hasNoData = !accounts?.length && !recentTransactions?.length

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

        {/* Error messages */}
        {(accountsError || summaryError) && (
          <div className="p-4 bg-red-50 border-l-4 border-red-400 rounded-md">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-700">
                  <strong>Error loading data:</strong> {accountsError?.message || summaryError?.message}
                </p>
                <button
                  onClick={handleRefresh}
                  className="mt-2 text-sm text-red-700 underline hover:text-red-800"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        )}

        {/* No Data State */}
        {hasNoData ? (
          <Card className="col-span-full">
            <CardContent className="py-12">
              <EmptyState
                icon={Package}
                title="No Financial Data Yet"
                description="Connect your first account to start tracking your finances and see insights here."
                actionText="Connect Account"
                onAction={() => window.location.href = '/accounts'}
              />
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Financial Summary Card */}
            {financialSummary ? (
              <FinancialSummaryCard
                data={financialSummary}
                isLoading={summaryLoading || isRefreshing}
                className="col-span-full"
              />
            ) : (
              <Card>
                <CardContent className="py-8">
                  <EmptyState
                    icon={FileText}
                    title="No Financial Summary"
                    description="Financial summary will appear here once you have account data."
                  />
                </CardContent>
              </Card>
            )}

            {/* KPI Widgets Grid */}
            {kpiWidgets.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                {kpiWidgets.map((widget, index) => (
                  <KPIWidget
                    key={index}
                    {...widget}
                    isLoading={kpisLoading || isRefreshing}
                    size="md"
                  />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                  <Card key={i} className="animate-pulse">
                    <CardContent className="h-32" />
                  </Card>
                ))}
              </div>
            )}

            {/* Account Balance Cards */}
            {accounts.length > 0 ? (
              <AccountBalanceCards
                accounts={accounts}
                isLoading={accountsLoading || isRefreshing}
                onAccountClick={(account) => console.log('Account clicked:', account)}
                onRefresh={handleRefresh}
              />
            ) : (
              <Card>
                <CardContent className="py-8">
                  <EmptyState
                    icon={CreditCard}
                    title="No Connected Accounts"
                    description="Connect your bank accounts to see balances here."
                    actionText="Connect Account"
                    onAction={() => window.location.href = '/accounts'}
                  />
                </CardContent>
              </Card>
            )}

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {spendingData.length > 0 ? (
                <SpendingByCategoryChart
                  data={spendingData}
                  isLoading={spendingLoading || isRefreshing}
                  className="col-span-1"
                />
              ) : (
                <Card>
                  <CardHeader>
                    <CardTitle>Spending by Category</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <EmptyState
                      icon={BarChart3}
                      title="No Spending Data"
                      description="Your spending breakdown will appear here once you have transactions."
                    />
                  </CardContent>
                </Card>
              )}

              {trendsData.length > 0 ? (
                <TransactionTrendsChart
                  data={trendsData}
                  isLoading={trendsLoading || isRefreshing}
                  dateRange={selectedDateRange.label}
                  className="col-span-1"
                />
              ) : (
                <Card>
                  <CardHeader>
                    <CardTitle>Transaction Trends</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <EmptyState
                      icon={TrendingUpIcon}
                      title="No Trend Data"
                      description="Transaction trends will appear here once you have transaction history."
                    />
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Cash Flow Chart - Full Width */}
            {cashFlowData.length > 0 ? (
              <CashFlowChart
                data={cashFlowData}
                isLoading={cashFlowLoading || isRefreshing}
                showRunningBalance={true}
              />
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>Cash Flow Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <EmptyState
                    icon={Activity}
                    title="No Cash Flow Data"
                    description="Monthly cash flow analysis will appear here once you have transaction history."
                  />
                </CardContent>
              </Card>
            )}

            {/* Bottom Section - Transactions and Alerts */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {recentTransactions.length > 0 ? (
                <RecentTransactionsList
                  transactions={recentTransactions}
                  isLoading={transactionsLoading || isRefreshing}
                  className="lg:col-span-2"
                  maxItems={8}
                  showFilters={true}
                  onTransactionClick={(transaction) => console.log('Transaction clicked:', transaction)}
                  onViewAll={() => window.location.href = '/transactions'}
                />
              ) : (
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>Recent Transactions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <EmptyState
                      icon={FileText}
                      title="No Transactions Yet"
                      description="Your recent transactions will appear here once you connect an account."
                    />
                  </CardContent>
                </Card>
              )}

              <AlertsNotificationsPanel
                alerts={alerts}
                isLoading={alertsLoading || isRefreshing}
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
                    <span className="font-medium">View Transactions</span>
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
          </>
        )}
      </div>
    </DashboardLayout>
  )
}

// Export unprotected version for local development
export default DashboardPage