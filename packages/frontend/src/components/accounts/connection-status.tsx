'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Account } from '../../lib/api/accounts'
import { formatCurrency } from '../../lib/utils'
import { 
  CheckCircle, 
  AlertCircle, 
  RefreshCw, 
  Building2,
  CreditCard,
  Wifi,
  WifiOff
} from 'lucide-react'
import { format } from 'date-fns'

interface ConnectionStatusProps {
  accounts: Account[]
  onSync: () => void
  isSyncing: boolean
}

export function ConnectionStatus({ accounts, onSync, isSyncing }: ConnectionStatusProps) {
  const activeAccounts = accounts.filter(account => account.is_active)
  const inactiveAccounts = accounts.filter(account => !account.is_active)
  
  const institutionIds = [...new Set(
    accounts
      .filter(account => account.institution_id)
      .map(account => account.institution_id!)
  )]
  
  const totalBalance = accounts.reduce((sum, account) => {
    if (account.type === 'credit') {
      return sum - Math.abs(account.balance_current)
    }
    return sum + account.balance_current
  }, 0)

  const lastSyncedDates = accounts
    .filter(account => account.last_synced_at)
    .map(account => new Date(account.last_synced_at!))
    .sort((a, b) => b.getTime() - a.getTime())
  
  const lastSyncedAt = lastSyncedDates.length > 0 ? lastSyncedDates[0] : null

  const getConnectionStatus = () => {
    if (accounts.length === 0) {
      return { status: 'none', message: 'No accounts connected', icon: WifiOff, color: 'text-muted-foreground' }
    }
    
    if (inactiveAccounts.length > 0) {
      return { 
        status: 'partial', 
        message: `${inactiveAccounts.length} account${inactiveAccounts.length > 1 ? 's' : ''} need attention`, 
        icon: AlertCircle, 
        color: 'text-warning-600' 
      }
    }
    
    return { 
      status: 'connected', 
      message: 'All accounts connected', 
      icon: Wifi, 
      color: 'text-success-600' 
    }
  }

  const connectionStatus = getConnectionStatus()
  const StatusIcon = connectionStatus.icon

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Connection Overview</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={onSync}
            disabled={isSyncing || accounts.length === 0}
            className="h-8"
          >
            <RefreshCw className={`h-3 w-3 mr-1.5 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? 'Syncing...' : 'Sync All'}
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Connection Status */}
        <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
          <div className="flex items-center space-x-2">
            <StatusIcon className={`h-4 w-4 ${connectionStatus.color}`} />
            <span className="text-sm font-medium">Connection Status</span>
          </div>
          <span className={`text-sm ${connectionStatus.color}`}>
            {connectionStatus.message}
          </span>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="text-center p-3 bg-primary-50 rounded-lg">
            <div className="flex items-center justify-center mb-1">
              <Building2 className="h-4 w-4 text-primary-600" />
            </div>
            <div className="text-lg font-semibold text-primary-900">{institutionIds.length}</div>
            <div className="text-xs text-primary-600">Institution{institutionIds.length !== 1 ? 's' : ''}</div>
          </div>
          
          <div className="text-center p-3 bg-success-50 rounded-lg">
            <div className="flex items-center justify-center mb-1">
              <CheckCircle className="h-4 w-4 text-success-600" />
            </div>
            <div className="text-lg font-semibold text-success-900">{activeAccounts.length}</div>
            <div className="text-xs text-success-600">Active</div>
          </div>
          
          <div className="text-center p-3 bg-neutral-50 rounded-lg">
            <div className="flex items-center justify-center mb-1">
              <CreditCard className="h-4 w-4 text-neutral-600" />
            </div>
            <div className="text-lg font-semibold text-neutral-900">{accounts.length}</div>
            <div className="text-xs text-neutral-600">Total</div>
          </div>
        </div>

        {/* Balance Summary */}
        {accounts.length > 0 && (
          <div className="p-3 border rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Total Balance</span>
              <span className={`text-lg font-semibold ${
                totalBalance >= 0 ? 'text-success-600' : 'text-error-600'
              }`}>
                {formatCurrency(totalBalance)}
              </span>
            </div>
          </div>
        )}

        {/* Last Sync Info */}
        {lastSyncedAt && (
          <div className="text-xs text-muted-foreground text-center border-t pt-3">
            Last synced: {format(lastSyncedAt, 'MMM dd, yyyy \'at\' h:mm a')}
          </div>
        )}

        {/* Issues Alert */}
        {inactiveAccounts.length > 0 && (
          <div className="p-3 bg-warning-50 border border-warning-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <AlertCircle className="h-4 w-4 text-warning-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-warning-800">
                  Connection Issues Detected
                </p>
                <p className="text-xs text-warning-700 mt-1">
                  {inactiveAccounts.length} account{inactiveAccounts.length > 1 ? 's are' : ' is'} inactive and may need to be reconnected.
                </p>
                <div className="mt-2 text-xs">
                  {inactiveAccounts.slice(0, 3).map(account => (
                    <div key={account.id} className="text-warning-600">
                      • {account.name}
                    </div>
                  ))}
                  {inactiveAccounts.length > 3 && (
                    <div className="text-warning-600">
                      • And {inactiveAccounts.length - 3} more...
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}