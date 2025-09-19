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
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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
  Plus,
  Trash2,
  Check,
  X,
  Calculator
} from 'lucide-react'
import { format } from 'date-fns'
import { useToast } from '@/components/ui/use-toast'

interface JournalEntryLine {
  id?: string
  account_id: string
  account_code?: string
  account_name?: string
  debit_amount: number
  credit_amount: number
  description: string
}

interface JournalEntry {
  id?: string
  entry_date: string
  description: string
  reference?: string
  journal_type?: string
  lines: JournalEntryLine[]
}

interface ChartAccount {
  id: string
  account_code: string
  account_name: string
  account_type: string
  normal_balance: string
}

interface JournalEntryFormProps {
  isOpen: boolean
  onClose: () => void
  onSave: (entry: JournalEntry) => void
  entry?: JournalEntry | null
}

export function JournalEntryForm({ isOpen, onClose, onSave, entry }: JournalEntryFormProps) {
  const [formData, setFormData] = useState<JournalEntry>({
    entry_date: format(new Date(), 'yyyy-MM-dd'),
    description: '',
    reference: '',
    journal_type: 'general',
    lines: [
      { account_id: '', debit_amount: 0, credit_amount: 0, description: '' },
      { account_id: '', debit_amount: 0, credit_amount: 0, description: '' },
    ],
  })
  const [accounts, setAccounts] = useState<ChartAccount[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    if (entry) {
      setFormData(entry)
    }
    fetchAccounts()
  }, [entry])

  const fetchAccounts = async () => {
    try {
      const response = await fetch('/api/v1/bookkeeping/chart-of-accounts', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setAccounts(data.accounts || [])
      }
    } catch (error) {
      console.error('Error fetching accounts:', error)
    }
  }

  const handleAddLine = () => {
    setFormData(prev => ({
      ...prev,
      lines: [
        ...prev.lines,
        { account_id: '', debit_amount: 0, credit_amount: 0, description: '' },
      ],
    }))
  }

  const handleRemoveLine = (index: number) => {
    if (formData.lines.length <= 2) {
      toast({
        title: 'Minimum Lines Required',
        description: 'A journal entry must have at least 2 lines',
        variant: 'destructive',
      })
      return
    }

    setFormData(prev => ({
      ...prev,
      lines: prev.lines.filter((_, i) => i !== index),
    }))
  }

  const handleLineChange = (index: number, field: keyof JournalEntryLine, value: any) => {
    setFormData(prev => ({
      ...prev,
      lines: prev.lines.map((line, i) => {
        if (i === index) {
          const updatedLine = { ...line, [field]: value }

          // If setting debit, clear credit and vice versa
          if (field === 'debit_amount' && value > 0) {
            updatedLine.credit_amount = 0
          } else if (field === 'credit_amount' && value > 0) {
            updatedLine.debit_amount = 0
          }

          // Update account details if account_id changes
          if (field === 'account_id') {
            const account = accounts.find(a => a.id === value)
            if (account) {
              updatedLine.account_code = account.account_code
              updatedLine.account_name = account.account_name
            }
          }

          return updatedLine
        }
        return line
      }),
    }))
  }

  const calculateTotals = () => {
    const totalDebits = formData.lines.reduce((sum, line) => sum + (line.debit_amount || 0), 0)
    const totalCredits = formData.lines.reduce((sum, line) => sum + (line.credit_amount || 0), 0)
    return { totalDebits, totalCredits, difference: totalDebits - totalCredits }
  }

  const isValid = () => {
    const { totalDebits, totalCredits } = calculateTotals()

    if (Math.abs(totalDebits - totalCredits) > 0.01) {
      return false
    }

    if (!formData.entry_date || !formData.description) {
      return false
    }

    const hasValidLines = formData.lines.every(line =>
      line.account_id && (line.debit_amount > 0 || line.credit_amount > 0)
    )

    return hasValidLines
  }

  const handleSubmit = async () => {
    if (!isValid()) {
      toast({
        title: 'Invalid Entry',
        description: 'Please ensure debits equal credits and all required fields are filled',
        variant: 'destructive',
      })
      return
    }

    setIsSubmitting(true)

    try {
      const url = entry?.id
        ? `/api/v1/bookkeeping/journal-entries/${entry.id}`
        : '/api/v1/bookkeeping/journal-entries'

      const method = entry?.id ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        toast({
          title: 'Success',
          description: entry?.id ? 'Journal entry updated' : 'Journal entry created',
        })
        onSave(formData)
      } else {
        throw new Error('Failed to save journal entry')
      }
    } catch (error) {
      console.error('Error saving journal entry:', error)
      toast({
        title: 'Error',
        description: 'Failed to save journal entry',
        variant: 'destructive',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const { totalDebits, totalCredits, difference } = calculateTotals()

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{entry?.id ? 'Edit' : 'Create'} Journal Entry</DialogTitle>
          <DialogDescription>
            Record a double-entry bookkeeping transaction. Debits must equal credits.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Basic Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Entry Date</Label>
              <Input
                type="date"
                value={formData.entry_date}
                onChange={(e) => setFormData(prev => ({ ...prev, entry_date: e.target.value }))}
              />
            </div>
            <div>
              <Label>Journal Type</Label>
              <Select
                value={formData.journal_type}
                onValueChange={(value) => setFormData(prev => ({ ...prev, journal_type: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">General</SelectItem>
                  <SelectItem value="sales">Sales</SelectItem>
                  <SelectItem value="purchase">Purchase</SelectItem>
                  <SelectItem value="cash_receipts">Cash Receipts</SelectItem>
                  <SelectItem value="cash_disbursements">Cash Disbursements</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label>Description</Label>
            <Textarea
              placeholder="Enter journal entry description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows={2}
            />
          </div>

          <div>
            <Label>Reference (Optional)</Label>
            <Input
              placeholder="Invoice #, Check #, etc."
              value={formData.reference}
              onChange={(e) => setFormData(prev => ({ ...prev, reference: e.target.value }))}
            />
          </div>

          {/* Journal Entry Lines */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label>Entry Lines</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAddLine}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Line
              </Button>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Account</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Debit</TableHead>
                  <TableHead className="text-right">Credit</TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {formData.lines.map((line, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Select
                        value={line.account_id}
                        onValueChange={(value) => handleLineChange(index, 'account_id', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select account" />
                        </SelectTrigger>
                        <SelectContent>
                          {accounts.map((account) => (
                            <SelectItem key={account.id} value={account.id}>
                              {account.account_code} - {account.account_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Input
                        placeholder="Line description"
                        value={line.description}
                        onChange={(e) => handleLineChange(index, 'description', e.target.value)}
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={line.debit_amount || ''}
                        onChange={(e) => handleLineChange(index, 'debit_amount', parseFloat(e.target.value) || 0)}
                        className="text-right"
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={line.credit_amount || ''}
                        onChange={(e) => handleLineChange(index, 'credit_amount', parseFloat(e.target.value) || 0)}
                        className="text-right"
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveLine(index)}
                        disabled={formData.lines.length <= 2}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                <TableRow>
                  <TableCell colSpan={2} className="font-medium">Total</TableCell>
                  <TableCell className="text-right font-medium">
                    ${totalDebits.toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    ${totalCredits.toFixed(2)}
                  </TableCell>
                  <TableCell></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>

          {/* Balance Check */}
          {Math.abs(difference) > 0.01 && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Entry is not balanced. Difference: ${Math.abs(difference).toFixed(2)}
              </AlertDescription>
            </Alert>
          )}

          {Math.abs(difference) <= 0.01 && totalDebits > 0 && (
            <Alert>
              <Check className="h-4 w-4" />
              <AlertDescription className="text-green-600">
                Entry is balanced. Ready to save.
              </AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isValid() || isSubmitting}
          >
            {isSubmitting ? 'Saving...' : 'Save Entry'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}