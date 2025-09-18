'use client'

import React, { useState, useCallback, useMemo } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Download,
  FileText,
  Trash2,
  Tag,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  X,
  Lightbulb,
  Archive,
  RotateCcw,
  Zap,
  BarChart3,
  Clock,
  Users
} from 'lucide-react'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Card, CardContent } from '../ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel
} from '../ui/dropdown-menu'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle
} from '../ui/alert-dialog'
import { Tooltip, TooltipContent, TooltipTrigger } from '../ui/tooltip'
import { Progress } from '../ui/progress'
import { cn, formatCurrency } from '../../lib/utils'
import { Transaction, transactionsApi } from '../../lib/api/transactions'
import { useSuccessToast, useErrorToast } from '../ui/toast'
import { format, isThisMonth, isThisYear } from 'date-fns'

interface BulkActionsProps {
  selectedTransactions: Transaction[]
  onClearSelection: () => void
  onCategorize: () => void
  onTransactionsUpdated: (transactions: Transaction[]) => void
  className?: string
}

interface SmartSuggestion {
  type: 'merchant' | 'amount' | 'category' | 'date'
  title: string
  description: string
  count: number
  icon: React.ReactNode
  action: () => void
}

interface BulkOperationProgress {
  isRunning: boolean
  operation: string
  completed: number
  total: number
  errors: string[]
  startTime?: Date
}

