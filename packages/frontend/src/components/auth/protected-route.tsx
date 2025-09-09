'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/components/providers/auth-provider'
import { Loading } from '@/components/ui/loading'

interface ProtectedRouteProps {
  children: React.ReactNode
  redirectTo?: string
  requiredRole?: string
  fallback?: React.ReactNode
}

/**
 * ProtectedRoute component that ensures user is authenticated before rendering children
 * @param children - The components to render if user is authenticated
 * @param redirectTo - Where to redirect if not authenticated (default: '/auth/login')
 * @param requiredRole - Optional role requirement
 * @param fallback - Optional custom loading component
 */
export function ProtectedRoute({
  children,
  redirectTo = '/auth/login',
  requiredRole,
  fallback
}: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()

  React.useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(redirectTo)
    }
  }, [isAuthenticated, isLoading, router, redirectTo])

  // Show loading state
  if (isLoading) {
    return fallback || (
      <div className="flex items-center justify-center min-h-screen">
        <Loading size="lg" />
      </div>
    )
  }

  // Not authenticated - don't render children
  if (!isAuthenticated || !user) {
    return null
  }

  // Check role requirement
  if (requiredRole && user.role !== requiredRole) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600">You don't have permission to access this page.</p>
        </div>
      </div>
    )
  }

  // Render protected content
  return <>{children}</>
}

/**
 * HOC version of ProtectedRoute for wrapping page components
 */
export function withProtectedRoute<P extends object>(
  Component: React.ComponentType<P>,
  options: Omit<ProtectedRouteProps, 'children'> = {}
) {
  return function ProtectedComponent(props: P) {
    return (
      <ProtectedRoute {...options}>
        <Component {...props} />
      </ProtectedRoute>
    )
  }
}

/**
 * Hook to check if user has required permissions
 */
export function usePermissions() {
  const { user, isAuthenticated } = useAuth()

  const hasRole = React.useCallback((role: string) => {
    return isAuthenticated && user?.role === role
  }, [isAuthenticated, user])

  const hasAnyRole = React.useCallback((roles: string[]) => {
    return isAuthenticated && user?.role && roles.includes(user.role)
  }, [isAuthenticated, user])

  return {
    isAuthenticated,
    user,
    hasRole,
    hasAnyRole,
    isAdmin: hasRole('admin'),
    isUser: hasRole('user')
  }
}