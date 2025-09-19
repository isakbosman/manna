import React from 'react'
import { Progress } from '@/components/ui/progress'
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  TrendingUp,
  Clock,
  Database
} from 'lucide-react'

interface BookkeepingHealth {
  status: 'healthy' | 'warning' | 'behind' | 'critical'
  unreconciled_accounts: number
  pending_journal_entries: number
  days_behind_reconciliation: number
  last_reconciliation_date: string | null
  current_period_status: string
  ml_categorization_accuracy: number
  pending_categorizations: number
}

interface HealthIndicatorsProps {
  health: BookkeepingHealth
}

export function HealthIndicators({ health }: HealthIndicatorsProps) {
  const getHealthScore = () => {
    let score = 100

    // Deduct points for various issues
    score -= health.unreconciled_accounts * 5
    score -= health.pending_journal_entries * 2
    score -= health.days_behind_reconciliation * 3
    score -= (100 - health.ml_categorization_accuracy) * 0.5

    return Math.max(0, Math.min(100, score))
  }

  const getIndicatorColor = (value: number, threshold: number) => {
    if (value === 0) return 'text-green-600'
    if (value <= threshold / 2) return 'text-yellow-600'
    if (value <= threshold) return 'text-orange-600'
    return 'text-red-600'
  }

  const healthScore = getHealthScore()

  return (
    <div className="space-y-4">
      {/* Overall Health Score */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Overall Health Score</span>
          <span className="text-sm text-muted-foreground">{healthScore}%</span>
        </div>
        <Progress
          value={healthScore}
          className={healthScore < 50 ? 'bg-red-100' : healthScore < 75 ? 'bg-yellow-100' : 'bg-green-100'}
        />
      </div>

      {/* Individual Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Unreconciled Accounts */}
        <div className="border rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <Database className={`h-4 w-4 ${getIndicatorColor(health.unreconciled_accounts, 5)}`} />
            <span className="text-xs text-muted-foreground">Unreconciled</span>
          </div>
          <div className="text-2xl font-bold">{health.unreconciled_accounts}</div>
          <div className="text-xs text-muted-foreground">accounts</div>
        </div>

        {/* Pending Journal Entries */}
        <div className="border rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <AlertCircle className={`h-4 w-4 ${getIndicatorColor(health.pending_journal_entries, 10)}`} />
            <span className="text-xs text-muted-foreground">Pending</span>
          </div>
          <div className="text-2xl font-bold">{health.pending_journal_entries}</div>
          <div className="text-xs text-muted-foreground">journal entries</div>
        </div>

        {/* Days Behind */}
        <div className="border rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <Clock className={`h-4 w-4 ${getIndicatorColor(health.days_behind_reconciliation, 7)}`} />
            <span className="text-xs text-muted-foreground">Days Behind</span>
          </div>
          <div className="text-2xl font-bold">{health.days_behind_reconciliation}</div>
          <div className="text-xs text-muted-foreground">reconciliation</div>
        </div>

        {/* ML Accuracy */}
        <div className="border rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className={`h-4 w-4 ${health.ml_categorization_accuracy >= 90 ? 'text-green-600' : health.ml_categorization_accuracy >= 75 ? 'text-yellow-600' : 'text-red-600'}`} />
            <span className="text-xs text-muted-foreground">ML Accuracy</span>
          </div>
          <div className="text-2xl font-bold">{health.ml_categorization_accuracy}%</div>
          <div className="text-xs text-muted-foreground">categorization</div>
        </div>
      </div>

      {/* Status Messages */}
      <div className="space-y-2">
        {health.unreconciled_accounts > 0 && (
          <div className="flex items-center gap-2 text-sm">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <span>{health.unreconciled_accounts} accounts need reconciliation</span>
          </div>
        )}
        {health.pending_categorizations > 0 && (
          <div className="flex items-center gap-2 text-sm">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <span>{health.pending_categorizations} transactions pending categorization</span>
          </div>
        )}
        {health.status === 'healthy' && (
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <span>All systems operating normally</span>
          </div>
        )}
      </div>
    </div>
  )
}