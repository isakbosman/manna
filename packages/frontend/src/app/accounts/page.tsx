'use client'

import React, { useState, useEffect } from 'react'
import { DashboardLayout } from '../../components/layout/dashboard-layout'
import { TestPlaid } from './test-plaid'
// import { withAuth } from '../../components/providers/auth-provider' // DISABLED for local dev
import { PlaidLink } from '../../components/plaid/plaid-link'
import { ConnectionStatus } from '../../components/accounts/connection-status'
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Loading } from '../../components/ui/loading'
import { accountsApi, Account, Institution } from '../../lib/api/accounts'
import { formatCurrency } from '../../lib/utils'
import { 
  CreditCard, 
  Building2, 
  RefreshCw, 
  Trash2, 
  CheckCircle, 
  AlertCircle,
  Plus,
  RefreshCcw,
  Eye,
  EyeOff
} from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSuccessToast, useErrorToast } from '../../components/ui/toast'

interface AccountCardProps {
  account: Account
  institution?: Institution
  onRemove: (accountId: string) => void
  onSync: (accountId: string) => void
  onFetchHistorical: (accountId: string) => void
  isRemoving: boolean
  isSyncing: boolean
  isFetchingHistorical: boolean
}

function AccountCard({
  account,
  institution,
  onRemove,
  onSync,
  onFetchHistorical,
  isRemoving,
  isSyncing,
  isFetchingHistorical
}: AccountCardProps) {
  const [balanceVisible, setBalanceVisible] = useState(true)
  
  const getAccountTypeDisplay = (type: string, subtype?: string) => {
    if (subtype) {
      return `${type.charAt(0).toUpperCase() + type.slice(1)} - ${subtype}`
    }
    return type.charAt(0).toUpperCase() + type.slice(1)
  }

  const getBalanceColor = (balance: number, type: string) => {
    if (type === 'credit') {
      return balance < 0 ? 'text-success-600' : 'text-error-600'
    }
    return balance >= 0 ? 'text-success-600' : 'text-error-600'
  }

  const lastSynced = account.last_synced_at 
    ? new Date(account.last_synced_at).toLocaleDateString()
    : 'Never'

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            {institution?.logo ? (
              <img 
                src={institution.logo} 
                alt={institution.name}
                className="w-8 h-8 rounded"
              />
            ) : (
              <Building2 className="w-8 h-8 text-muted-foreground" />
            )}
            <div>
              <CardTitle className="text-lg">{account.name}</CardTitle>
              <CardDescription className="text-sm">
                {getAccountTypeDisplay(account.type, account.subtype)} 
                {account.mask && ` •••• ${account.mask}`}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setBalanceVisible(!balanceVisible)}
              title="Toggle balance visibility"
            >
              {balanceVisible ? (
                <Eye className="w-4 h-4" />
              ) : (
                <EyeOff className="w-4 h-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onSync(account.id)}
              disabled={isSyncing}
              title="Sync recent transactions"
            >
              {isSyncing ? (
                <Loading size="sm" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onFetchHistorical(account.id)}
              disabled={isFetchingHistorical}
              title="Fetch all historical transactions"
            >
              {isFetchingHistorical ? (
                <Loading size="sm" />
              ) : (
                <RefreshCcw className="w-4 h-4 text-primary-600" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRemove(account.id)}
              disabled={isRemoving}
              title="Remove account"
            >
              {isRemoving ? (
                <Loading size="sm" />
              ) : (
                <Trash2 className="w-4 h-4 text-error-600" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Current Balance</span>
            <span className={`font-semibold ${getBalanceColor(account.balance_current, account.type)}`}>
              {balanceVisible ? formatCurrency(account.balance_current) : '••••••'}
            </span>
          </div>
          
          {account.balance_available !== undefined && account.balance_available !== account.balance_current && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Available Balance</span>
              <span className="font-semibold">
                {balanceVisible ? formatCurrency(account.balance_available) : '••••••'}
              </span>
            </div>
          )}
          
          {account.balance_limit && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Credit Limit</span>
              <span className="font-semibold">
                {balanceVisible ? formatCurrency(account.balance_limit) : '••••••'}
              </span>
            </div>
          )}
          
          <div className="pt-2 border-t">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <div className="flex items-center space-x-1">
                {account.is_active ? (
                  <>
                    <CheckCircle className="w-3 h-3 text-success-600" />
                    <span>Active</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-3 h-3 text-error-600" />
                    <span>Inactive</span>
                  </>
                )}
              </div>
              <span>Last synced: {lastSynced}</span>
            </div>
            
            {institution && (
              <div className="mt-2 text-xs text-muted-foreground">
                Institution: {institution.name}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function AccountsPage() {
  const [showAddAccount, setShowAddAccount] = useState(false)
  const [syncingAccounts, setSyncingAccounts] = useState<Set<string>>(new Set())
  const [fetchingHistoricalAccounts, setFetchingHistoricalAccounts] = useState<Set<string>>(new Set())
  const [removingAccounts, setRemovingAccounts] = useState<Set<string>>(new Set())
  const queryClient = useQueryClient()

  // Fetch accounts
  const {
    data: accounts = [],
    isLoading: accountsLoading,
    error: accountsError,
    refetch: refetchAccounts
  } = useQuery({
    queryKey: ['accounts'],
    queryFn: accountsApi.getAccounts
  })

  // Fetch institutions for connected accounts
  const institutionIds = [...new Set(
    accounts
      .filter(account => account.institution_id)
      .map(account => account.institution_id!)
  )]

  const {
    data: institutions = [],
    isLoading: institutionsLoading
  } = useQuery({
    queryKey: ['institutions', institutionIds],
    queryFn: async () => {
      const results = await Promise.allSettled(
        institutionIds.map(id => accountsApi.getInstitution(id))
      )
      return results
        .filter((result): result is PromiseFulfilledResult<Institution> => 
          result.status === 'fulfilled'
        )
        .map(result => result.value)
    },
    enabled: institutionIds.length > 0
  })

  // Sync transactions mutation
  const syncMutation = useMutation({
    mutationFn: accountsApi.syncTransactions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    }
  })

  // Fetch historical transactions mutation
  const fetchHistoricalMutation = useMutation({
    mutationFn: accountsApi.fetchHistoricalTransactions,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
    }
  })

  // Remove account mutation
  const removeMutation = useMutation({
    mutationFn: accountsApi.deleteAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
    }
  })

  const successToast = useSuccessToast()
  const errorToast = useErrorToast()

  const handlePlaidSuccess = (newAccounts: Account[], institutionName: string) => {
    setShowAddAccount(false)
    queryClient.invalidateQueries({ queryKey: ['accounts'] })
    queryClient.invalidateQueries({ queryKey: ['institutions'] })
    successToast(
      'Accounts Connected Successfully!',
      `Successfully connected ${newAccounts.length} accounts from ${institutionName}`
    )
  }

  const handlePlaidError = (error: string) => {
    console.error('Plaid connection error:', error)
    errorToast('Connection Failed', error)
  }

  const handleSyncAccount = async (accountId: string) => {
    setSyncingAccounts(prev => new Set(prev).add(accountId))
    
    try {
      await syncMutation.mutateAsync([accountId])
      successToast('Account Synced', 'Account balance and transactions updated successfully')
    } catch (error: any) {
      console.error('Sync error:', error)
      errorToast('Sync Failed', error.message || 'Failed to sync account')
    } finally {
      setSyncingAccounts(prev => {
        const next = new Set(prev)
        next.delete(accountId)
        return next
      })
    }
  }

  const handleRemoveAccount = async (accountId: string) => {
    if (!confirm('Are you sure you want to remove this account? This action cannot be undone.')) {
      return
    }

    setRemovingAccounts(prev => new Set(prev).add(accountId))
    
    try {
      await removeMutation.mutateAsync(accountId)
      successToast('Account Removed', 'Account has been successfully disconnected')
    } catch (error: any) {
      console.error('Remove error:', error)
      errorToast('Remove Failed', error.message || 'Failed to remove account')
    } finally {
      setRemovingAccounts(prev => {
        const next = new Set(prev)
        next.delete(accountId)
        return next
      })
    }
  }

  const handleFetchHistorical = async (accountId: string) => {
    setFetchingHistoricalAccounts(prev => new Set(prev).add(accountId))

    try {
      const result = await fetchHistoricalMutation.mutateAsync([accountId])
      successToast(
        'Historical Transactions Fetched',
        `Fetched ${result.total_fetched} transactions (${result.new_transactions} new) for ${result.date_range}`
      )
    } catch (error: any) {
      console.error('Fetch historical error:', error)
      errorToast('Fetch Failed', error.message || 'Failed to fetch historical transactions')
    } finally {
      setFetchingHistoricalAccounts(prev => {
        const next = new Set(prev)
        next.delete(accountId)
        return next
      })
    }
  }

  const handleSyncAllAccounts = async () => {
    try {
      const result = await syncMutation.mutateAsync(undefined)
      successToast(
        'All Accounts Synced',
        `Updated ${result.synced_count} accounts with ${result.new_transactions} new transactions`
      )
    } catch (error: any) {
      console.error('Sync all error:', error)
      errorToast('Sync Failed', error.message || 'Failed to sync accounts')
    }
  }

  const handleFetchAllHistorical = async () => {
    try {
      const result = await fetchHistoricalMutation.mutateAsync(undefined)
      successToast(
        'Historical Transactions Fetched',
        `Fetched ${result.total_fetched} transactions (${result.new_transactions} new) for ${result.date_range}`
      )
    } catch (error: any) {
      console.error('Fetch all historical error:', error)
      errorToast('Fetch Historical Failed', error.message || 'Failed to fetch historical transactions')
    }
  }

  const institutionMap = new Map(
    institutions.map(inst => [inst.institution_id, inst])
  )

  const totalBalance = accounts.reduce((sum, account) => {
    if (account.type === 'credit') {
      return sum - Math.abs(account.balance_current) // Credit balances are negative
    }
    return sum + account.balance_current
  }, 0)

  const activeAccounts = accounts.filter(account => account.is_active)

  return (
    <DashboardLayout
      title="Accounts"
      description="Manage your connected bank accounts and financial institutions"
    >
      <TestPlaid />
      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Balance</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalBalance)}</div>
            <p className="text-xs text-muted-foreground">Across all accounts</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Connected Accounts</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{accounts.length}</div>
            <p className="text-xs text-muted-foreground">
              {activeAccounts.length} active
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Institutions</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{institutionIds.length}</div>
            <p className="text-xs text-muted-foreground">Connected banks</p>
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 mb-6">
        <Button
          onClick={() => setShowAddAccount(true)}
          disabled={showAddAccount}
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Account
        </Button>

        <Button
          variant="outline"
          onClick={handleFetchAllHistorical}
          disabled={fetchHistoricalMutation.isPending}
        >
          {fetchHistoricalMutation.isPending ? (
            <>
              <Loading size="sm" className="mr-2" />
              Fetching Historical...
            </>
          ) : (
            <>
              <RefreshCcw className="w-4 h-4 mr-2" />
              Fetch All Historical
            </>
          )}
        </Button>

        <Button
          variant="outline" 
          onClick={handleSyncAllAccounts}
          disabled={syncMutation.isPending}
        >
          {syncMutation.isPending ? (
            <Loading size="sm" className="mr-2" />
          ) : (
            <RefreshCcw className="w-4 h-4 mr-2" />
          )}
          Sync All
        </Button>
        
        <Button 
          variant="outline" 
          onClick={() => refetchAccounts()}
          disabled={accountsLoading}
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Connection Status */}
      <div className="mb-6">
        <ConnectionStatus
          accounts={accounts}
          onSync={handleSyncAllAccounts}
          isSyncing={syncMutation.isPending}
        />
      </div>

      {/* Add Account Section */}
      {showAddAccount && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Connect Bank Account</CardTitle>
            <CardDescription>
              Use Plaid to securely connect your bank account and automatically import transactions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 items-center">
              <div className="flex-1">
                <PlaidLink
                  onSuccess={handlePlaidSuccess}
                  onError={handlePlaidError}
                />
              </div>
              <Button
                variant="ghost"
                onClick={() => setShowAddAccount(false)}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Accounts List */}
      {accountsLoading && (
        <div className="flex items-center justify-center py-8">
          <Loading size="lg" />
          <span className="ml-2">Loading accounts...</span>
        </div>
      )}

      {accountsError && (
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-error-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Error Loading Accounts</h3>
              <p className="text-muted-foreground mb-4">
                {accountsError.message || 'Failed to load accounts'}
              </p>
              <Button onClick={() => refetchAccounts()}>
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!accountsLoading && !accountsError && accounts.length === 0 && (
        <Card>
          <CardContent className="flex items-center justify-center py-8">
            <div className="text-center">
              <CreditCard className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Accounts Connected</h3>
              <p className="text-muted-foreground mb-4">
                Connect your first bank account to get started with financial tracking
              </p>
              <Button onClick={() => setShowAddAccount(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Account
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!accountsLoading && accounts.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map(account => (
            <AccountCard
              key={account.id}
              account={account}
              institution={institutionMap.get(account.institution_id || '')}
              onRemove={handleRemoveAccount}
              onSync={handleSyncAccount}
              onFetchHistorical={handleFetchHistorical}
              isRemoving={removingAccounts.has(account.id)}
              isSyncing={syncingAccounts.has(account.id)}
              isFetchingHistorical={fetchingHistoricalAccounts.has(account.id)}
            />
          ))}
        </div>
      )}
    </DashboardLayout>
  )
}

// Export protected version
// Export unprotected version for local development
export default AccountsPage