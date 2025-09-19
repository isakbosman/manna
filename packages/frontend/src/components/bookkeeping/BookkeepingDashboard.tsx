'use client'

import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  FileText,
  RefreshCw,
  BookOpen,
  Calendar,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  Database,
  Brain
} from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { PendingTasksList } from './PendingTasksList'
import { ReconciliationPanel } from './ReconciliationPanel'
import { JournalEntriesTable } from './JournalEntriesTable'
import { PeriodClosingModal } from './PeriodClosingModal'
import { HealthIndicators } from './HealthIndicators'

interface BookkeepingHealth {
  status: 'healthy' | 'warning' | 'behind' | 'critical'
  unreconciled_accounts: number
  pending_journal_entries: number
  days_behind_reconciliation: number
  last_reconciliation_date: string | null
  current_period_status: string
  ml_categorization_accuracy: number
  pending_categorizations: number
}

interface PendingTask {
  id: string
  task_type: string
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  due_date: string | null
  account_id?: string
  account_name?: string
  transaction_count?: number
  amount?: number
}

export function BookkeepingDashboard() {
  const [health, setHealth] = useState<BookkeepingHealth | null>(null)
  const [pendingTasks, setPendingTasks] = useState<PendingTask[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [refreshing, setRefreshing] = useState(false)
  const [showPeriodClosing, setShowPeriodClosing] = useState(false)
  const { toast } = useToast()

  const fetchBookkeepingData = async () => {
    try {
      setRefreshing(true)

      // Fetch health status
      const healthResponse = await fetch('/api/v1/bookkeeping/health', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (healthResponse.ok) {
        const healthData = await healthResponse.json()
        setHealth(healthData)
      }

      // Fetch pending tasks
      const tasksResponse = await fetch('/api/v1/bookkeeping/pending-tasks', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (tasksResponse.ok) {
        const tasksData = await tasksResponse.json()
        setPendingTasks(tasksData.tasks || [])
      }
    } catch (error) {
      console.error('Error fetching bookkeeping data:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch bookkeeping data',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchBookkeepingData()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100'
      case 'warning':
        return 'text-yellow-600 bg-yellow-100'
      case 'behind':
        return 'text-orange-600 bg-orange-100'
      case 'critical':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getHighPriorityTasksCount = () => {
    return pendingTasks.filter(task => task.priority === 'high').length
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading bookkeeping data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BookOpen className="h-8 w-8 text-primary" />
            Bookkeeping & Reconciliation
          </h1>
          <p className="text-muted-foreground mt-1">
            Automated double-entry bookkeeping with ML-powered categorization
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => fetchBookkeepingData()}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setShowPeriodClosing(true)}>
            <Calendar className="h-4 w-4 mr-2" />
            Close Period
          </Button>
        </div>
      </div>

      {/* Critical Alerts */}
      {health && health.status === 'critical' && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Critical Bookkeeping Issues</AlertTitle>
          <AlertDescription>
            Your bookkeeping is {health.days_behind_reconciliation} days behind.
            {health.unreconciled_accounts} accounts need reconciliation.
            Immediate attention required to maintain accurate financial records.
          </AlertDescription>
        </Alert>
      )}

      {/* High Priority Tasks Alert */}
      {getHighPriorityTasksCount() > 0 && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>High Priority Tasks</AlertTitle>
          <AlertDescription>
            You have {getHighPriorityTasksCount()} high priority bookkeeping tasks that need attention.
          </AlertDescription>
        </Alert>
      )}

      {/* Health Status Overview */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle>Bookkeeping Health Status</CardTitle>
            <CardDescription>Overall system health and key metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Badge className={getStatusColor(health.status)} variant="outline">
                  {health.status.toUpperCase()}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Last reconciliation: {health.last_reconciliation_date || 'Never'}
                </span>
              </div>
              <div className="text-sm text-muted-foreground">
                Current Period: {health.current_period_status}
              </div>
            </div>
            <HealthIndicators health={health} />
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="reconciliation">Reconciliation</TabsTrigger>
          <TabsTrigger value="journal">Journal Entries</TabsTrigger>
          <TabsTrigger value="automation">Automation</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Pending Tasks */}
          <Card>
            <CardHeader>
              <CardTitle>Pending Tasks</CardTitle>
              <CardDescription>
                Tasks requiring manual review or action
              </CardDescription>
            </CardHeader>
            <CardContent>
              <PendingTasksList
                tasks={pendingTasks}
                onTaskComplete={fetchBookkeepingData}
              />
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Common bookkeeping operations</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Button variant="outline" className="h-20 flex-col">
                <FileText className="h-5 w-5 mb-2" />
                <span className="text-xs">Create Entry</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col">
                <RefreshCw className="h-5 w-5 mb-2" />
                <span className="text-xs">Reconcile All</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col">
                <Brain className="h-5 w-5 mb-2" />
                <span className="text-xs">Train ML</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col">
                <Database className="h-5 w-5 mb-2" />
                <span className="text-xs">Export Data</span>
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reconciliation">
          <ReconciliationPanel onReconciliationComplete={fetchBookkeepingData} />
        </TabsContent>

        <TabsContent value="journal">
          <JournalEntriesTable />
        </TabsContent>

        <TabsContent value="automation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>ML Categorization</CardTitle>
              <CardDescription>
                Machine learning model performance and training
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">Accuracy</span>
                  <span className="text-sm text-muted-foreground">
                    {health?.ml_categorization_accuracy || 0}%
                  </span>
                </div>
                <Progress value={health?.ml_categorization_accuracy || 0} />
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <p className="font-medium">Pending Categorizations</p>
                  <p className="text-sm text-muted-foreground">
                    {health?.pending_categorizations || 0} transactions need review
                  </p>
                </div>
                <Button>
                  Review
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </div>

              <Button variant="outline" className="w-full">
                <Brain className="h-4 w-4 mr-2" />
                Retrain Model
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Automation Rules</CardTitle>
              <CardDescription>
                Configure automated bookkeeping rules
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Button variant="outline" className="w-full justify-start">
                  <FileText className="h-4 w-4 mr-2" />
                  Manage Journal Entry Templates
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Configure Accrual Rules
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <DollarSign className="h-4 w-4 mr-2" />
                  Set Categorization Rules
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Period Closing Modal */}
      {showPeriodClosing && (
        <PeriodClosingModal
          isOpen={showPeriodClosing}
          onClose={() => setShowPeriodClosing(false)}
          onPeriodClosed={fetchBookkeepingData}
        />
      )}
    </div>
  )
}