export function BulkActions({
  selectedTransactions,
  onClearSelection,
  onCategorize,
  onTransactionsUpdated,
  className
}: BulkActionsProps) {
  const queryClient = useQueryClient()
  const successToast = useSuccessToast()
  const errorToast = useErrorToast()

  // State
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [exportDialogOpen, setExportDialogOpen] = useState(false)
  const [progress, setProgress] = useState<BulkOperationProgress | null>(null)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [undoStack, setUndoStack] = useState<Array<{
    operation: string
    transactions: Transaction[]
    timestamp: Date
  }>>([])

  // Mutations
  const bulkUpdateMutation = useMutation({
    mutationFn: async ({ updates, transactionIds }: {
      updates: Partial<Transaction>
      transactionIds: string[]
    }) => {
      return transactionsApi.bulkUpdateTransactions({
        transaction_ids: transactionIds,
        updates
      })
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
      onTransactionsUpdated(result)
    }
  })

  const bulkDeleteMutation = useMutation({
    mutationFn: async (transactionIds: string[]) => {
      // Store for undo before deleting
      const transactionsForUndo = selectedTransactions.slice()
      setUndoStack(prev => [...prev, {
        operation: 'delete',
        transactions: transactionsForUndo,
        timestamp: new Date()
      }])

      // Simulate batch delete (would need actual API endpoint)
      const deletePromises = transactionIds.map(id =>
        transactionsApi.deleteTransaction(id)
      )
      return Promise.all(deletePromises)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['transaction-stats'] })
      successToast(
        'Transactions Deleted',
        `Successfully deleted ${selectedTransactions.length} transactions`
      )
      onClearSelection()
    },
    onError: (error: any) => {
      errorToast('Delete Failed', error.message || 'Failed to delete transactions')
    }
  })

  const exportMutation = useMutation({
    mutationFn: async (format: 'csv' | 'xlsx') => {
      // Create a filter that includes only selected transaction IDs
      const filters = {
        transaction_ids: selectedTransactions.map(t => t.id)
      }
      return transactionsApi.exportTransactions(filters as any, format)
    },
    onSuccess: (_, format) => {
      successToast(
        'Export Complete',
        `${selectedTransactions.length} transactions exported as ${format.toUpperCase()}`
      )
    },
    onError: (error: any) => {
      errorToast('Export Failed', error.message || 'Failed to export transactions')
    }
  })

  // Calculate summary stats
  const summary = useMemo(() => {
    const totalAmount = selectedTransactions.reduce((sum, t) => sum + t.amount, 0)
    const incomeAmount = selectedTransactions
      .filter(t => t.amount > 0)
      .reduce((sum, t) => sum + t.amount, 0)
    const expenseAmount = selectedTransactions
      .filter(t => t.amount < 0)
      .reduce((sum, t) => sum + Math.abs(t.amount), 0)

    const accounts = new Set(selectedTransactions.map(t => t.account_id)).size
    const dateRange = selectedTransactions.length > 0 ? {
      start: new Date(Math.min(...selectedTransactions.map(t => new Date(t.date).getTime()))),
      end: new Date(Math.max(...selectedTransactions.map(t => new Date(t.date).getTime())))
    } : null

    const uncategorized = selectedTransactions.filter(t => !t.category_id).length
    const pending = selectedTransactions.filter(t => t.is_pending).length

    return {
      count: selectedTransactions.length,
      totalAmount,
      incomeAmount,
      expenseAmount,
      accounts,
      dateRange,
      uncategorized,
      pending
    }
  }, [selectedTransactions])

  // Generate smart suggestions
  const smartSuggestions = useMemo((): SmartSuggestion[] => {
    if (selectedTransactions.length < 2) return []

    const suggestions: SmartSuggestion[] = []

    // Same merchant suggestion
    const merchantGroups = selectedTransactions.reduce((acc, t) => {
      const merchant = t.merchant_name || 'Unknown'
      acc[merchant] = (acc[merchant] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    const topMerchant = Object.entries(merchantGroups)
      .sort(([,a], [,b]) => b - a)[0]

    if (topMerchant && topMerchant[1] > 1) {
      suggestions.push({
        type: 'merchant',
        title: `All from ${topMerchant[0]}`,
        description: `${topMerchant[1]} transactions from the same merchant`,
        count: topMerchant[1],
        icon: <Users className="h-4 w-4" />,
        action: () => {
          // Would filter to show only transactions from this merchant
          console.log('Filter by merchant:', topMerchant[0])
        }
      })
    }

    // Similar amounts
    const amountGroups = selectedTransactions.reduce((acc, t) => {
      const roundedAmount = Math.round(Math.abs(t.amount))
      acc[roundedAmount] = (acc[roundedAmount] || 0) + 1
      return acc
    }, {} as Record<number, number>)

    const topAmount = Object.entries(amountGroups)
      .sort(([,a], [,b]) => b - a)[0]

    if (topAmount && topAmount[1] > 1) {
      suggestions.push({
        type: 'amount',
        title: `Similar amounts (~${formatCurrency(Number(topAmount[0]))})`,
        description: `${topAmount[1]} transactions with similar amounts`,
        count: topAmount[1],
        icon: <BarChart3 className="h-4 w-4" />,
        action: () => {
          console.log('Filter by amount:', topAmount[0])
        }
      })
    }

    // Recent transactions
    const recentCount = selectedTransactions.filter(t =>
      isThisMonth(new Date(t.date))
    ).length

    if (recentCount > selectedTransactions.length * 0.8) {
      suggestions.push({
        type: 'date',
        title: 'Recent transactions',
        description: `${recentCount} transactions from this month`,
        count: recentCount,
        icon: <Clock className="h-4 w-4" />,
        action: () => {
          console.log('Focus on recent transactions')
        }
      })
    }

    return suggestions
  }, [selectedTransactions])

  // Handlers
  const handleBulkMarkReviewed = useCallback(async (reviewed: boolean) => {
    try {
      setProgress({
        isRunning: true,
        operation: reviewed ? 'Marking as reviewed' : 'Marking as unreviewed',
        completed: 0,
        total: selectedTransactions.length,
        errors: [],
        startTime: new Date()
      })

      const result = await bulkUpdateMutation.mutateAsync({
        updates: { notes: reviewed ? 'reviewed' : undefined },
        transactionIds: selectedTransactions.map(t => t.id)
      })

      setProgress(null)
      successToast(
        reviewed ? 'Marked as Reviewed' : 'Marked as Unreviewed',
        `${selectedTransactions.length} transactions updated`
      )
      onClearSelection()
    } catch (error: any) {
      setProgress(null)
      errorToast('Update Failed', error.message || 'Failed to update transactions')
    }
  }, [selectedTransactions, bulkUpdateMutation, successToast, errorToast, onClearSelection])

  const handleBulkDelete = useCallback(async () => {
    try {
      setProgress({
        isRunning: true,
        operation: 'Deleting transactions',
        completed: 0,
        total: selectedTransactions.length,
        errors: [],
        startTime: new Date()
      })

      await bulkDeleteMutation.mutateAsync(selectedTransactions.map(t => t.id))
      setProgress(null)
      setDeleteDialogOpen(false)
    } catch (error) {
      setProgress(null)
    }
  }, [selectedTransactions, bulkDeleteMutation])

  const handleExport = useCallback(async (format: 'csv' | 'xlsx') => {
    try {
      await exportMutation.mutateAsync(format)
      setExportDialogOpen(false)
    } catch (error) {
      // Error handled by mutation
    }
  }, [exportMutation])

  const handleUndo = useCallback(() => {
    if (undoStack.length === 0) return

    const lastOperation = undoStack[undoStack.length - 1]

    // Remove from undo stack
    setUndoStack(prev => prev.slice(0, -1))

    // For now, just show a message since undo is complex
    successToast(
      'Undo Available',
      `${lastOperation.operation} operation can be undone (feature coming soon)`
    )
  }, [undoStack, successToast])

  if (selectedTransactions.length === 0) return null

  return (
    <>
      <Card className={cn('border-primary-200 bg-primary-50/50', className)}>
        <CardContent className="p-4">
          <div className="space-y-4">
            {/* Progress Bar */}
            {progress && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{progress.operation}...</span>
                  <span>{progress.completed}/{progress.total}</span>
                </div>
                <Progress
                  value={(progress.completed / progress.total) * 100}
                  className="h-2"
                />
                {progress.errors.length > 0 && (
                  <div className="text-xs text-error-600">
                    {progress.errors.length} errors occurred
                  </div>
                )}
              </div>
            )}

            {/* Summary and Actions */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {/* Selection Summary */}
                <div className="flex items-center gap-2">
                  <Badge variant="default" className="text-sm">
                    {summary.count} selected
                  </Badge>
                  <div className="text-sm text-neutral-600">
                    <span className="font-medium">
                      {formatCurrency(summary.totalAmount)}
                    </span>
                    {summary.accounts > 1 && (
                      <span className="ml-2">• {summary.accounts} accounts</span>
                    )}
                  </div>
                </div>

                {/* Quick Stats */}
                {summary.incomeAmount > 0 && summary.expenseAmount > 0 && (
                  <div className="flex items-center gap-2 text-xs text-neutral-500">
                    <span className="text-success-600">
                      +{formatCurrency(summary.incomeAmount)}
                    </span>
                    <span>•</span>
                    <span className="text-error-600">
                      -{formatCurrency(summary.expenseAmount)}
                    </span>
                  </div>
                )}

                {/* Indicators */}
                <div className="flex items-center gap-1">
                  {summary.uncategorized > 0 && (
                    <Tooltip>
                      <TooltipTrigger>
                        <Badge variant="outline" className="text-xs">
                          {summary.uncategorized} uncategorized
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        {summary.uncategorized} transactions need categorization
                      </TooltipContent>
                    </Tooltip>
                  )}
                  {summary.pending > 0 && (
                    <Tooltip>
                      <TooltipTrigger>
                        <Badge variant="secondary" className="text-xs">
                          {summary.pending} pending
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        {summary.pending} transactions are still pending
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>

                {/* Smart Suggestions */}
                {smartSuggestions.length > 0 && (
                  <DropdownMenu open={showSuggestions} onOpenChange={setShowSuggestions}>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-7">
                        <Lightbulb className="h-4 w-4 mr-1" />
                        {smartSuggestions.length} suggestion{smartSuggestions.length !== 1 ? 's' : ''}
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start" className="w-80">
                      <DropdownMenuLabel>Smart Suggestions</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      {smartSuggestions.map((suggestion, index) => (
                        <DropdownMenuItem
                          key={index}
                          onClick={suggestion.action}
                          className="flex items-start gap-3 py-3"
                        >
                          <div className="flex-shrink-0 mt-0.5">
                            {suggestion.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-medium">{suggestion.title}</div>
                            <div className="text-xs text-neutral-500">
                              {suggestion.description}
                            </div>
                          </div>
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                {/* Quick Actions */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onCategorize}
                  disabled={bulkUpdateMutation.isPending}
                >
                  <Tag className="h-4 w-4 mr-1" />
                  Categorize
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleBulkMarkReviewed(true)}
                  disabled={bulkUpdateMutation.isPending}
                >
                  <CheckCircle2 className="h-4 w-4 mr-1" />
                  Mark Reviewed
                </Button>

                {/* More Actions Dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      <Zap className="h-4 w-4 mr-1" />
                      More Actions
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel>Bulk Actions</DropdownMenuLabel>
                    <DropdownMenuSeparator />

                    <DropdownMenuItem onClick={() => setExportDialogOpen(true)}>
                      <Download className="h-4 w-4 mr-2" />
                      Export Selected
                    </DropdownMenuItem>

                    <DropdownMenuItem onClick={() => handleBulkMarkReviewed(false)}>
                      <XCircle className="h-4 w-4 mr-2" />
                      Mark Unreviewed
                    </DropdownMenuItem>

                    <DropdownMenuItem
                      onClick={() => {
                        // Archive functionality (mark as archived)
                        handleBulkMarkReviewed(true)
                      }}
                    >
                      <Archive className="h-4 w-4 mr-2" />
                      Archive
                    </DropdownMenuItem>

                    <DropdownMenuSeparator />

                    <DropdownMenuItem
                      onClick={() => setDeleteDialogOpen(true)}
                      className="text-error-600 focus:text-error-600"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete Selected
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>

                {/* Undo Button */}
                {undoStack.length > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleUndo}
                        className="h-8 w-8 p-0"
                      >
                        <RotateCcw className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      Undo last operation
                    </TooltipContent>
                  </Tooltip>
                )}

                {/* Clear Selection */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClearSelection}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Date Range */}
            {summary.dateRange && (
              <div className="text-xs text-neutral-500">
                {summary.dateRange.start.getTime() === summary.dateRange.end.getTime() ? (
                  `${format(summary.dateRange.start, 'MMM d, yyyy')}`
                ) : (
                  `${format(summary.dateRange.start, 'MMM d')} - ${format(summary.dateRange.end, 'MMM d, yyyy')}`
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-error-600" />
              Delete {selectedTransactions.length} Transaction{selectedTransactions.length !== 1 ? 's' : ''}?
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-2">
              <p>This action cannot be undone. The following transactions will be permanently deleted:</p>
              <div className="bg-neutral-50 rounded-lg p-3 space-y-1 max-h-32 overflow-y-auto">
                <div className="text-sm font-medium">
                  {summary.count} transactions • {formatCurrency(summary.totalAmount)}
                </div>
                {summary.dateRange && (
                  <div className="text-xs text-neutral-500">
                    {format(summary.dateRange.start, 'MMM d')} - {format(summary.dateRange.end, 'MMM d, yyyy')}
                  </div>
                )}
                {summary.accounts > 1 && (
                  <div className="text-xs text-neutral-500">
                    Across {summary.accounts} accounts
                  </div>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBulkDelete}
              className="bg-error-600 hover:bg-error-700"
              disabled={bulkDeleteMutation.isPending}
            >
              {bulkDeleteMutation.isPending ? 'Deleting...' : 'Delete Transactions'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Export Dialog */}
      <AlertDialog open={exportDialogOpen} onOpenChange={setExportDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Export {selectedTransactions.length} Transaction{selectedTransactions.length !== 1 ? 's' : ''}
            </AlertDialogTitle>
            <AlertDialogDescription>
              Choose the format for exporting your selected transactions.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="grid grid-cols-2 gap-3 py-4">
            <Button
              variant="outline"
              onClick={() => handleExport('csv')}
              disabled={exportMutation.isPending}
              className="h-20 flex-col"
            >
              <FileText className="h-6 w-6 mb-2" />
              CSV File
              <span className="text-xs text-neutral-500">Spreadsheet compatible</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => handleExport('xlsx')}
              disabled={exportMutation.isPending}
              className="h-20 flex-col"
            >
              <FileText className="h-6 w-6 mb-2" />
              Excel File
              <span className="text-xs text-neutral-500">Full formatting</span>
            </Button>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}