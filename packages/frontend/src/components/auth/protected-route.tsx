'use client'

import React from 'react'

interface ProtectedRouteProps {
  children: React.ReactNode
  redirectTo?: string
  requiredRole?: string
  fallback?: React.ReactNode
}

/**
 * ProtectedRoute component - DISABLED for local development
 * Always renders children without authentication checks
 */
export function ProtectedRoute({
  children,
  redirectTo = '/auth/login',
  requiredRole,
  fallback
}: ProtectedRouteProps) {
  // Always render children for local development
  return <>{children}</>
}

/**
 * HOC version of ProtectedRoute - DISABLED for local development
 */
export function withProtectedRoute<P extends object>(
  Component: React.ComponentType<P>,
  options: Omit<ProtectedRouteProps, 'children'> = {}
) {
  return function ProtectedComponent(props: P) {
    // Always render component for local development
    return <Component {...props} />
  }
}

/**
 * Hook to check if user has required permissions - DISABLED for local development
 * Always returns true for all permission checks
 */
export function usePermissions() {
  return {
    isAuthenticated: true,
    user: {
      id: '00000000-0000-0000-0000-000000000001',
      email: 'local@manna.finance',
      role: 'admin'
    },
    hasRole: () => true,
    hasAnyRole: () => true,
    isAdmin: true,
    isUser: true
  }
}