'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  FileText,
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Check,
  X,
  Eye,
  Edit,
  Copy,
  Trash2,
  Download
} from 'lucide-react'
import { format } from 'date-fns'
import { useToast } from '@/components/ui/use-toast'
import { JournalEntryForm } from './JournalEntryForm'

interface JournalEntry {
  id: string
  entry_number: string
  entry_date: string
  description: string
  reference: string | null
  journal_type: string | null
  total_debits: number
  total_credits: number
  is_balanced: boolean
  is_posted: boolean
  posting_date: string | null
  source_type: string | null
  created_at: string
  lines: JournalEntryLine[]
}

interface JournalEntryLine {
  id: string
  account_code: string
  account_name: string
  debit_amount: number
  credit_amount: number
  description: string | null
}

export function JournalEntriesTable() {
  const [entries, setEntries] = useState<JournalEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null)
  const [showEntryForm, setShowEntryForm] = useState(false)
  const [editingEntry, setEditingEntry] = useState<JournalEntry | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    fetchJournalEntries()
  }, [])

  const fetchJournalEntries = async () => {
    try {
      const response = await fetch('/api/v1/bookkeeping/journal-entries', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setEntries(data.entries || [])
      }
    } catch (error) {
      console.error('Error fetching journal entries:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch journal entries',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handlePost = async (entryId: string) => {
    try {
      const response = await fetch(`/api/v1/bookkeeping/journal-entries/${entryId}/post`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (response.ok) {
        toast({
          title: 'Entry Posted',
          description: 'Journal entry has been posted successfully',
        })
        fetchJournalEntries()
      } else {
        throw new Error('Failed to post entry')
      }
    } catch (error) {
      console.error('Error posting entry:', error)
      toast({
        title: 'Error',
        description: 'Failed to post journal entry',
        variant: 'destructive',
      })
    }
  }

  const handleDelete = async (entryId: string) => {
    if (!confirm('Are you sure you want to delete this journal entry?')) {
      return
    }

    try {
      const response = await fetch(`/api/v1/bookkeeping/journal-entries/${entryId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (response.ok) {
        toast({
          title: 'Entry Deleted',
          description: 'Journal entry has been deleted',
        })
        fetchJournalEntries()
      } else {
        throw new Error('Failed to delete entry')
      }
    } catch (error) {
      console.error('Error deleting entry:', error)
      toast({
        title: 'Error',
        description: 'Failed to delete journal entry',
        variant: 'destructive',
      })
    }
  }

  const handleDuplicate = async (entry: JournalEntry) => {
    const duplicatedEntry = {
      ...entry,
      id: undefined,
      entry_number: undefined,
      is_posted: false,
      posting_date: null,
      created_at: undefined,
    }
    setEditingEntry(duplicatedEntry as any)
    setShowEntryForm(true)
  }

  const exportEntries = () => {
    // Create CSV content
    const csvContent = entries.map(entry =>
      `${entry.entry_number},${entry.entry_date},${entry.description},${entry.total_debits},${entry.total_credits}`
    ).join('\n')

    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `journal_entries_${format(new Date(), 'yyyy-MM-dd')}.csv`
    a.click()
  }

  const filteredEntries = entries.filter(entry => {
    const matchesSearch = searchTerm === '' ||
      entry.entry_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (entry.reference && entry.reference.toLowerCase().includes(searchTerm.toLowerCase()))

    const matchesType = filterType === 'all' || entry.journal_type === filterType
    const matchesStatus = filterStatus === 'all' ||
      (filterStatus === 'posted' && entry.is_posted) ||
      (filterStatus === 'unposted' && !entry.is_posted) ||
      (filterStatus === 'unbalanced' && !entry.is_balanced)

    return matchesSearch && matchesType && matchesStatus
  })

  const getStatusBadge = (entry: JournalEntry) => {
    if (!entry.is_balanced) {
      return (
        <Badge variant="destructive">
          <X className="h-3 w-3 mr-1" />
          Unbalanced
        </Badge>
      )
    }
    if (entry.is_posted) {
      return (
        <Badge className="bg-green-100 text-green-800">
          <Check className="h-3 w-3 mr-1" />
          Posted
        </Badge>
      )
    }
    return (
      <Badge variant="outline">
        Unposted
      </Badge>
    )
  }

  const getSourceBadge = (source: string | null) => {
    const colors = {
      plaid_sync: 'bg-blue-100 text-blue-800',
      manual: 'bg-gray-100 text-gray-800',
      recurring: 'bg-purple-100 text-purple-800',
      adjustment: 'bg-yellow-100 text-yellow-800',
    }

    if (!source) return null

    return (
      <Badge className={colors[source as keyof typeof colors] || 'bg-gray-100 text-gray-800'} variant="outline">
        {source}
      </Badge>
    )
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <p className="text-muted-foreground">Loading journal entries...</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Journal Entries</CardTitle>
              <CardDescription>
                Manage and review double-entry bookkeeping records
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={exportEntries}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button onClick={() => setShowEntryForm(true)}>
                <Plus className="h-4 w-4 mr-2" />
                New Entry
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex items-center gap-4 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search entries..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="general">General</SelectItem>
                <SelectItem value="sales">Sales</SelectItem>
                <SelectItem value="purchase">Purchase</SelectItem>
                <SelectItem value="cash_receipts">Cash Receipts</SelectItem>
                <SelectItem value="cash_disbursements">Cash Disbursements</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="posted">Posted</SelectItem>
                <SelectItem value="unposted">Unposted</SelectItem>
                <SelectItem value="unbalanced">Unbalanced</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Journal Entries Table */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Entry #</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Reference</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Debits</TableHead>
                <TableHead className="text-right">Credits</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Source</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEntries.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell className="font-medium">{entry.entry_number}</TableCell>
                  <TableCell>{format(new Date(entry.entry_date), 'MMM d, yyyy')}</TableCell>
                  <TableCell className="max-w-xs truncate">{entry.description}</TableCell>
                  <TableCell>{entry.reference || '-'}</TableCell>
                  <TableCell>{entry.journal_type || 'General'}</TableCell>
                  <TableCell className="text-right">${entry.total_debits.toFixed(2)}</TableCell>
                  <TableCell className="text-right">${entry.total_credits.toFixed(2)}</TableCell>
                  <TableCell>{getStatusBadge(entry)}</TableCell>
                  <TableCell>{getSourceBadge(entry.source_type)}</TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => setSelectedEntry(entry)}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        {!entry.is_posted && (
                          <>
                            <DropdownMenuItem onClick={() => {
                              setEditingEntry(entry)
                              setShowEntryForm(true)
                            }}>
                              <Edit className="h-4 w-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handlePost(entry.id)}>
                              <Check className="h-4 w-4 mr-2" />
                              Post Entry
                            </DropdownMenuItem>
                          </>
                        )}
                        <DropdownMenuItem onClick={() => handleDuplicate(entry)}>
                          <Copy className="h-4 w-4 mr-2" />
                          Duplicate
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        {!entry.is_posted && (
                          <DropdownMenuItem
                            onClick={() => handleDelete(entry.id)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Entry Details Dialog */}
      {selectedEntry && (
        <Dialog open={!!selectedEntry} onOpenChange={() => setSelectedEntry(null)}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Journal Entry #{selectedEntry.entry_number}</DialogTitle>
              <DialogDescription>
                {selectedEntry.description}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Date:</span> {format(new Date(selectedEntry.entry_date), 'MMM d, yyyy')}
                </div>
                <div>
                  <span className="font-medium">Reference:</span> {selectedEntry.reference || 'N/A'}
                </div>
                <div>
                  <span className="font-medium">Type:</span> {selectedEntry.journal_type || 'General'}
                </div>
                <div>
                  <span className="font-medium">Status:</span> {selectedEntry.is_posted ? 'Posted' : 'Unposted'}
                </div>
              </div>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Account</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Debit</TableHead>
                    <TableHead className="text-right">Credit</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {selectedEntry.lines.map((line) => (
                    <TableRow key={line.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{line.account_code}</p>
                          <p className="text-sm text-muted-foreground">{line.account_name}</p>
                        </div>
                      </TableCell>
                      <TableCell>{line.description || '-'}</TableCell>
                      <TableCell className="text-right">
                        {line.debit_amount > 0 ? `$${line.debit_amount.toFixed(2)}` : '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        {line.credit_amount > 0 ? `$${line.credit_amount.toFixed(2)}` : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow>
                    <TableCell colSpan={2} className="font-medium">Total</TableCell>
                    <TableCell className="text-right font-medium">
                      ${selectedEntry.total_debits.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      ${selectedEntry.total_credits.toFixed(2)}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Journal Entry Form */}
      {showEntryForm && (
        <JournalEntryForm
          isOpen={showEntryForm}
          onClose={() => {
            setShowEntryForm(false)
            setEditingEntry(null)
          }}
          onSave={() => {
            setShowEntryForm(false)
            setEditingEntry(null)
            fetchJournalEntries()
          }}
          entry={editingEntry}
        />
      )}
    </>
  )
}