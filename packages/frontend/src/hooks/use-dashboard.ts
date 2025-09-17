'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api-client'

export interface FinancialSummary {
  totalAssets: number
  totalLiabilities: number
  netWorth: number
  liquidAssets: number
  monthlyChange: {
    assets: number
    liabilities: number
    netWorth: number
  }
  breakdown: {
    checking: number
    savings: number
    investments: number
    creditCards: number
    loans: number
    other: number
  }
}

export interface Transaction {
  id: string
  date: string
  description: string
  amount: number
  category: string
  account: string
  merchant?: string
  type: 'credit' | 'debit'
}

export interface SpendingCategory {
  name: string
  value: number
  color: string
  percentage: number
}

export interface TrendData {
  date: string
  income: number
  expenses: number
  netFlow: number
}

export interface CashFlowData {
  month: string
  income: number
  expenses: number
  netFlow: number
  runningBalance: number
}

export interface Alert {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  category: string
  priority: string
  created_at: string
  data?: any
  actionable?: boolean
}

export interface KPIs {
  totalBalance: number
  monthlyIncome: number
  monthlyExpenses: number
  savingsRate: number
  accountCount: number
}

// Fetch financial summary
export function useFinancialSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: async (): Promise<FinancialSummary> => {
      const response = await api.get('/dashboard/summary')
      return response.data
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Fetch recent transactions
export function useRecentTransactions(limit: number = 10) {
  return useQuery({
    queryKey: ['dashboard', 'transactions', limit],
    queryFn: async (): Promise<Transaction[]> => {
      const response = await api.get('/dashboard/transactions/recent', { limit })
      return response.data || []
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
  })
}

// Fetch spending by category
export function useSpendingByCategory(days: number = 30) {
  return useQuery({
    queryKey: ['dashboard', 'spending', days],
    queryFn: async (): Promise<SpendingCategory[]> => {
      const response = await api.get('/dashboard/spending/by-category', { days })
      return response.data || []
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Fetch transaction trends
export function useTransactionTrends(days: number = 30) {
  return useQuery({
    queryKey: ['dashboard', 'trends', days],
    queryFn: async (): Promise<TrendData[]> => {
      const response = await api.get('/dashboard/trends', { days })
      return response.data || []
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Fetch cash flow data
export function useCashFlow(months: number = 6) {
  return useQuery({
    queryKey: ['dashboard', 'cashflow', months],
    queryFn: async (): Promise<CashFlowData[]> => {
      const response = await api.get('/dashboard/cash-flow', { months })
      return response.data || []
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Fetch alerts
export function useAlerts() {
  return useQuery({
    queryKey: ['dashboard', 'alerts'],
    queryFn: async (): Promise<Alert[]> => {
      const response = await api.get('/dashboard/alerts')
      return response.data || []
    },
    staleTime: 1000 * 60 * 1, // 1 minute
  })
}

// Fetch KPIs
export function useKPIs() {
  return useQuery({
    queryKey: ['dashboard', 'kpis'],
    queryFn: async (): Promise<KPIs> => {
      const response = await api.get('/dashboard/kpis')
      return response.data
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
  })
}