import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Search,
  Edit,
  Trash2,
  ChevronRight,
  ChevronDown,
  DollarSign,
  Building,
  CreditCard,
  TrendingUp,
  Wallet,
  Filter,
  Eye,
  EyeOff,
} from 'lucide-react'
import { Card } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Switch } from '../ui/switch'
import { ScrollArea } from '../ui/scroll-area'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog'
import { taxApi, ChartOfAccount } from '../../lib/api/tax'
import { cn } from '../../lib/utils'

interface ChartOfAccountsManagerProps {
  className?: string
}

interface AccountTreeNode extends ChartOfAccount {
  children: AccountTreeNode[]
  level: number
}

export function ChartOfAccountsManager({ className }: ChartOfAccountsManagerProps) {
  const queryClient = useQueryClient()

  // State
  const [searchTerm, setSearchTerm] = React.useState<string>('')
  const [filterAccountType, setFilterAccountType] = React.useState<string>('')
  const [showInactiveAccounts, setShowInactiveAccounts] = React.useState<boolean>(false)
  const [expandedNodes, setExpandedNodes] = React.useState<Set<string>>(new Set())
  const [isCreateModalOpen, setIsCreateModalOpen] = React.useState<boolean>(false)
  const [editingAccount, setEditingAccount] = React.useState<ChartOfAccount | null>(null)

  // Form state for create/edit
  const [formData, setFormData] = React.useState({
    name: '',
    account_type: 'asset' as ChartOfAccount['account_type'],
    parent_id: '',
    is_active: true,
  })
  const [formErrors, setFormErrors] = React.useState<Record<string, string>>({})

  // Load chart of accounts
  const { data: accounts = [], isLoading, error } = useQuery({
    queryKey: ['chart-of-accounts'],
    queryFn: taxApi.getChartOfAccounts,
  })

  // Create/Update mutations would go here if the API supported it
  // For now, we'll focus on the display and structure

  // Build account tree structure
  const accountTree = React.useMemo(() => {
    const buildTree = (accounts: ChartOfAccount[], parentId: string | null = null, level = 0): AccountTreeNode[] => {
      return accounts
        .filter(account => account.parent_id === parentId)
        .map(account => ({
          ...account,
          level,
          children: buildTree(accounts, account.id, level + 1),
        }))
        .sort((a, b) => a.name.localeCompare(b.name))
    }

    return buildTree(accounts)
  }, [accounts])

  // Filter accounts based on search and filters
  const filteredAccountTree = React.useMemo(() => {
    const filterNode = (node: AccountTreeNode): AccountTreeNode | null => {
      const matchesSearch = !searchTerm ||
        node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        node.account_type.toLowerCase().includes(searchTerm.toLowerCase())

      const matchesType = !filterAccountType || node.account_type === filterAccountType
      const matchesActive = showInactiveAccounts || node.is_active

      const filteredChildren = node.children
        .map(child => filterNode(child))
        .filter(Boolean) as AccountTreeNode[]

      if ((matchesSearch && matchesType && matchesActive) || filteredChildren.length > 0) {
        return {
          ...node,
          children: filteredChildren,
        }
      }

      return null
    }

    return accountTree
      .map(node => filterNode(node))
      .filter(Boolean) as AccountTreeNode[]
  }, [accountTree, searchTerm, filterAccountType, showInactiveAccounts])

  const accountTypeIcons = {
    asset: <Wallet className="h-4 w-4 text-green-600" />,
    liability: <CreditCard className="h-4 w-4 text-red-600" />,
    equity: <Building className="h-4 w-4 text-blue-600" />,
    income: <TrendingUp className="h-4 w-4 text-emerald-600" />,
    expense: <DollarSign className="h-4 w-4 text-orange-600" />,
  }

  const accountTypeColors = {
    asset: 'text-green-600 bg-green-50 border-green-200',
    liability: 'text-red-600 bg-red-50 border-red-200',
    equity: 'text-blue-600 bg-blue-50 border-blue-200',
    income: 'text-emerald-600 bg-emerald-50 border-emerald-200',
    expense: 'text-orange-600 bg-orange-50 border-orange-200',
  }

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const toggleNodeExpansion = (nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev)
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId)
      } else {
        newSet.add(nodeId)
      }
      return newSet
    })
  }

  const handleCreateAccount = () => {
    setFormData({
      name: '',
      account_type: 'asset',
      parent_id: '',
      is_active: true,
    })
    setFormErrors({})
    setEditingAccount(null)
    setIsCreateModalOpen(true)
  }

  const handleEditAccount = (account: ChartOfAccount) => {
    setFormData({
      name: account.name,
      account_type: account.account_type,
      parent_id: account.parent_id || '',
      is_active: account.is_active,
    })
    setFormErrors({})
    setEditingAccount(account)
    setIsCreateModalOpen(true)
  }

  const renderAccountNode = (node: AccountTreeNode) => {
    const hasChildren = node.children.length > 0
    const isExpanded = expandedNodes.has(node.id)
    const indentLevel = node.level * 24

    return (
      <div key={node.id}>
        <div
          className={cn(
            'flex items-center gap-2 p-3 border-b border-gray-100 hover:bg-gray-50 transition-colors',
            !node.is_active && 'opacity-50'
          )}
          style={{ paddingLeft: `${indentLevel + 12}px` }}
        >
          {hasChildren ? (
            <button
              onClick={() => toggleNodeExpansion(node.id)}
              className="p-1 hover:bg-gray-200 rounded"
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
          ) : (
            <div className="w-6" />
          )}

          <div className="flex items-center gap-2">
            {accountTypeIcons[node.account_type]}
            <span className={cn(
              'font-medium',
              !node.is_active && 'text-gray-500'
            )}>
              {node.name}
            </span>
            {!node.is_active && (
              <EyeOff className="h-4 w-4 text-gray-400" />
            )}
          </div>

          <Badge
            variant="outline"
            className={cn('text-xs capitalize', accountTypeColors[node.account_type])}
          >
            {node.account_type}
          </Badge>

          <div className="ml-auto flex items-center gap-2">
            <span className={cn(
              'font-medium',
              node.balance >= 0 ? 'text-green-600' : 'text-red-600'
            )}>
              {formatAmount(node.balance)}
            </span>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleEditAccount(node)}
                className="h-8 w-8 p-0"
              >
                <Edit className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div>
            {node.children.map(child => renderAccountNode(child))}
          </div>
        )}
      </div>
    )
  }

  const accountTypeTotals = React.useMemo(() => {
    const totals: Record<ChartOfAccount['account_type'], number> = {
      asset: 0,
      liability: 0,
      equity: 0,
      income: 0,
      expense: 0,
    }

    accounts.forEach(account => {
      if (account.is_active) {
        totals[account.account_type] += account.balance
      }
    })

    return totals
  }, [accounts])

  if (error) {
    return (
      <Card className={cn('p-6', className)}>
        <div className="text-center">
          <Building className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Chart of Accounts</h3>
          <p className="text-gray-600">
            Unable to load chart of accounts. Please try again later.
          </p>
        </div>
      </Card>
    )
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Chart of Accounts</h2>
        <Button onClick={handleCreateAccount}>
          <Plus className="h-4 w-4 mr-2" />
          Add Account
        </Button>
      </div>

      {/* Account Type Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {Object.entries(accountTypeTotals).map(([type, total]) => (
          <Card key={type} className="p-4">
            <div className="flex items-center gap-2 mb-2">
              {accountTypeIcons[type as ChartOfAccount['account_type']]}
              <h3 className="font-medium text-gray-700 capitalize">{type}</h3>
            </div>
            <p className={cn(
              'text-lg font-bold',
              total >= 0 ? 'text-green-600' : 'text-red-600'
            )}>
              {formatAmount(total)}
            </p>
          </Card>
        ))}
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search accounts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-64"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={filterAccountType}
              onChange={(e) => setFilterAccountType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">All Types</option>
              <option value="asset">Assets</option>
              <option value="liability">Liabilities</option>
              <option value="equity">Equity</option>
              <option value="income">Income</option>
              <option value="expense">Expenses</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Switch
              checked={showInactiveAccounts}
              onCheckedChange={setShowInactiveAccounts}
            />
            <Label className="text-sm">Show inactive accounts</Label>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              // Expand all nodes
              const allNodeIds = new Set<string>()
              const collectIds = (nodes: AccountTreeNode[]) => {
                nodes.forEach(node => {
                  if (node.children.length > 0) {
                    allNodeIds.add(node.id)
                    collectIds(node.children)
                  }
                })
              }
              collectIds(filteredAccountTree)
              setExpandedNodes(allNodeIds)
            }}
          >
            Expand All
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setExpandedNodes(new Set())}
          >
            Collapse All
          </Button>
        </div>
      </Card>

      {/* Accounts Tree */}
      <Card>
        <div className="border-b border-gray-200 p-4">
          <h3 className="font-semibold text-gray-900">Accounts</h3>
        </div>

        {isLoading ? (
          <div className="p-8 text-center">
            <div className="h-6 w-6 animate-spin rounded-full border-b-2 border-blue-600 mx-auto" />
            <p className="text-gray-600 mt-2">Loading accounts...</p>
          </div>
        ) : filteredAccountTree.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {searchTerm || filterAccountType ? 'No accounts match your filters' : 'No accounts found'}
          </div>
        ) : (
          <ScrollArea className="max-h-96">
            <div>
              {filteredAccountTree.map(node => renderAccountNode(node))}
            </div>
          </ScrollArea>
        )}
      </Card>

      {/* Create/Edit Account Modal */}
      <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingAccount ? 'Edit Account' : 'Create New Account'}
            </DialogTitle>
            <DialogDescription>
              {editingAccount
                ? 'Update the account details below.'
                : 'Add a new account to your chart of accounts.'
              }
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="account-name">Account Name *</Label>
              <Input
                id="account-name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter account name"
                className={formErrors.name ? 'border-red-500' : ''}
              />
              {formErrors.name && (
                <p className="text-sm text-red-600 mt-1">{formErrors.name}</p>
              )}
            </div>

            <div>
              <Label htmlFor="account-type">Account Type *</Label>
              <select
                id="account-type"
                value={formData.account_type}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  account_type: e.target.value as ChartOfAccount['account_type']
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="asset">Asset</option>
                <option value="liability">Liability</option>
                <option value="equity">Equity</option>
                <option value="income">Income</option>
                <option value="expense">Expense</option>
              </select>
            </div>

            <div>
              <Label htmlFor="parent-account">Parent Account (Optional)</Label>
              <select
                id="parent-account"
                value={formData.parent_id}
                onChange={(e) => setFormData(prev => ({ ...prev, parent_id: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="">No Parent (Top Level)</option>
                {accounts
                  .filter(account => account.id !== editingAccount?.id)
                  .map(account => (
                    <option key={account.id} value={account.id}>
                      {account.name} ({account.account_type})
                    </option>
                  ))
                }
              </select>
            </div>

            <div className="flex items-center gap-2">
              <Switch
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_active: checked }))}
              />
              <Label>Active Account</Label>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                // Here you would handle the create/update logic
                // For now, just close the modal
                setIsCreateModalOpen(false)
              }}
            >
              {editingAccount ? 'Update Account' : 'Create Account'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}