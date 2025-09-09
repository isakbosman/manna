'use client'

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react'
import { cn } from '@/lib/utils'

type ToastType = 'success' | 'error' | 'info' | 'warning'

interface Toast {
  id: string
  type: ToastType
  title: string
  description?: string
  duration?: number
}

interface ToastContextType {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2)
    const newToast = { ...toast, id }
    
    setToasts(prev => [...prev, newToast])
    
    // Auto remove after duration (default 5 seconds)
    const duration = toast.duration ?? 5000
    if (duration > 0) {
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id))
      }, duration)
    }
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

function ToastContainer() {
  const { toasts } = useToast()

  if (toasts.length === 0) {
    return null
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  )
}

function ToastItem({ toast }: { toast: Toast }) {
  const { removeToast } = useToast()

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    info: Info,
    warning: AlertCircle
  }

  const colors = {
    success: 'bg-success-50 border-success-200 text-success-800',
    error: 'bg-error-50 border-error-200 text-error-800',
    info: 'bg-primary-50 border-primary-200 text-primary-800',
    warning: 'bg-warning-50 border-warning-200 text-warning-800'
  }

  const iconColors = {
    success: 'text-success-600',
    error: 'text-error-600',
    info: 'text-primary-600',
    warning: 'text-warning-600'
  }

  const Icon = icons[toast.type]

  return (
    <div
      className={cn(
        'relative flex w-full items-start space-x-3 rounded-md border p-4 shadow-lg animate-in slide-in-from-top-2',
        colors[toast.type]
      )}
    >
      <Icon className={cn('h-5 w-5 mt-0.5', iconColors[toast.type])} />
      <div className="flex-1 space-y-1">
        <h4 className="text-sm font-medium">{toast.title}</h4>
        {toast.description && (
          <p className="text-sm opacity-90">{toast.description}</p>
        )}
      </div>
      <button
        onClick={() => removeToast(toast.id)}
        className="absolute top-2 right-2 rounded-md p-1.5 opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

// Convenience hooks
export function useSuccessToast() {
  const { addToast } = useToast()
  return useCallback((title: string, description?: string) => {
    addToast({ type: 'success', title, description })
  }, [addToast])
}

export function useErrorToast() {
  const { addToast } = useToast()
  return useCallback((title: string, description?: string) => {
    addToast({ type: 'error', title, description })
  }, [addToast])
}

export function useInfoToast() {
  const { addToast } = useToast()
  return useCallback((title: string, description?: string) => {
    addToast({ type: 'info', title, description })
  }, [addToast])
}

export function useWarningToast() {
  const { addToast } = useToast()
  return useCallback((title: string, description?: string) => {
    addToast({ type: 'warning', title, description })
  }, [addToast])
}