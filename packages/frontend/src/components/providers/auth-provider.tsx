'use client'

import React, { createContext, useContext, ComponentType } from 'react'

interface User {
  id: string
  email: string
  firstName?: string
  lastName?: string
  is_superuser?: boolean
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>
  logout: () => Promise<void>
  refreshAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Mock user for local development
const MOCK_USER: User = {
  id: '00000000-0000-0000-0000-000000000001',
  email: 'local@manna.finance',
  firstName: 'Local',
  lastName: 'User',
  is_superuser: true
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Always return a logged-in user for local development
  const user = MOCK_USER
  const isLoading = false
  const isAuthenticated = true

  const refreshAuth = async () => {
    // No-op for local development
  }

  const login = async (email: string, password: string, rememberMe = false) => {
    // No-op for local development - already logged in
  }

  const logout = async () => {
    // No-op for local development - can't log out
    console.log('Logout disabled for local development')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        login,
        logout,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// Higher-order component for protecting routes - DISABLED for local development
export function withAuth<P extends object>(Component: ComponentType<P>) {
  return function ProtectedComponent(props: P) {
    // Always allow access for local development
    return <Component {...props} />
  }
}