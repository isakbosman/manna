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
export function useFinancialSummary(startDate?: Date, endDate?: Date) {
  return useQuery({
    queryKey: ['dashboard', 'summary', startDate?.toISOString(), endDate?.toISOString()],
    queryFn: async (): Promise<FinancialSummary> => {
      const params: any = {}
      if (startDate) params.start_date = startDate.toISOString()
      if (endDate) params.end_date = endDate.toISOString()
      const response = await api.get('/dashboard/summary', params)
      return response.data
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Fetch recent transactions
export function useRecentTransactions(limit: number = 10, startDate?: Date, endDate?: Date) {
  return useQuery({
    queryKey: ['dashboard', 'transactions', limit, startDate?.toISOString(), endDate?.toISOString()],
    queryFn: async (): Promise<Transaction[]> => {
      const params: any = { limit }
      if (startDate) params.start_date = startDate.toISOString()
      if (endDate) params.end_date = endDate.toISOString()
      const response = await api.get('/dashboard/transactions/recent', params)
      return response.data || []
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
  })
}

// Fetch spending by category
export function useSpendingByCategory(startDate?: Date, endDate?: Date) {
  return useQuery({
    queryKey: ['dashboard', 'spending', startDate?.toISOString(), endDate?.toISOString()],
    queryFn: async (): Promise<SpendingCategory[]> => {
      const params: any = {}
      if (startDate) params.start_date = startDate.toISOString()
      if (endDate) params.end_date = endDate.toISOString()
      const response = await api.get('/dashboard/spending/by-category', params)
      return response.data || []
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Fetch transaction trends
export function useTransactionTrends(startDate?: Date, endDate?: Date) {
  return useQuery({
    queryKey: ['dashboard', 'trends', startDate?.toISOString(), endDate?.toISOString()],
    queryFn: async (): Promise<TrendData[]> => {
      const params: any = {}
      if (startDate) params.start_date = startDate.toISOString()
      if (endDate) params.end_date = endDate.toISOString()
      const response = await api.get('/dashboard/trends', params)
      return response.data || []
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Fetch cash flow data
export function useCashFlow(startDate?: Date, endDate?: Date) {
  return useQuery({
    queryKey: ['dashboard', 'cashflow', startDate?.toISOString(), endDate?.toISOString()],
    queryFn: async (): Promise<CashFlowData[]> => {
      const params: any = {}
      if (startDate) params.start_date = startDate.toISOString()
      if (endDate) params.end_date = endDate.toISOString()
      const response = await api.get('/dashboard/cash-flow', params)
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
export function useKPIs(startDate?: Date, endDate?: Date) {
  return useQuery({
    queryKey: ['dashboard', 'kpis', startDate?.toISOString(), endDate?.toISOString()],
    queryFn: async (): Promise<KPIs> => {
      const params: any = {}
      if (startDate) params.start_date = startDate.toISOString()
      if (endDate) params.end_date = endDate.toISOString()
      const response = await api.get('/dashboard/kpis', params)
      return response.data
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
  })
}