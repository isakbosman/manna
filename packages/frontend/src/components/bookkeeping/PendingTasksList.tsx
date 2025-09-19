import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  AlertCircle,
  CheckCircle,
  Clock,
  FileText,
  RefreshCw,
  ArrowRight,
  AlertTriangle
} from 'lucide-react'
import { format } from 'date-fns'
import { useToast } from '@/components/ui/use-toast'

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

interface PendingTasksListProps {
  tasks: PendingTask[]
  onTaskComplete: () => void
}

export function PendingTasksList({ tasks, onTaskComplete }: PendingTasksListProps) {
  const [processingTasks, setProcessingTasks] = useState<Set<string>>(new Set())
  const { toast } = useToast()

  const handleTaskAction = async (task: PendingTask) => {
    setProcessingTasks(prev => new Set(prev).add(task.id))

    try {
      // Handle different task types
      switch (task.task_type) {
        case 'reconciliation':
          await startReconciliation(task.account_id!)
          break
        case 'categorization':
          await reviewCategorizations(task)
          break
        case 'journal_entry':
          await reviewJournalEntry(task)
          break
        case 'period_closing':
          await initiatePeriodClosing(task)
          break
        default:
          toast({
            title: 'Task Started',
            description: `Processing ${task.title}`,
          })
      }

      onTaskComplete()
    } catch (error) {
      console.error('Error processing task:', error)
      toast({
        title: 'Error',
        description: `Failed to process ${task.title}`,
        variant: 'destructive',
      })
    } finally {
      setProcessingTasks(prev => {
        const next = new Set(prev)
        next.delete(task.id)
        return next
      })
    }
  }

  const startReconciliation = async (accountId: string) => {
    const response = await fetch('/api/v1/bookkeeping/reconciliation/start', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ account_id: accountId }),
    })

    if (!response.ok) {
      throw new Error('Failed to start reconciliation')
    }

    toast({
      title: 'Reconciliation Started',
      description: 'Account reconciliation has been initiated',
    })
  }

  const reviewCategorizations = async (task: PendingTask) => {
    toast({
      title: 'Opening Categorization Review',
      description: `${task.transaction_count} transactions to review`,
    })
    // Navigate to categorization review page
    window.location.href = '/bookkeeping/categorization'
  }

  const reviewJournalEntry = async (task: PendingTask) => {
    toast({
      title: 'Opening Journal Entry',
      description: 'Review and approve journal entry',
    })
    // Navigate to journal entry review
    window.location.href = `/bookkeeping/journal/${task.id}`
  }

  const initiatePeriodClosing = async (task: PendingTask) => {
    toast({
      title: 'Period Closing',
      description: 'Opening period closing workflow',
    })
    // Navigate to period closing
    window.location.href = '/bookkeeping/period-closing'
  }

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case 'medium':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      default:
        return <Clock className="h-4 w-4 text-blue-600" />
    }
  }

  const getPriorityBadge = (priority: string) => {
    const colors = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-blue-100 text-blue-800',
    }
    return (
      <Badge className={colors[priority as keyof typeof colors] || colors.low} variant="outline">
        {priority}
      </Badge>
    )
  }

  const getTaskTypeIcon = (type: string) => {
    switch (type) {
      case 'reconciliation':
        return <RefreshCw className="h-4 w-4" />
      case 'journal_entry':
        return <FileText className="h-4 w-4" />
      case 'categorization':
        return <AlertCircle className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  if (tasks.length === 0) {
    return (
      <div className="text-center py-8">
        <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
        <p className="text-lg font-medium">All caught up!</p>
        <p className="text-sm text-muted-foreground mt-1">
          No pending bookkeeping tasks at this time.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Priority</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Task</TableHead>
            <TableHead>Details</TableHead>
            <TableHead>Due Date</TableHead>
            <TableHead className="text-right">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tasks.map((task) => (
            <TableRow key={task.id}>
              <TableCell>
                <div className="flex items-center gap-2">
                  {getPriorityIcon(task.priority)}
                  {getPriorityBadge(task.priority)}
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  {getTaskTypeIcon(task.task_type)}
                  <span className="text-sm">{task.task_type}</span>
                </div>
              </TableCell>
              <TableCell>
                <div>
                  <p className="font-medium">{task.title}</p>
                  <p className="text-sm text-muted-foreground">{task.description}</p>
                </div>
              </TableCell>
              <TableCell>
                <div className="text-sm">
                  {task.account_name && (
                    <p>Account: {task.account_name}</p>
                  )}
                  {task.transaction_count && (
                    <p>{task.transaction_count} transactions</p>
                  )}
                  {task.amount && (
                    <p>${task.amount.toLocaleString()}</p>
                  )}
                </div>
              </TableCell>
              <TableCell>
                {task.due_date ? (
                  <span className="text-sm">
                    {format(new Date(task.due_date), 'MMM d, yyyy')}
                  </span>
                ) : (
                  <span className="text-sm text-muted-foreground">No deadline</span>
                )}
              </TableCell>
              <TableCell className="text-right">
                <Button
                  size="sm"
                  onClick={() => handleTaskAction(task)}
                  disabled={processingTasks.has(task.id)}
                >
                  {processingTasks.has(task.id) ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      Process
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </>
                  )}
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}