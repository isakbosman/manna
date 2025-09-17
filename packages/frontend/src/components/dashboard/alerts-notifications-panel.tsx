'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { formatCurrency } from '../../lib/utils'
import { 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  CheckCircle, 
  TrendingDown,
  CreditCard,
  DollarSign,
  Calendar,
  X,
  Bell
} from 'lucide-react'
import { format } from 'date-fns'

export interface Alert {
  id: string
  type: 'warning' | 'error' | 'info' | 'success'
  title: string
  message: string
  category: 'account' | 'transaction' | 'budget' | 'payment' | 'security' | 'system'
  priority: 'low' | 'medium' | 'high' | 'critical'
  created_at: string
  data?: {
    amount?: number
    account_name?: string
    due_date?: string
    utilization?: number
    [key: string]: any
  }
  actionable?: boolean
  action_url?: string
  dismissed?: boolean
}

interface AlertsNotificationsPanelProps {
  alerts: Alert[]
  isLoading?: boolean
  className?: string
  maxItems?: number
  showDismissed?: boolean
  onAlertClick?: (alert: Alert) => void
  onDismissAlert?: (alertId: string) => void
  onViewAll?: () => void
}

const getAlertIcon = (type: string) => {
  const iconMap: Record<string, React.ElementType> = {
    warning: AlertTriangle,
    error: AlertCircle,
    info: Info,
    success: CheckCircle,
  }
  return iconMap[type] || Info
}

const getAlertColor = (type: string, priority: string) => {
  const colors = {
    error: {
      critical: 'border-error-500 bg-error-50 text-error-800',
      high: 'border-error-400 bg-error-50 text-error-700',
      medium: 'border-error-300 bg-error-25 text-error-600',
      low: 'border-error-200 bg-error-25 text-error-600'
    },
    warning: {
      critical: 'border-warning-500 bg-warning-50 text-warning-800',
      high: 'border-warning-400 bg-warning-50 text-warning-700',
      medium: 'border-warning-300 bg-warning-25 text-warning-600',
      low: 'border-warning-200 bg-warning-25 text-warning-600'
    },
    info: {
      critical: 'border-info-500 bg-info-50 text-info-800',
      high: 'border-info-400 bg-info-50 text-info-700',
      medium: 'border-info-300 bg-info-25 text-info-600',
      low: 'border-info-200 bg-info-25 text-info-600'
    },
    success: {
      critical: 'border-success-500 bg-success-50 text-success-800',
      high: 'border-success-400 bg-success-50 text-success-700',
      medium: 'border-success-300 bg-success-25 text-success-600',
      low: 'border-success-200 bg-success-25 text-success-600'
    }
  }
  
  return colors[type as keyof typeof colors]?.[priority as keyof typeof colors['error']] || 
         'border-neutral-200 bg-neutral-50 text-neutral-600'
}

const getCategoryIcon = (category: string) => {
  const categoryMap: Record<string, React.ElementType> = {
    account: CreditCard,
    transaction: DollarSign,
    budget: TrendingDown,
    payment: Calendar,
    security: AlertTriangle,
    system: Info,
  }
  return categoryMap[category] || Info
}

const formatAlertData = (alert: Alert) => {
  if (!alert.data) return null

  const parts = []
  
  if (alert.data.amount) {
    parts.push(`Amount: ${formatCurrency(alert.data.amount)}`)
  }
  
  if (alert.data.account_name) {
    parts.push(`Account: ${alert.data.account_name}`)
  }
  
  if (alert.data.due_date) {
    parts.push(`Due: ${format(new Date(alert.data.due_date), 'MMM dd, yyyy')}`)
  }
  
  if (alert.data.utilization) {
    parts.push(`Utilization: ${(alert.data.utilization * 100).toFixed(1)}%`)
  }

  return parts.join(' • ')
}

const LoadingSkeleton = ({ count = 3 }: { count?: number }) => (
  <div className="space-y-3">
    {[...Array(count)].map((_, i) => (
      <div key={i} className="animate-pulse border rounded-lg p-3">
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 bg-neutral-200 rounded-full"></div>
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-neutral-200 rounded w-3/4"></div>
            <div className="h-3 bg-neutral-200 rounded w-1/2"></div>
            <div className="h-3 bg-neutral-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>
    ))}
  </div>
)

