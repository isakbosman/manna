'use client'

import React, { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  AlertCircle,
  CheckCircle2,
  Calendar,
  FileText,
  RefreshCw,
  AlertTriangle,
  ArrowRight
} from 'lucide-react'
import { format } from 'date-fns'
import { useToast } from '@/components/ui/use-toast'

interface PeriodClosingModalProps {
  isOpen: boolean
  onClose: () => void
  onPeriodClosed: () => void
}

interface ClosingChecklistItem {
  id: string
  task: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  required: boolean
  description: string
  warning?: string
}

interface AccountingPeriod {
  id: string
  period_name: string
  period_type: string
  start_date: string
  end_date: string
  is_closed: boolean
}

export function PeriodClosingModal({ isOpen, onClose, onPeriodClosed }: PeriodClosingModalProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<string>('')
  const [periods, setPeriods] = useState<AccountingPeriod[]>([])
  const [checklist, setChecklist] = useState<ClosingChecklistItem[]>([])
  const [isClosing, setIsClosing] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [confirmChecked, setConfirmChecked] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    if (isOpen) {
      fetchPeriods()
      initializeChecklist()
    }
  }, [isOpen])

  const fetchPeriods = async () => {
    try {
      const response = await fetch('/api/v1/bookkeeping/periods', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setPeriods(data.periods?.filter((p: AccountingPeriod) => !p.is_closed) || [])
      }
    } catch (error) {
      console.error('Error fetching periods:', error)
    }
  }

  const initializeChecklist = () => {
    setChecklist([
      {
        id: 'reconciliation',
        task: 'Complete All Bank Reconciliations',
        status: 'pending',
        required: true,
        description: 'Ensure all bank and credit card accounts are reconciled',
        warning: '3 accounts remain unreconciled',
      },
      {
        id: 'categorization',
        task: 'Review and Categorize All Transactions',
        status: 'pending',
        required: true,
        description: 'All transactions must be properly categorized for accurate reporting',
        warning: '15 transactions need categorization',
      },
      {
        id: 'journal_entries',
        task: 'Post All Journal Entries',
        status: 'pending',
        required: true,
        description: 'All journal entries must be reviewed and posted',
        warning: '2 unposted journal entries',
      },
      {
        id: 'accruals',
        task: 'Record Accruals and Deferrals',
        status: 'pending',
        required: false,
        description: 'Record any necessary accrued expenses or deferred revenue',
      },
      {
        id: 'depreciation',
        task: 'Calculate and Record Depreciation',
        status: 'pending',
        required: false,
        description: 'Record depreciation for fixed assets',
      },
      {
        id: 'inventory',
        task: 'Adjust Inventory Balances',
        status: 'pending',
        required: false,
        description: 'Record inventory adjustments if applicable',
      },
      {
        id: 'trial_balance',
        task: 'Review Trial Balance',
        status: 'pending',
        required: true,
        description: 'Ensure trial balance is balanced and accounts are accurate',
      },
      {
        id: 'reports',
        task: 'Generate Financial Reports',
        status: 'pending',
        required: true,
        description: 'Generate P&L, Balance Sheet, and Cash Flow statements',
      },
      {
        id: 'backup',
        task: 'Create Period Backup',
        status: 'pending',
        required: true,
        description: 'Create a backup of all financial data for the period',
      },
    ])
  }

  const runClosingChecklist = async () => {
    setIsClosing(true)

    for (let i = 0; i < checklist.length; i++) {
      const item = checklist[i]
      setCurrentStep(i)

      // Update status to in_progress
      setChecklist(prev =>
        prev.map(check =>
          check.id === item.id ? { ...check, status: 'in_progress' } : check
        )
      )

      // Simulate processing each item
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Simulate some items having issues
      const hasIssue = item.warning && Math.random() > 0.7

      if (hasIssue && item.required) {
        setChecklist(prev =>
          prev.map(check =>
            check.id === item.id ? { ...check, status: 'failed' } : check
          )
        )

        setIsClosing(false)
        toast({
          title: 'Period Closing Failed',
          description: `Failed at step: ${item.task}. ${item.warning}`,
          variant: 'destructive',
        })
        return
      }

      // Update status to completed
      setChecklist(prev =>
        prev.map(check =>
          check.id === item.id ? { ...check, status: 'completed' } : check
        )
      )
    }

    // Close the period
    await closePeriod()
  }

  const closePeriod = async () => {
    try {
      const response = await fetch('/api/v1/bookkeeping/periods/close', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ period_id: selectedPeriod }),
      })

      if (response.ok) {
        toast({
          title: 'Period Closed Successfully',
          description: 'The accounting period has been closed and locked',
        })
        onPeriodClosed()
        onClose()
      } else {
        throw new Error('Failed to close period')
      }
    } catch (error) {
      console.error('Error closing period:', error)
      toast({
        title: 'Error',
        description: 'Failed to close the period',
        variant: 'destructive',
      })
    } finally {
      setIsClosing(false)
    }
  }

  const getProgress = () => {
    const completed = checklist.filter(item => item.status === 'completed').length
    return (completed / checklist.length) * 100
  }

  const canClose = () => {
    const requiredItems = checklist.filter(item => item.required)
    const allRequiredComplete = requiredItems.every(item => item.status === 'completed')
    return allRequiredComplete && confirmChecked
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />
      case 'in_progress':
        return <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      default:
        return <Calendar className="h-4 w-4 text-gray-400" />
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Close Accounting Period</DialogTitle>
          <DialogDescription>
            Complete all required tasks before closing the period. Once closed, the period will be locked and no changes can be made.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Period Selection */}
          <div>
            <Label>Select Period to Close</Label>
            <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
              <SelectTrigger>
                <SelectValue placeholder="Select accounting period" />
              </SelectTrigger>
              <SelectContent>
                {periods.map((period) => (
                  <SelectItem key={period.id} value={period.id}>
                    <div>
                      <p className="font-medium">{period.period_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {format(new Date(period.start_date), 'MMM d')} - {format(new Date(period.end_date), 'MMM d, yyyy')}
                      </p>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Progress */}
          {isClosing && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Closing Progress</span>
                <span className="text-sm text-muted-foreground">{Math.round(getProgress())}%</span>
              </div>
              <Progress value={getProgress()} />
            </div>
          )}

          {/* Closing Checklist */}
          <div>
            <Label className="mb-2">Period Closing Checklist</Label>
            <div className="space-y-2 border rounded-lg p-4">
              {checklist.map((item, index) => (
                <div
                  key={item.id}
                  className={`flex items-start gap-3 p-2 rounded ${
                    index === currentStep && isClosing ? 'bg-blue-50' : ''
                  }`}
                >
                  {getStatusIcon(item.status)}
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className={`font-medium ${item.status === 'completed' ? 'line-through text-muted-foreground' : ''}`}>
                        {item.task}
                      </p>
                      {item.required && (
                        <Badge variant="outline" className="text-xs">Required</Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{item.description}</p>
                    {item.warning && item.status === 'pending' && (
                      <div className="flex items-center gap-1 mt-1">
                        <AlertTriangle className="h-3 w-3 text-yellow-600" />
                        <span className="text-xs text-yellow-600">{item.warning}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Warning Alert */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Important Notice</AlertTitle>
            <AlertDescription>
              Closing a period is irreversible. Once closed, you cannot make any changes to transactions or journal entries within this period. Please ensure all data is accurate before proceeding.
            </AlertDescription>
          </Alert>

          {/* Confirmation */}
          <div className="flex items-center gap-2">
            <Checkbox
              checked={confirmChecked}
              onCheckedChange={(checked) => setConfirmChecked(checked as boolean)}
              disabled={isClosing}
            />
            <Label className="text-sm">
              I confirm that all financial data for this period is accurate and complete
            </Label>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isClosing}>
            Cancel
          </Button>
          <Button
            onClick={runClosingChecklist}
            disabled={!selectedPeriod || !confirmChecked || isClosing}
          >
            {isClosing ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Closing Period...
              </>
            ) : (
              <>
                Close Period
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}