'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
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
  RefreshCw,
  Search,
  Upload,
  Download,
  FileText,
  DollarSign,
  Calendar
} from 'lucide-react'
import { format } from 'date-fns'
import { useToast } from '@/components/ui/use-toast'

interface Account {
  id: string
  name: string
  institution: string
  type: string
  balance: number
  last_reconciliation_date: string | null
  unreconciled_transaction_count: number
}

interface ReconciliationItem {
  id: string
  transaction_id: string | null
  statement_date: string
  statement_description: string
  statement_amount: number
  is_matched: boolean
  match_confidence: number | null
  transaction?: {
    id: string
    date: string
    description: string
    amount: number
    category: string
  }
}

interface ReconciliationPanelProps {
  onReconciliationComplete: () => void
}

export function ReconciliationPanel({ onReconciliationComplete }: ReconciliationPanelProps) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [selectedAccount, setSelectedAccount] = useState<string>('')
  const [reconciliationItems, setReconciliationItems] = useState<ReconciliationItem[]>([])
  const [statementBalance, setStatementBalance] = useState('')
  const [statementDate, setStatementDate] = useState('')
  const [isReconciling, setIsReconciling] = useState(false)
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())
  const [searchTerm, setSearchTerm] = useState('')
  const { toast } = useToast()

  useEffect(() => {
    fetchAccounts()
  }, [])

  const fetchAccounts = async () => {
    try {
      const response = await fetch('/api/v1/accounts', {
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

  const startReconciliation = async () => {
    if (!selectedAccount || !statementBalance || !statementDate) {
      toast({
        title: 'Missing Information',
        description: 'Please select an account and enter statement details',
        variant: 'destructive',
      })
      return
    }

    setIsReconciling(true)

    try {
      const response = await fetch('/api/v1/bookkeeping/reconciliation/start', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account_id: selectedAccount,
          statement_balance: parseFloat(statementBalance),
          statement_date: statementDate,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setReconciliationItems(data.items || [])
        toast({
          title: 'Reconciliation Started',
          description: `Found ${data.items?.length || 0} transactions to reconcile`,
        })
      } else {
        throw new Error('Failed to start reconciliation')
      }
    } catch (error) {
      console.error('Error starting reconciliation:', error)
      toast({
        title: 'Error',
        description: 'Failed to start reconciliation',
        variant: 'destructive',
      })
    } finally {
      setIsReconciling(false)
    }
  }

  const confirmReconciliation = async () => {
    if (selectedItems.size === 0) {
      toast({
        title: 'No Items Selected',
        description: 'Please select items to reconcile',
        variant: 'destructive',
      })
      return
    }

    try {
      const response = await fetch('/api/v1/bookkeeping/reconciliation/confirm', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account_id: selectedAccount,
          reconciled_item_ids: Array.from(selectedItems),
        }),
      })

      if (response.ok) {
        toast({
          title: 'Reconciliation Complete',
          description: `Successfully reconciled ${selectedItems.size} items`,
        })
        onReconciliationComplete()
        setReconciliationItems([])
        setSelectedItems(new Set())
        setStatementBalance('')
        setStatementDate('')
      } else {
        throw new Error('Failed to confirm reconciliation')
      }
    } catch (error) {
      console.error('Error confirming reconciliation:', error)
      toast({
        title: 'Error',
        description: 'Failed to confirm reconciliation',
        variant: 'destructive',
      })
    }
  }

  const handleItemToggle = (itemId: string) => {
    setSelectedItems(prev => {
      const next = new Set(prev)
      if (next.has(itemId)) {
        next.delete(itemId)
      } else {
        next.add(itemId)
      }
      return next
    })
  }

  const selectAllMatched = () => {
    const matched = reconciliationItems
      .filter(item => item.is_matched)
      .map(item => item.id)
    setSelectedItems(new Set(matched))
  }

  const filteredItems = reconciliationItems.filter(item =>
    searchTerm === '' ||
    item.statement_description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.transaction?.description.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const calculateDiscrepancy = () => {
    const selectedAmount = reconciliationItems
      .filter(item => selectedItems.has(item.id))
      .reduce((sum, item) => sum + item.statement_amount, 0)

    const statementTotal = parseFloat(statementBalance) || 0
    return statementTotal - selectedAmount
  }

  return (
    <div className="space-y-4">
      {/* Account Selection and Statement Details */}
      <Card>
        <CardHeader>
          <CardTitle>Start Reconciliation</CardTitle>
          <CardDescription>
            Select an account and enter your statement details
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Account</Label>
              <Select value={selectedAccount} onValueChange={setSelectedAccount}>
                <SelectTrigger>
                  <SelectValue placeholder="Select account" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      <div className="flex items-center justify-between w-full">
                        <span>{account.name}</span>
                        {account.unreconciled_transaction_count > 0 && (
                          <Badge variant="outline" className="ml-2">
                            {account.unreconciled_transaction_count} unreconciled
                          </Badge>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Statement Balance</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="number"
                  placeholder="0.00"
                  value={statementBalance}
                  onChange={(e) => setStatementBalance(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            <div>
              <Label>Statement Date</Label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  type="date"
                  value={statementDate}
                  onChange={(e) => setStatementDate(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={startReconciliation}
              disabled={isReconciling || !selectedAccount}
            >
              {isReconciling ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Start Reconciliation
                </>
              )}
            </Button>

            <Button variant="outline">
              <Upload className="h-4 w-4 mr-2" />
              Import Statement
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Reconciliation Items */}
      {reconciliationItems.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Reconciliation Items</CardTitle>
                <CardDescription>
                  Review and match transactions with your statement
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search transactions..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9 w-64"
                  />
                </div>
                <Button variant="outline" onClick={selectAllMatched}>
                  Select Matched
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedItems.size === filteredItems.length && filteredItems.length > 0}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setSelectedItems(new Set(filteredItems.map(item => item.id)))
                        } else {
                          setSelectedItems(new Set())
                        }
                      }}
                    />
                  </TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Statement Description</TableHead>
                  <TableHead>Matched Transaction</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Confidence</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedItems.has(item.id)}
                        onCheckedChange={() => handleItemToggle(item.id)}
                      />
                    </TableCell>
                    <TableCell>
                      {format(new Date(item.statement_date), 'MMM d, yyyy')}
                    </TableCell>
                    <TableCell>{item.statement_description}</TableCell>
                    <TableCell>
                      {item.transaction ? (
                        <div>
                          <p className="font-medium">{item.transaction.description}</p>
                          <p className="text-sm text-muted-foreground">
                            {item.transaction.category}
                          </p>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">No match found</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      ${Math.abs(item.statement_amount).toFixed(2)}
                    </TableCell>
                    <TableCell>
                      {item.is_matched ? (
                        <Badge className="bg-green-100 text-green-800">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Matched
                        </Badge>
                      ) : (
                        <Badge variant="outline">
                          <AlertCircle className="h-3 w-3 mr-1" />
                          Unmatched
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {item.match_confidence && (
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${item.match_confidence * 100}%` }}
                            />
                          </div>
                          <span className="text-sm text-muted-foreground">
                            {Math.round(item.match_confidence * 100)}%
                          </span>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {/* Reconciliation Summary */}
            <div className="mt-4 p-4 border rounded-lg bg-muted/50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Selected Items</p>
                  <p className="text-2xl font-bold">{selectedItems.size} of {reconciliationItems.length}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Discrepancy</p>
                  <p className={`text-2xl font-bold ${Math.abs(calculateDiscrepancy()) < 0.01 ? 'text-green-600' : 'text-red-600'}`}>
                    ${calculateDiscrepancy().toFixed(2)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                  <Button
                    onClick={confirmReconciliation}
                    disabled={selectedItems.size === 0}
                  >
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Confirm Reconciliation
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}