export function AlertsNotificationsPanel({
  alerts,
  isLoading = false,
  className = '',
  maxItems = 5,
  showDismissed = false,
  onAlertClick,
  onDismissAlert,
  onViewAll
}: AlertsNotificationsPanelProps) {
  const filteredAlerts = alerts
    .filter(alert => showDismissed || !alert.dismissed)
    .sort((a, b) => {
      // Sort by priority first, then by date
      const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
      const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority]
      if (priorityDiff !== 0) return priorityDiff
      
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
    .slice(0, maxItems)

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Bell className="h-5 w-5 mr-2" />
            Alerts & Notifications
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton count={maxItems} />
        </CardContent>
      </Card>
    )
  }

  if (filteredAlerts.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Bell className="h-5 w-5 mr-2" />
            Alerts & Notifications
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6">
            <CheckCircle className="h-12 w-12 text-success-300 mx-auto mb-3" />
            <p className="text-neutral-600 mb-2">All caught up!</p>
            <p className="text-sm text-neutral-500">
              No new alerts or notifications
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const criticalCount = alerts.filter(a => a.priority === 'critical' && !a.dismissed).length
  const highCount = alerts.filter(a => a.priority === 'high' && !a.dismissed).length

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center">
            <Bell className="h-5 w-5 mr-2" />
            Alerts & Notifications
            {(criticalCount > 0 || highCount > 0) && (
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-error-100 text-error-800">
                {criticalCount + highCount} urgent
              </span>
            )}
          </CardTitle>
          {onViewAll && alerts.length > maxItems && (
            <button
              onClick={onViewAll}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              View all
            </button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {filteredAlerts.map((alert) => {
            const AlertIcon = getAlertIcon(alert.type)
            const CategoryIcon = getCategoryIcon(alert.category)
            const alertColorClass = getAlertColor(alert.type, alert.priority)
            
            return (
              <div
                key={alert.id}
                className={`border-l-4 rounded-lg p-3 transition-all ${alertColorClass} ${
                  onAlertClick ? 'hover:shadow-sm cursor-pointer' : ''
                }`}
                onClick={() => onAlertClick?.(alert)}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      alert.type === 'error' ? 'bg-error-100' :
                      alert.type === 'warning' ? 'bg-warning-100' :
                      alert.type === 'info' ? 'bg-info-100' :
                      'bg-success-100'
                    }`}>
                      <AlertIcon className="h-4 w-4" />
                    </div>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h4 className="text-sm font-semibold">
                            {alert.title}
                          </h4>
                          <CategoryIcon className="h-3 w-3 opacity-60" />
                          <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium ${
                            alert.priority === 'critical' ? 'bg-error-100 text-error-700' :
                            alert.priority === 'high' ? 'bg-warning-100 text-warning-700' :
                            alert.priority === 'medium' ? 'bg-info-100 text-info-700' :
                            'bg-neutral-100 text-neutral-600'
                          }`}>
                            {alert.priority}
                          </span>
                        </div>
                        
                        <p className="text-sm opacity-90 mb-2">
                          {alert.message}
                        </p>
                        
                        {formatAlertData(alert) && (
                          <p className="text-xs opacity-75 mb-2">
                            {formatAlertData(alert)}
                          </p>
                        )}
                        
                        <div className="flex items-center justify-between">
                          <span className="text-xs opacity-60">
                            {format(new Date(alert.created_at), 'MMM dd, h:mm a')}
                          </span>
                          
                          <div className="flex items-center space-x-2">
                            {alert.actionable && alert.action_url && (
                              <button className="text-xs font-medium hover:underline">
                                Take Action
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {onDismissAlert && !alert.dismissed && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onDismissAlert(alert.id)
                          }}
                          className="ml-2 p-1 hover:bg-black/10 rounded transition-colors"
                          title="Dismiss alert"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Summary Footer */}
        {alerts.length > 0 && (
          <div className="mt-4 pt-3 border-t text-xs text-neutral-500">
            <div className="flex justify-between items-center">
              <span>
                Showing {filteredAlerts.length} of {alerts.filter(a => !a.dismissed).length} active alerts
              </span>
              <div className="flex space-x-3">
                {criticalCount > 0 && (
                  <span className="text-error-600">
                    {criticalCount} critical
                  </span>
                )}
                {highCount > 0 && (
                  <span className="text-warning-600">
                    {highCount} high priority
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}