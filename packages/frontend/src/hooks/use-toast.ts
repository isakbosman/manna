// Simple toast hook - in a real app you'd use a toast library like sonner or react-hot-toast
import { useCallback } from 'react'

export interface Toast {
  title: string
  description?: string
  variant?: 'default' | 'destructive' | 'success'
  duration?: number
}

// Simple toast implementation - replace with a proper toast library
export function toast({ title, description, variant = 'default', duration = 3000 }: Toast) {
  // Create a simple toast element
  const toastElement = document.createElement('div')
  toastElement.className = `fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg max-w-sm ${
    variant === 'destructive'
      ? 'bg-error-600 text-white'
      : variant === 'success'
        ? 'bg-success-600 text-white'
        : 'bg-white border text-gray-900'
  }`

  toastElement.innerHTML = `
    <div class="flex items-start space-x-2">
      <div class="flex-1">
        <div class="font-medium">${title}</div>
        ${description ? `<div class="text-sm mt-1 opacity-90">${description}</div>` : ''}
      </div>
      <button class="text-current opacity-70 hover:opacity-100 ml-2" onclick="this.parentElement.parentElement.remove()">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
        </svg>
      </button>
    </div>
  `

  document.body.appendChild(toastElement)

  // Auto-remove after duration
  setTimeout(() => {
    if (toastElement.parentNode) {
      toastElement.remove()
    }
  }, duration)
}

// Hook version for convenience
export function useToast() {
  return useCallback(toast, [])
}

// Default export for module compatibility
export default { toast, useToast }