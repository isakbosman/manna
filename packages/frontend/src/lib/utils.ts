import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Utility function to merge Tailwind classes with clsx
 * This prevents conflicts and duplicates while allowing conditional classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format currency values for display
 */
export function formatCurrency(
  value: number,
  currency: string = 'USD',
  locale: string = 'en-US'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

/**
 * Format percentage values for display
 */
export function formatPercentage(
  value: number,
  decimals: number = 2
): string {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value / 100)
}

/**
 * Format numbers with thousand separators
 */
export function formatNumber(
  value: number,
  decimals: number = 0
): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

/**
 * Debounce function to limit the frequency of function calls
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

/**
 * Throttle function to limit the frequency of function calls
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * Convert a string to title case
 */
export function toTitleCase(str: string): string {
  return str.replace(
    /\w\S*/g,
    (txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
  )
}

/**
 * Generate a random ID
 */
export function generateId(): string {
  return Math.random().toString(36).substr(2, 9)
}

/**
 * Check if a value is empty (null, undefined, empty string, empty array, empty object)
 */
export function isEmpty(value: any): boolean {
  if (value == null) return true
  if (typeof value === 'string') return value.trim().length === 0
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'object') return Object.keys(value).length === 0
  return false
}

/**
 * Safely parse JSON with fallback
 */
export function safeJsonParse<T>(str: string, fallback: T): T {
  try {
    return JSON.parse(str)
  } catch {
    return fallback
  }
}

/**
 * Get the initials from a full name
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

/**
 * Calculate the difference between two dates in days
 */
export function daysBetween(date1: Date, date2: Date): number {
  const oneDay = 24 * 60 * 60 * 1000
  return Math.round(Math.abs((date1.getTime() - date2.getTime()) / oneDay))
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

/**
 * Deep clone an object
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}

/**
 * Check if an object has a specific property
 */
export function hasProperty<T extends object>(
  obj: T,
  prop: string
): prop is keyof T {
  return Object.prototype.hasOwnProperty.call(obj, prop)
}

/**
 * Format file size in human-readable format
 */
export function formatFileSize(bytes: number): string {
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  if (bytes === 0) return '0 Bytes'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * Calculate financial metrics
 */
export function calculateSavingsRate(income: number, expenses: number): number {
  if (income <= 0) return 0
  return ((income - Math.abs(expenses)) / income) * 100
}

export function calculateRunRate(monthlyExpenses: number, currentBalance: number): number {
  if (monthlyExpenses <= 0) return Infinity
  return currentBalance / monthlyExpenses
}

export function calculateDebtToIncomeRatio(monthlyDebtPayments: number, monthlyIncome: number): number {
  if (monthlyIncome <= 0) return 0
  return (monthlyDebtPayments / monthlyIncome) * 100
}

export function calculateCreditUtilization(currentBalance: number, creditLimit: number): number {
  if (creditLimit <= 0) return 0
  return (Math.abs(currentBalance) / creditLimit) * 100
}

export function calculateNetWorth(assets: number, liabilities: number): number {
  return assets - Math.abs(liabilities)
}

/**
 * Generate financial health score (0-100)
 */
export function calculateFinancialHealthScore(metrics: {
  savingsRate: number
  debtToIncomeRatio: number
  creditUtilization: number
  emergencyFundMonths: number
}): number {
  let score = 100
  
  // Savings rate (30% of score)
  if (metrics.savingsRate < 10) score -= 30
  else if (metrics.savingsRate < 20) score -= 15
  
  // Debt-to-income ratio (25% of score)
  if (metrics.debtToIncomeRatio > 36) score -= 25
  else if (metrics.debtToIncomeRatio > 28) score -= 15
  else if (metrics.debtToIncomeRatio > 20) score -= 8
  
  // Credit utilization (25% of score)
  if (metrics.creditUtilization > 30) score -= 25
  else if (metrics.creditUtilization > 10) score -= 10
  
  // Emergency fund (20% of score)
  if (metrics.emergencyFundMonths < 3) score -= 20
  else if (metrics.emergencyFundMonths < 6) score -= 10
  
  return Math.max(0, Math.min(100, score))
}

/**
 * Format large numbers with K, M, B suffixes
 */
export function formatCompactNumber(value: number, decimals: number = 1): string {
  const suffixes = ['', 'K', 'M', 'B', 'T']
  const tier = Math.log10(Math.abs(value)) / 3 | 0
  
  if (tier === 0) return value.toString()
  
  const suffix = suffixes[tier]
  const scale = Math.pow(10, tier * 3)
  const scaled = value / scale
  
  return scaled.toFixed(decimals) + suffix
}

/**
 * Calculate percentage change between two values
 */
export function calculatePercentageChange(currentValue: number, previousValue: number): number {
  if (previousValue === 0) return currentValue > 0 ? 100 : 0
  return ((currentValue - previousValue) / Math.abs(previousValue)) * 100
}