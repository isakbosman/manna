'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
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
import { Checkbox } from '@/components/ui/checkbox'
import {
  Brain,
  Check,
  X,
  RefreshCw,
  TrendingUp,
  AlertCircle,
  Sparkles,
  ArrowRight,
  FileText
} from 'lucide-react'
import { format } from 'date-fns'
import { useToast } from '@/components/ui/use-toast'

interface UncategorizedTransaction {
  id: string
  date: string
  description: string
  amount: number
  merchant_name?: string
  suggested_category?: {
    id: string
    name: string
    confidence: number
  }
  suggested_tax_category?: {
    id: string
    code: string
    name: string
    confidence: number
  }
  similar_transactions?: Array<{
    id: string
    description: string
    category: string
    date: string
  }>
}

interface Category {
  id: string
  name: string
  parent_id?: string
}

interface TaxCategory {
  id: string
  code: string
  name: string
  tax_form: string
  deduction_type: string
}

export function CategorizationReview() {
  const [transactions, setTransactions] = useState<UncategorizedTransaction[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [taxCategories, setTaxCategories] = useState<TaxCategory[]>([])
  const [selectedTransactions, setSelectedTransactions] = useState<Set<string>>(new Set())
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [selectedTaxCategory, setSelectedTaxCategory] = useState<string>('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [modelAccuracy, setModelAccuracy] = useState(0)
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      // Fetch uncategorized transactions
      const transResponse = await fetch('/api/v1/transactions/uncategorized', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (transResponse.ok) {
        const transData = await transResponse.json()
        setTransactions(transData.transactions || [])
      }

      // Fetch categories
      const catResponse = await fetch('/api/v1/categories', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (catResponse.ok) {
        const catData = await catResponse.json()
        setCategories(catData.categories || [])
      }

      // Fetch tax categories
      const taxResponse = await fetch('/api/v1/tax-categories', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (taxResponse.ok) {
        const taxData = await taxResponse.json()
        setTaxCategories(taxData.categories || [])
      }

      // Fetch model accuracy
      const accuracyResponse = await fetch('/api/v1/ml/model-status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (accuracyResponse.ok) {
        const accuracyData = await accuracyResponse.json()
        setModelAccuracy(accuracyData.accuracy || 0)
      }
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTransactionToggle = (transactionId: string) => {
    setSelectedTransactions(prev => {
      const next = new Set(prev)
      if (next.has(transactionId)) {
        next.delete(transactionId)
      } else {
        next.add(transactionId)
      }
      return next
    })
  }

  const selectAllSuggested = () => {
    const suggested = transactions
      .filter(t => t.suggested_category && t.suggested_category.confidence > 0.8)
      .map(t => t.id)
    setSelectedTransactions(new Set(suggested))
  }

  const applySuggestedCategories = async () => {
    const toApply = transactions.filter(t =>
      selectedTransactions.has(t.id) && t.suggested_category
    )

    if (toApply.length === 0) {
      toast({
        title: 'No Suggestions',
        description: 'Select transactions with suggestions to apply',
        variant: 'destructive',
      })
      return
    }

    setIsProcessing(true)

    try {
      const updates = toApply.map(t => ({
        transaction_id: t.id,
        category_id: t.suggested_category!.id,
        tax_category_id: t.suggested_tax_category?.id,
      }))

      const response = await fetch('/api/v1/transactions/bulk-categorize', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ updates }),
      })

      if (response.ok) {
        toast({
          title: 'Categories Applied',
          description: `Successfully categorized ${toApply.length} transactions`,
        })
        fetchData()
        setSelectedTransactions(new Set())
      } else {
        throw new Error('Failed to apply categories')
      }
    } catch (error) {
      console.error('Error applying categories:', error)
      toast({
        title: 'Error',
        description: 'Failed to apply categories',
        variant: 'destructive',
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const applyManualCategories = async () => {
    if (!selectedCategory || selectedTransactions.size === 0) {
      toast({
        title: 'Selection Required',
        description: 'Select transactions and a category',
        variant: 'destructive',
      })
      return
    }

    setIsProcessing(true)

    try {
      const updates = Array.from(selectedTransactions).map(id => ({
        transaction_id: id,
        category_id: selectedCategory,
        tax_category_id: selectedTaxCategory || undefined,
      }))

      const response = await fetch('/api/v1/transactions/bulk-categorize', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ updates, train_model: true }),
      })

      if (response.ok) {
        toast({
          title: 'Categories Applied',
          description: `Successfully categorized ${selectedTransactions.size} transactions`,
        })
        fetchData()
        setSelectedTransactions(new Set())
        setSelectedCategory('')
        setSelectedTaxCategory('')
      } else {
        throw new Error('Failed to apply categories')
      }
    } catch (error) {
      console.error('Error applying categories:', error)
      toast({
        title: 'Error',
        description: 'Failed to apply categories',
        variant: 'destructive',
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const trainModel = async () => {
    setIsProcessing(true)

    try {
      const response = await fetch('/api/v1/ml/train', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (response.ok) {
        const result = await response.json()
        toast({
          title: 'Model Training Complete',
          description: `New accuracy: ${(result.accuracy * 100).toFixed(1)}%`,
        })
        setModelAccuracy(result.accuracy * 100)
      } else {
        throw new Error('Failed to train model')
      }
    } catch (error) {
      console.error('Error training model:', error)
      toast({
        title: 'Error',
        description: 'Failed to train model',
        variant: 'destructive',
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.9) {
      return <Badge className="bg-green-100 text-green-800">High ({(confidence * 100).toFixed(0)}%)</Badge>
    } else if (confidence >= 0.7) {
      return <Badge className="bg-yellow-100 text-yellow-800">Medium ({(confidence * 100).toFixed(0)}%)</Badge>
    } else {
      return <Badge className="bg-red-100 text-red-800">Low ({(confidence * 100).toFixed(0)}%)</Badge>
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <RefreshCw className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* ML Model Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-primary" />
                ML Categorization Engine
              </CardTitle>
              <CardDescription>
                Automated transaction categorization using machine learning
              </CardDescription>
            </div>
            <Button onClick={trainModel} disabled={isProcessing}>
              <Sparkles className="h-4 w-4 mr-2" />
              Train Model
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Model Accuracy</p>
              <div className="flex items-center gap-2">
                <Progress value={modelAccuracy} className="flex-1" />
                <span className="text-sm font-medium">{modelAccuracy.toFixed(1)}%</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Uncategorized</p>
              <p className="text-2xl font-bold">{transactions.length}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">High Confidence</p>
              <p className="text-2xl font-bold">
                {transactions.filter(t => t.suggested_category?.confidence && t.suggested_category.confidence > 0.9).length}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Manual Categorization Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Bulk Categorization</CardTitle>
          <CardDescription>
            Select multiple transactions to categorize at once
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((category) => (
                  <SelectItem key={category.id} value={category.id}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedTaxCategory} onValueChange={setSelectedTaxCategory}>
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Select tax category (optional)" />
              </SelectTrigger>
              <SelectContent>
                {taxCategories.map((category) => (
                  <SelectItem key={category.id} value={category.id}>
                    {category.code} - {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              onClick={applyManualCategories}
              disabled={!selectedCategory || selectedTransactions.size === 0 || isProcessing}
            >
              Apply to {selectedTransactions.size} Selected
            </Button>
          </div>

          <div className="flex items-center gap-2 mt-4">
            <Button
              variant="outline"
              onClick={selectAllSuggested}
              disabled={isProcessing}
            >
              Select High Confidence
            </Button>
            <Button
              variant="outline"
              onClick={applySuggestedCategories}
              disabled={selectedTransactions.size === 0 || isProcessing}
            >
              <Check className="h-4 w-4 mr-2" />
              Apply Suggestions
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Transactions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Uncategorized Transactions</CardTitle>
          <CardDescription>
            Review and categorize transactions with ML suggestions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {transactions.length === 0 ? (
            <div className="text-center py-8">
              <Check className="h-12 w-12 text-green-600 mx-auto mb-4" />
              <p className="text-lg font-medium">All transactions categorized!</p>
              <p className="text-sm text-muted-foreground mt-1">
                No transactions require categorization at this time.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedTransactions.size === transactions.length && transactions.length > 0}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setSelectedTransactions(new Set(transactions.map(t => t.id)))
                        } else {
                          setSelectedTransactions(new Set())
                        }
                      }}
                    />
                  </TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Suggested Category</TableHead>
                  <TableHead>Tax Category</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((transaction) => (
                  <TableRow key={transaction.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedTransactions.has(transaction.id)}
                        onCheckedChange={() => handleTransactionToggle(transaction.id)}
                      />
                    </TableCell>
                    <TableCell>{format(new Date(transaction.date), 'MMM d')}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{transaction.description}</p>
                        {transaction.merchant_name && (
                          <p className="text-sm text-muted-foreground">{transaction.merchant_name}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      ${Math.abs(transaction.amount).toFixed(2)}
                    </TableCell>
                    <TableCell>
                      {transaction.suggested_category ? (
                        <Badge variant="outline">
                          {transaction.suggested_category.name}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">No suggestion</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {transaction.suggested_tax_category ? (
                        <Badge variant="outline" className="text-xs">
                          {transaction.suggested_tax_category.code}
                        </Badge>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {transaction.suggested_category &&
                        getConfidenceBadge(transaction.suggested_category.confidence)
                      }
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {transaction.suggested_category && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setSelectedTransactions(new Set([transaction.id]))
                              applySuggestedCategories()
                            }}
                            title="Accept suggestion"
                          >
                            <Check className="h-4 w-4 text-green-600" />
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            // Show similar transactions or details
                            toast({
                              title: 'Similar Transactions',
                              description: `Found ${transaction.similar_transactions?.length || 0} similar transactions`,
                            })
                          }}
                          title="View similar"
                        >
                          <FileText className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}